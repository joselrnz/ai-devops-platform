"""
Pydantic models for Natural Language Automation Hub.

Type-safe request/response models with validation for the NL automation platform.
"""

from typing import List, Dict, Optional, Literal, Any, Union
from datetime import datetime, UTC
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Chat & Conversation Models
# ============================================================================

class ChatMessage(BaseModel):
    """Single chat message in a conversation"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    role: Literal["user", "assistant", "system"] = Field(..., description="Message role")
    content: str = Field(..., min_length=1, description="Message content")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "msg-123",
                "role": "user",
                "content": "Deploy auth-service to production",
                "timestamp": "2024-12-01T20:00:00Z"
            }
        }


class Conversation(BaseModel):
    """Conversation session with message history"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = Field(..., description="User identifier")
    messages: List[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    """Incoming chat request from user"""
    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID")
    user_id: str = Field(..., description="User identifier")
    stream: bool = Field(False, description="Enable streaming response")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Show me all running EC2 instances in production",
                "conversation_id": "conv-456",
                "user_id": "user-001",
                "stream": False
            }
        }


class ChatResponse(BaseModel):
    """Chat response from the agent"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    conversation_id: str = Field(..., description="Conversation ID")
    message: str = Field(..., description="Agent response")
    tools_used: List[str] = Field(default_factory=list, description="Tools invoked")
    execution_time_ms: int = Field(..., ge=0, description="Total execution time")
    tokens_used: int = Field(0, ge=0, description="Total tokens consumed")
    cost: float = Field(0.0, ge=0.0, description="Estimated cost in USD")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Config:
        json_schema_extra = {
            "example": {
                "id": "resp-789",
                "conversation_id": "conv-456",
                "message": "I found 5 running EC2 instances in production...",
                "tools_used": ["ec2_list_instances"],
                "execution_time_ms": 1234,
                "tokens_used": 350,
                "cost": 0.0105
            }
        }


# ============================================================================
# Agent State Models (LangGraph)
# ============================================================================

class AgentIntent(BaseModel):
    """Parsed intent from user message"""
    action: str = Field(..., description="Identified action (e.g., 'deploy', 'query', 'troubleshoot')")
    target_project: Optional[int] = Field(None, ge=1, le=6, description="Target project number (1-6)")
    entities: Dict[str, Any] = Field(default_factory=dict, description="Extracted entities")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")

    class Config:
        json_schema_extra = {
            "example": {
                "action": "list_instances",
                "target_project": 1,
                "entities": {"service": "EC2", "environment": "production"},
                "confidence": 0.95
            }
        }


class ToolCall(BaseModel):
    """Record of a tool execution"""
    tool_name: str = Field(..., description="Tool name")
    project: int = Field(..., ge=1, le=6, description="Project number")
    arguments: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: int = Field(0, ge=0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AgentState(BaseModel):
    """LangGraph agent state"""
    messages: List[ChatMessage] = Field(default_factory=list)
    current_intent: Optional[AgentIntent] = None
    tool_calls: List[ToolCall] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    completed: bool = Field(False)


# ============================================================================
# Tool Registry Models
# ============================================================================

class ToolDefinition(BaseModel):
    """Definition of an available tool"""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    project: int = Field(..., ge=1, le=6, description="Source project")
    project_name: str = Field(..., description="Project name")
    parameters: Dict[str, Any] = Field(..., description="JSON Schema for parameters")
    examples: List[str] = Field(default_factory=list, description="Example usage")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "ec2_list_instances",
                "description": "List EC2 instances with optional filters",
                "project": 1,
                "project_name": "MCP AWS Server",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filters": {"type": "object"}
                    }
                },
                "examples": ["List all running instances", "Show production servers"]
            }
        }


class ToolRegistry(BaseModel):
    """Registry of all available tools"""
    tools: List[ToolDefinition] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get tool by name"""
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None

    def get_tools_for_project(self, project: int) -> List[ToolDefinition]:
        """Get all tools for a specific project"""
        return [t for t in self.tools if t.project == project]


# ============================================================================
# Voice Models (Whisper Integration)
# ============================================================================

class VoiceTranscription(BaseModel):
    """Voice transcription result"""
    text: str = Field(..., description="Transcribed text")
    language: str = Field("en", description="Detected language")
    confidence: float = Field(..., ge=0.0, le=1.0)
    duration_seconds: float = Field(..., ge=0.0, description="Audio duration")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Deploy the authentication service to production",
                "language": "en",
                "confidence": 0.95,
                "duration_seconds": 3.2
            }
        }


class VoiceRequest(BaseModel):
    """Voice input request"""
    audio_data: str = Field(..., description="Base64 encoded audio")
    format: Literal["wav", "mp3", "webm", "ogg"] = Field("webm")
    user_id: str = Field(..., description="User identifier")
    conversation_id: Optional[str] = None


# ============================================================================
# Project Integration Models
# ============================================================================

class ProjectHealth(BaseModel):
    """Health status of a connected project"""
    project: int = Field(..., ge=1, le=6)
    name: str
    status: Literal["healthy", "degraded", "unhealthy", "unknown"]
    latency_ms: Optional[int] = None
    last_check: datetime = Field(default_factory=lambda: datetime.now(UTC))
    error: Optional[str] = None


class ProjectConnection(BaseModel):
    """Connection configuration for a project"""
    project: int = Field(..., ge=1, le=6)
    name: str
    base_url: str
    protocol: Literal["http", "mcp", "grpc"] = "http"
    timeout_seconds: int = Field(30, ge=1, le=300)
    retry_count: int = Field(3, ge=0, le=10)
    headers: Dict[str, str] = Field(default_factory=dict)


# ============================================================================
# Audit & Observability Models
# ============================================================================

class AuditLogEntry(BaseModel):
    """Audit log for automation hub operations"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    user_id: str = Field(..., description="User identifier")
    conversation_id: str = Field(..., description="Conversation ID")
    action: str = Field(..., description="Action performed")
    intent: Optional[AgentIntent] = None
    tools_called: List[str] = Field(default_factory=list)
    projects_accessed: List[int] = Field(default_factory=list)
    result: Literal["success", "failure", "partial"]
    error_message: Optional[str] = None
    execution_time_ms: int = Field(..., ge=0)
    tokens_used: int = Field(0, ge=0)
    cost: float = Field(0.0, ge=0.0)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "audit-001",
                "timestamp": "2024-12-01T20:00:00Z",
                "user_id": "user-001",
                "conversation_id": "conv-456",
                "action": "deploy_service",
                "tools_called": ["k8s_deploy_agent", "get_deployment_status"],
                "projects_accessed": [3, 4],
                "result": "success",
                "execution_time_ms": 5432,
                "tokens_used": 850,
                "cost": 0.0255
            }
        }


class UsageMetrics(BaseModel):
    """Usage metrics for the automation hub"""
    period_start: datetime
    period_end: datetime
    total_requests: int = Field(0, ge=0)
    total_tokens: int = Field(0, ge=0)
    total_cost: float = Field(0.0, ge=0.0)
    requests_by_project: Dict[int, int] = Field(default_factory=dict)
    top_tools: List[Dict[str, Union[str, int]]] = Field(default_factory=list)
    average_latency_ms: float = Field(0.0, ge=0.0)
    error_rate: float = Field(0.0, ge=0.0, le=1.0)


# ============================================================================
# Health Check Models
# ============================================================================

class HealthCheck(BaseModel):
    """Health check response"""
    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    uptime_seconds: int = Field(..., ge=0)
    projects: List[ProjectHealth] = Field(default_factory=list)
    dependencies: Dict[str, bool] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2024-12-01T20:00:00Z",
                "uptime_seconds": 86400,
                "projects": [
                    {"project": 1, "name": "MCP AWS Server", "status": "healthy"},
                    {"project": 2, "name": "LLM Security Gateway", "status": "healthy"}
                ],
                "dependencies": {
                    "redis": True,
                    "postgres": True,
                    "langsmith": True
                }
            }
        }


# ============================================================================
# WebSocket Models
# ============================================================================

class WSMessage(BaseModel):
    """WebSocket message format"""
    type: Literal["chat", "status", "error", "tool_call", "result"]
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class StreamChunk(BaseModel):
    """Streaming response chunk"""
    conversation_id: str
    chunk: str
    is_final: bool = False
    tool_in_progress: Optional[str] = None
