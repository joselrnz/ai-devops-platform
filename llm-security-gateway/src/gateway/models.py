"""
Pydantic models for LLM Security Gateway.

Provides type-safe request/response models with validation.
"""

from typing import List, Dict, Optional, Literal, Any
from datetime import datetime, UTC
from pydantic import BaseModel, Field, field_validator


class Message(BaseModel):
    """Chat message"""
    role: Literal["system", "user", "assistant"] = Field(..., description="Message role")
    content: str = Field(..., min_length=1, description="Message content")

    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "What is the weather today?"
            }
        }


class CompletionRequest(BaseModel):
    """LLM completion request"""
    model: str = Field(..., description="Model name (e.g., gpt-4, claude-3-opus)")
    messages: List[Message] = Field(..., min_length=1, description="Chat messages")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(1000, ge=1, le=32000, description="Maximum tokens to generate")
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description="Nucleus sampling")
    frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)

    @field_validator('model')
    @classmethod
    def validate_model(cls, v: str) -> str:
        """Validate model name"""
        allowed_models = [
            'gpt-4', 'gpt-3.5-turbo',
            'claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku',
            'command', 'command-light',
            'local'
        ]
        if v not in allowed_models:
            raise ValueError(f"Model {v} not in allowed list: {allowed_models}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "model": "gpt-4",
                "messages": [
                    {"role": "user", "content": "Explain quantum computing"}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            }
        }


class Usage(BaseModel):
    """Token usage statistics"""
    prompt_tokens: int = Field(..., ge=0)
    completion_tokens: int = Field(..., ge=0)
    total_tokens: int = Field(..., ge=0)

    @field_validator('total_tokens')
    @classmethod
    def validate_total(cls, v: int, info) -> int:
        """Ensure total = prompt + completion"""
        data = info.data
        expected = data.get('prompt_tokens', 0) + data.get('completion_tokens', 0)
        if v != expected:
            raise ValueError(f"total_tokens must equal prompt_tokens + completion_tokens")
        return v


class CompletionResponse(BaseModel):
    """LLM completion response"""
    id: str = Field(..., description="Unique request ID")
    model: str = Field(..., description="Model used")
    choices: List[Dict[str, Any]] = Field(..., description="Generated choices")
    usage: Usage = Field(..., description="Token usage")
    cost: float = Field(..., ge=0.0, description="Cost in USD")
    latency_ms: int = Field(..., ge=0, description="Response latency")
    created: int = Field(default_factory=lambda: int(datetime.now(UTC).timestamp()))

    class Config:
        json_schema_extra = {
            "example": {
                "id": "chatcmpl-abc123",
                "model": "gpt-4",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Quantum computing uses quantum bits..."
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": 15,
                    "completion_tokens": 150,
                    "total_tokens": 165
                },
                "cost": 0.00495,
                "latency_ms": 1234,
                "created": 1701446400
            }
        }


class SecurityEvent(BaseModel):
    """Security event detected during processing"""
    event_type: Literal["pii_detected", "prompt_injection", "rate_limit", "policy_violation"]
    severity: Literal["low", "medium", "high", "critical"]
    description: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AuditLog(BaseModel):
    """Audit log entry"""
    request_id: str = Field(..., description="Unique request ID")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    user_id: str = Field(..., description="User/service identifier")
    tenant_id: Optional[str] = Field(None, description="Tenant identifier")

    # Request details
    model: str
    endpoint: str
    prompt_tokens: int = Field(..., ge=0)
    completion_tokens: int = Field(..., ge=0)
    total_tokens: int = Field(..., ge=0)

    # Response details
    status_code: int = Field(..., ge=100, lt=600)
    response_time_ms: int = Field(..., ge=0)
    error_message: Optional[str] = None

    # Security events
    pii_detected: bool = Field(False)
    pii_entities: Optional[List[str]] = None
    prompt_injection_detected: bool = Field(False)
    policy_violations: Optional[List[str]] = None

    # Cost tracking
    estimated_cost: float = Field(..., ge=0.0)

    # Metadata
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "req-abc123",
                "timestamp": "2024-12-01T20:00:00Z",
                "user_id": "user-001",
                "tenant_id": "acme-corp",
                "model": "gpt-4",
                "endpoint": "/v1/chat/completions",
                "prompt_tokens": 25,
                "completion_tokens": 150,
                "total_tokens": 175,
                "status_code": 200,
                "response_time_ms": 1234,
                "pii_detected": True,
                "pii_entities": ["EMAIL_ADDRESS", "PHONE_NUMBER"],
                "estimated_cost": 0.00525,
                "ip_address": "192.168.1.100"
            }
        }


class RateLimitInfo(BaseModel):
    """Rate limit information"""
    limit_type: Literal["requests", "tokens", "cost"]
    limit: int = Field(..., ge=0, description="Maximum allowed")
    remaining: int = Field(..., ge=0, description="Remaining quota")
    reset_at: datetime = Field(..., description="When quota resets")
    retry_after: Optional[int] = Field(None, ge=0, description="Seconds until retry allowed")

    @field_validator('remaining')
    @classmethod
    def validate_remaining(cls, v: int, info) -> int:
        """Ensure remaining <= limit"""
        data = info.data
        limit = data.get('limit', 0)
        if v > limit:
            raise ValueError("remaining cannot exceed limit")
        return v


class HealthCheck(BaseModel):
    """Health check response"""
    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    checks: Dict[str, bool] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2024-12-01T20:00:00Z",
                "checks": {
                    "redis": True,
                    "postgres": True,
                    "opa": True,
                    "presidio": True
                }
            }
        }
