"""
FastAPI Application - Natural Language Automation Hub.

Main API server providing:
- Chat endpoints (REST and WebSocket)
- Voice input processing
- Health checks
- Tool registry introspection
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, UTC
from typing import List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from ..config.settings import settings
from ..models.schemas import (
    ChatRequest,
    ChatResponse,
    HealthCheck,
    ProjectHealth,
    ToolDefinition,
    VoiceRequest,
    VoiceTranscription,
    Conversation,
    ChatMessage,
    WSMessage,
)
from ..agent.graph import agent_executor
from ..tools.registry import tool_registry

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Track start time for uptime
START_TIME = datetime.now(UTC)


# ============================================================================
# Lifespan Management
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Initialize LangSmith tracing
    if settings.LANGCHAIN_TRACING_V2 and settings.LANGCHAIN_API_KEY:
        import os
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGCHAIN_ENDPOINT
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
        logger.info("LangSmith tracing enabled")

    yield

    # Cleanup
    await tool_registry.close()
    logger.info("Application shutdown complete")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title=settings.APP_NAME,
    description="Natural Language Automation Hub - Unified control plane for AI-augmented DevOps",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Health & Status Endpoints
# ============================================================================

@app.get("/health", response_model=HealthCheck, tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns status of the application and connected projects.
    """
    uptime = int((datetime.now(UTC) - START_TIME).total_seconds())

    # Check project connectivity
    projects = []
    for project_num, project_name, url in [
        (1, "MCP AWS Server", settings.MCP_AWS_SERVER_URL),
        (2, "LLM Security Gateway", settings.LLM_GATEWAY_URL),
        (3, "K8s AgentOps Platform", settings.K8S_AGENTOPS_URL),
        (4, "Enterprise CI/CD Framework", settings.CICD_API_URL),
        (5, "Centralized Logging", settings.OPENSEARCH_URL),
        (6, "Observability Fabric", settings.PROMETHEUS_URL),
    ]:
        try:
            # Quick connectivity check
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{url}/health")
                status = "healthy" if response.status_code == 200 else "degraded"
                latency = int(response.elapsed.total_seconds() * 1000)
        except Exception as e:
            status = "unhealthy"
            latency = None
            logger.warning(f"Project {project_num} ({project_name}) unhealthy: {e}")

        projects.append(ProjectHealth(
            project=project_num,
            name=project_name,
            status=status,
            latency_ms=latency,
        ))

    # Overall status
    unhealthy_count = sum(1 for p in projects if p.status == "unhealthy")
    if unhealthy_count == 0:
        overall_status = "healthy"
    elif unhealthy_count < len(projects):
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    return HealthCheck(
        status=overall_status,
        version=settings.APP_VERSION,
        uptime_seconds=uptime,
        projects=projects,
        dependencies={
            "langsmith": bool(settings.LANGCHAIN_API_KEY),
            "voice": settings.ENABLE_VOICE,
        },
    )


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with basic info"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }


# ============================================================================
# Chat Endpoints
# ============================================================================

@app.post("/api/v1/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Process a natural language chat message.

    The agent will:
    1. Parse the user's intent
    2. Select and execute appropriate tools
    3. Return a formatted response

    Example:
    ```json
    {
        "message": "Show me all running EC2 instances",
        "user_id": "user-001",
        "conversation_id": "conv-123"
    }
    ```
    """
    logger.info(f"Chat request from user={request.user_id}: {request.message[:50]}...")

    # Generate conversation ID if not provided
    conversation_id = request.conversation_id or str(uuid4())

    try:
        # Execute agent
        result = await agent_executor.run(
            message=request.message,
            user_id=request.user_id,
            conversation_id=conversation_id,
        )

        return ChatResponse(
            conversation_id=conversation_id,
            message=result["message"],
            tools_used=result.get("tools_used", []),
            execution_time_ms=result.get("execution_time_ms", 0),
            tokens_used=result.get("tokens_used", 0),
            cost=result.get("cost", 0.0),
        )

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/chat/stream", tags=["Chat"])
async def chat_stream(request: ChatRequest):
    """
    Stream a chat response for real-time updates.

    Returns Server-Sent Events (SSE) with incremental updates.
    """
    from fastapi.responses import StreamingResponse
    import json

    conversation_id = request.conversation_id or str(uuid4())

    async def generate():
        async for event in agent_executor.stream(
            message=request.message,
            user_id=request.user_id,
            conversation_id=conversation_id,
        ):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


# ============================================================================
# WebSocket Endpoint
# ============================================================================

class ConnectionManager:
    """Manage WebSocket connections"""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"WebSocket connected: {user_id}")

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"WebSocket disconnected: {user_id}")

    async def send_message(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)


manager = ConnectionManager()


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time chat.

    Connect with: ws://host/ws/{user_id}

    Send messages as JSON:
    ```json
    {
        "type": "chat",
        "payload": {
            "message": "Show me production instances",
            "conversation_id": "conv-123"
        }
    }
    ```
    """
    await manager.connect(websocket, user_id)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            payload = data.get("payload", {})

            if msg_type == "chat":
                message = payload.get("message", "")
                conversation_id = payload.get("conversation_id", str(uuid4()))

                # Send status update
                await manager.send_message(user_id, {
                    "type": "status",
                    "payload": {"status": "processing"},
                })

                # Stream execution
                async for event in agent_executor.stream(
                    message=message,
                    user_id=user_id,
                    conversation_id=conversation_id,
                ):
                    await manager.send_message(user_id, {
                        "type": event.get("type", "update"),
                        "payload": event,
                    })

            elif msg_type == "ping":
                await manager.send_message(user_id, {
                    "type": "pong",
                    "payload": {"timestamp": datetime.now(UTC).isoformat()},
                })

    except WebSocketDisconnect:
        manager.disconnect(user_id)


# ============================================================================
# Voice Endpoints
# ============================================================================

@app.post("/api/v1/voice/transcribe", response_model=VoiceTranscription, tags=["Voice"])
async def transcribe_voice(request: VoiceRequest):
    """
    Transcribe voice input to text using Whisper.

    Accepts base64 encoded audio in various formats.
    """
    if not settings.ENABLE_VOICE:
        raise HTTPException(status_code=503, detail="Voice feature is disabled")

    try:
        import base64
        import tempfile
        import whisper

        # Decode audio
        audio_bytes = base64.b64decode(request.audio_data)

        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=f".{request.format}", delete=False) as f:
            f.write(audio_bytes)
            temp_path = f.name

        # Transcribe
        model = whisper.load_model(settings.WHISPER_MODEL_SIZE)
        result = model.transcribe(temp_path)

        # Cleanup
        import os
        os.unlink(temp_path)

        return VoiceTranscription(
            text=result["text"],
            language=result.get("language", "en"),
            confidence=0.95,  # Whisper doesn't provide confidence
            duration_seconds=result.get("duration", 0),
        )

    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@app.post("/api/v1/voice/chat", response_model=ChatResponse, tags=["Voice"])
async def voice_chat(request: VoiceRequest):
    """
    Combined voice transcription and chat.

    Transcribes the audio and processes it as a chat message.
    """
    # First transcribe
    transcription = await transcribe_voice(request)

    # Then chat
    chat_request = ChatRequest(
        message=transcription.text,
        user_id=request.user_id,
        conversation_id=request.conversation_id,
    )

    return await chat(chat_request)


# ============================================================================
# Tool Registry Endpoints
# ============================================================================

@app.get("/api/v1/tools", response_model=List[ToolDefinition], tags=["Tools"])
async def list_tools():
    """
    List all available tools from connected projects.

    Returns tool definitions including:
    - Tool name and description
    - Source project
    - Parameter schema
    - Example usage
    """
    tools = tool_registry.get_all_tools()

    return [
        ToolDefinition(
            name=tool.name,
            description=tool.description,
            project=_get_project_for_tool(tool.name),
            project_name=_get_project_name(_get_project_for_tool(tool.name)),
            parameters=tool.args_schema.schema() if tool.args_schema else {},
            examples=[],
        )
        for tool in tools
    ]


@app.get("/api/v1/tools/{tool_name}", response_model=ToolDefinition, tags=["Tools"])
async def get_tool(tool_name: str):
    """Get details for a specific tool"""
    tool = tool_registry.get_tool_by_name(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    return ToolDefinition(
        name=tool.name,
        description=tool.description,
        project=_get_project_for_tool(tool.name),
        project_name=_get_project_name(_get_project_for_tool(tool.name)),
        parameters=tool.args_schema.schema() if tool.args_schema else {},
        examples=[],
    )


def _get_project_for_tool(tool_name: str) -> int:
    """Map tool name to project number"""
    if tool_name.startswith("ec2_") or tool_name.startswith("rds_") or tool_name.startswith("cloudwatch_"):
        return 1
    elif tool_name.startswith("k8s_"):
        return 3
    elif tool_name in ["trigger_deployment", "rollback_deployment"]:
        return 4
    elif tool_name in ["search_logs", "query_threats"]:
        return 5
    elif tool_name in ["get_metrics", "query_traces"]:
        return 6
    return 0


def _get_project_name(project_num: int) -> str:
    """Get project name by number"""
    names = {
        1: "MCP AWS Server",
        2: "LLM Security Gateway",
        3: "K8s AgentOps Platform",
        4: "Enterprise CI/CD Framework",
        5: "Centralized Logging & Threat Analytics",
        6: "Multi-Cloud Observability Fabric",
    }
    return names.get(project_num, "Unknown")


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Run the application"""
    uvicorn.run(
        "src.api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS,
        reload=settings.DEBUG,
    )


if __name__ == "__main__":
    main()
