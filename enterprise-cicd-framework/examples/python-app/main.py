"""
Example Python FastAPI application demonstrating CI/CD best practices.
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, make_asgi_app
from pydantic import BaseModel
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Prometheus metrics
request_counter = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])

# Create FastAPI app
app = FastAPI(
    title="Example Python App",
    description="Demonstrates CI/CD pipeline with security scanning, testing, and monitoring",
    version="1.0.0"
)

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    version: str


class MessageRequest(BaseModel):
    """Message request model."""
    message: str


class MessageResponse(BaseModel):
    """Message response model."""
    message: str
    reversed: str
    length: int


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    logger.info("Health check requested")
    request_counter.labels(method="GET", endpoint="/health", status="200").inc()
    return HealthResponse(status="healthy", version="1.0.0")


@app.get("/ready", response_model=HealthResponse)
async def ready():
    """Readiness check endpoint."""
    logger.info("Readiness check requested")
    request_counter.labels(method="GET", endpoint="/ready", status="200").inc()
    return HealthResponse(status="ready", version="1.0.0")


@app.get("/")
async def root():
    """Root endpoint."""
    logger.info("Root endpoint accessed")
    request_counter.labels(method="GET", endpoint="/", status="200").inc()
    return {"message": "Welcome to the Example Python App"}


@app.post("/process", response_model=MessageResponse)
async def process_message(request: MessageRequest):
    """
    Process a message by reversing it and returning its length.

    Args:
        request: Message request containing the message to process

    Returns:
        MessageResponse with original, reversed message and length
    """
    logger.info(f"Processing message: {request.message}")

    if not request.message:
        logger.warning("Empty message received")
        request_counter.labels(method="POST", endpoint="/process", status="400").inc()
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    reversed_message = request.message[::-1]

    logger.info(f"Message processed successfully: {len(request.message)} characters")
    request_counter.labels(method="POST", endpoint="/process", status="200").inc()

    return MessageResponse(
        message=request.message,
        reversed=reversed_message,
        length=len(request.message)
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unexpected errors."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    request_counter.labels(method=request.method, endpoint=request.url.path, status="500").inc()
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
