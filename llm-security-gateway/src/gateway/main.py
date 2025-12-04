"""
LLM Security Gateway - Main FastAPI application.

Enterprise security gateway enforcing DLP, PII redaction, RBAC, and rate limiting.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..dlp.engine import DLPEngine
from ..rbac.policy_engine import PolicyEngine
from ..routing.model_router import ModelRouter
from ..utils.rate_limiter import RateLimiter
from ..utils.audit_logger import AuditLogger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Global instances
dlp_engine: DLPEngine
policy_engine: PolicyEngine
model_router: ModelRouter
rate_limiter: RateLimiter
audit_logger: AuditLogger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global dlp_engine, policy_engine, model_router, rate_limiter, audit_logger

    logger.info("Initializing LLM Security Gateway...")

    # Initialize components
    dlp_engine = DLPEngine()
    policy_engine = PolicyEngine()
    model_router = ModelRouter()
    rate_limiter = RateLimiter()
    audit_logger = AuditLogger()

    logger.info("Gateway initialized successfully")

    yield

    # Cleanup
    logger.info("Shutting down gateway...")
    await rate_limiter.close()
    await audit_logger.close()


# Create FastAPI app
app = FastAPI(
    title="LLM Security Gateway",
    description="Enterprise security gateway for AI/LLM applications",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class ChatMessage(BaseModel):
    """Chat message"""
    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Chat completion request"""
    model: str = Field(..., description="Model name (claude-3-sonnet, gpt-4, etc.)")
    messages: list[ChatMessage]
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=1000, gt=0, le=4000)
    user_id: str = Field(default="anonymous")


class ChatResponse(BaseModel):
    """Chat completion response"""
    model: str
    response: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    components: Dict[str, str]


# Dependency: Get current user from JWT
async def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Extract and validate user from JWT token.

    TODO: Implement full JWT validation
    """
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    # token = auth_header.replace("Bearer ", "")
    # TODO: Validate JWT and extract user info

    # Temporary: Return mock user
    return {
        "user_id": "user_123",
        "role": "user",
        "tier": "premium",
        "tenant": "acme_corp",
    }


# Routes
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        components={
            "dlp": "operational",
            "rbac": "operational",
            "rate_limiter": "operational",
            "router": "operational",
        },
    )


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_completion(
    request: ChatRequest,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Process chat completion request with security checks.

    Security Pipeline:
    1. Rate limiting
    2. RBAC authorization
    3. DLP & PII detection/redaction (request)
    4. Model routing
    5. DLP & PII detection/redaction (response)
    6. Audit logging
    """
    request_id = f"req_{user['user_id']}_{hash(str(request))}"

    try:
        # Step 1: Rate Limiting
        logger.info(f"[{request_id}] Checking rate limits for user {user['user_id']}")
        is_allowed, limit_info = await rate_limiter.check_limit(
            user_id=user["user_id"],
            tenant=user["tenant"],
        )

        if not is_allowed:
            logger.warning(f"[{request_id}] Rate limit exceeded for user {user['user_id']}")
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Try again in {limit_info['retry_after']}s",
            )

        # Step 2: RBAC Authorization
        logger.info(f"[{request_id}] Checking authorization")
        is_authorized = await policy_engine.evaluate(
            user=user,
            action="chat",
            resource={"model": request.model},
        )

        if not is_authorized:
            logger.warning(f"[{request_id}] Authorization denied for model {request.model}")
            raise HTTPException(
                status_code=403,
                detail=f"Access denied to model: {request.model}",
            )

        # Step 3: DLP & PII Detection (Request)
        logger.info(f"[{request_id}] Scanning request for sensitive data")
        request_content = " ".join([msg.content for msg in request.messages])

        dlp_result = await dlp_engine.scan(
            text=request_content,
            mode="redact",  # block, redact, alert
        )

        if dlp_result.blocked:
            logger.error(f"[{request_id}] Request blocked by DLP: {dlp_result.violations}")
            raise HTTPException(
                status_code=400,
                detail=f"Request contains sensitive data: {dlp_result.violations}",
            )

        # Redact PII from request if found
        if dlp_result.pii_detected:
            logger.warning(f"[{request_id}] PII detected in request: {dlp_result.pii_entities}")
            request_content = dlp_result.redacted_text

        # Step 4: Model Routing
        logger.info(f"[{request_id}] Routing to model {request.model}")
        model_response = await model_router.route(
            model=request.model,
            messages=[{"role": msg.role, "content": msg.content} for msg in request.messages],
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        # Step 5: DLP & PII Detection (Response)
        logger.info(f"[{request_id}] Scanning response for sensitive data")
        response_dlp = await dlp_engine.scan(
            text=model_response.content,
            mode="redact",
        )

        final_response = response_dlp.redacted_text if response_dlp.pii_detected else model_response.content

        # Step 6: Audit Logging
        await audit_logger.log(
            request_id=request_id,
            user_id=user["user_id"],
            tenant=user["tenant"],
            model=request.model,
            tokens_used=model_response.tokens_used,
            cost=model_response.cost,
            pii_detected=dlp_result.pii_detected or response_dlp.pii_detected,
            pii_entities=list(set(dlp_result.pii_entities + response_dlp.pii_entities)),
        )

        return ChatResponse(
            model=request.model,
            response=final_response,
            metadata={
                "tokens_used": model_response.tokens_used,
                "cost": model_response.cost,
                "pii_detected": dlp_result.pii_detected or response_dlp.pii_detected,
                "pii_entities": list(set(dlp_result.pii_entities + response_dlp.pii_entities)),
                "latency_ms": model_response.latency_ms,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Error processing request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
        },
    )


def main():
    """Run FastAPI server"""
    import uvicorn

    logger.info("Starting LLM Security Gateway...")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info",
    )


if __name__ == "__main__":
    main()
