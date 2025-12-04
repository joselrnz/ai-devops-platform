"""
Pydantic models for MCP AWS Server.

Provides type-safe request/response models with validation for all AWS tools.
"""

from typing import List, Dict, Optional, Literal, Any
from datetime import datetime, UTC
from pydantic import BaseModel, Field, field_validator, IPvAnyAddress


# ============================================================================
# MCP Protocol Models
# ============================================================================

class MCPRequest(BaseModel):
    """MCP JSON-RPC 2.0 request"""
    jsonrpc: Literal["2.0"] = Field("2.0", description="JSON-RPC version")
    id: str = Field(..., description="Unique request identifier")
    method: Literal["tools/list", "tools/call"] = Field(..., description="RPC method")
    params: Optional[Dict[str, Any]] = Field(None, description="Method parameters")

    class Config:
        json_schema_extra = {
            "example": {
                "jsonrpc": "2.0",
                "id": "req-123",
                "method": "tools/call",
                "params": {
                    "name": "ec2_list_instances",
                    "arguments": {"filters": {"tag:Environment": "production"}}
                }
            }
        }


class MCPResponse(BaseModel):
    """MCP JSON-RPC 2.0 response"""
    jsonrpc: Literal["2.0"] = "2.0"
    id: str
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

    @field_validator('error')
    @classmethod
    def validate_error(cls, v: Optional[Dict[str, Any]], info) -> Optional[Dict[str, Any]]:
        """Ensure either result or error is set, not both"""
        data = info.data
        if v is not None and data.get('result') is not None:
            raise ValueError("Cannot have both result and error")
        return v


class Tool(BaseModel):
    """MCP Tool definition"""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    parameters: Dict[str, Any] = Field(..., description="JSON Schema for parameters")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "ec2_list_instances",
                "description": "List EC2 instances with optional filters",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filters": {
                            "type": "object",
                            "description": "Tag filters"
                        }
                    }
                }
            }
        }


# ============================================================================
# EC2 Models
# ============================================================================

class EC2Tag(BaseModel):
    """EC2 resource tag"""
    key: str = Field(..., min_length=1, max_length=128)
    value: str = Field(..., max_length=256)


class EC2Instance(BaseModel):
    """EC2 instance details"""
    instance_id: str = Field(..., regex=r'^i-[a-f0-9]{8,17}$')
    instance_type: str = Field(..., description="Instance type (e.g., t2.micro)")
    state: Literal["pending", "running", "stopping", "stopped", "shutting-down", "terminated"]
    public_ip: Optional[IPvAnyAddress] = None
    private_ip: Optional[IPvAnyAddress] = None
    availability_zone: str
    launch_time: datetime
    tags: List[EC2Tag] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "instance_id": "i-1234567890abcdef0",
                "instance_type": "t2.micro",
                "state": "running",
                "public_ip": "54.123.45.67",
                "private_ip": "10.0.1.10",
                "availability_zone": "us-east-1a",
                "launch_time": "2024-12-01T20:00:00Z",
                "tags": [
                    {"key": "Name", "value": "web-server-01"},
                    {"key": "Environment", "value": "production"}
                ]
            }
        }


class EC2InstancesResponse(BaseModel):
    """Response for listing EC2 instances"""
    instances: List[EC2Instance]
    count: int = Field(..., ge=0)

    @field_validator('count')
    @classmethod
    def validate_count(cls, v: int, info) -> int:
        """Ensure count matches instances length"""
        data = info.data
        instances = data.get('instances', [])
        if v != len(instances):
            raise ValueError(f"count must match instances length")
        return v


# ============================================================================
# ECS Models
# ============================================================================

class ECSCluster(BaseModel):
    """ECS cluster details"""
    cluster_name: str = Field(..., min_length=1, max_length=255)
    cluster_arn: str = Field(..., regex=r'^arn:aws:ecs:')
    status: Literal["ACTIVE", "PROVISIONING", "DEPROVISIONING", "FAILED", "INACTIVE"]
    registered_container_instances_count: int = Field(..., ge=0)
    running_tasks_count: int = Field(..., ge=0)
    pending_tasks_count: int = Field(..., ge=0)
    active_services_count: int = Field(..., ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "cluster_name": "production-cluster",
                "cluster_arn": "arn:aws:ecs:us-east-1:123456789012:cluster/production-cluster",
                "status": "ACTIVE",
                "registered_container_instances_count": 3,
                "running_tasks_count": 10,
                "pending_tasks_count": 0,
                "active_services_count": 5
            }
        }


class ECSService(BaseModel):
    """ECS service details"""
    service_name: str
    service_arn: str
    status: Literal["ACTIVE", "DRAINING", "INACTIVE"]
    desired_count: int = Field(..., ge=0)
    running_count: int = Field(..., ge=0)
    pending_count: int = Field(..., ge=0)
    task_definition: str
    launch_type: Literal["EC2", "FARGATE", "EXTERNAL"]

    class Config:
        json_schema_extra = {
            "example": {
                "service_name": "web-service",
                "service_arn": "arn:aws:ecs:us-east-1:123456789012:service/production-cluster/web-service",
                "status": "ACTIVE",
                "desired_count": 3,
                "running_count": 3,
                "pending_count": 0,
                "task_definition": "web-app:5",
                "launch_type": "FARGATE"
            }
        }


# ============================================================================
# RDS Models
# ============================================================================

class RDSInstance(BaseModel):
    """RDS database instance details"""
    db_instance_identifier: str = Field(..., min_length=1, max_length=63)
    db_instance_class: str
    engine: str
    engine_version: str
    db_instance_status: str
    endpoint: Optional[str] = None
    port: Optional[int] = Field(None, ge=1, le=65535)
    allocated_storage: int = Field(..., ge=20, le=65536, description="Storage in GB")
    availability_zone: str
    multi_az: bool = Field(False, description="Multi-AZ deployment")
    publicly_accessible: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "db_instance_identifier": "production-db",
                "db_instance_class": "db.t3.micro",
                "engine": "postgres",
                "engine_version": "15.4",
                "db_instance_status": "available",
                "endpoint": "production-db.c1234567890.us-east-1.rds.amazonaws.com",
                "port": 5432,
                "allocated_storage": 100,
                "availability_zone": "us-east-1a",
                "multi_az": True,
                "publicly_accessible": False
            }
        }


class RDSSnapshot(BaseModel):
    """RDS database snapshot"""
    db_snapshot_identifier: str
    db_instance_identifier: str
    snapshot_create_time: datetime
    engine: str
    allocated_storage: int = Field(..., ge=0)
    status: str
    snapshot_type: Literal["automated", "manual", "shared", "public"]

    class Config:
        json_schema_extra = {
            "example": {
                "db_snapshot_identifier": "production-db-snapshot-2024-12-01",
                "db_instance_identifier": "production-db",
                "snapshot_create_time": "2024-12-01T20:00:00Z",
                "engine": "postgres",
                "allocated_storage": 100,
                "status": "available",
                "snapshot_type": "manual"
            }
        }


# ============================================================================
# CloudWatch Models
# ============================================================================

class MetricDatapoint(BaseModel):
    """CloudWatch metric datapoint"""
    timestamp: datetime
    average: Optional[float] = None
    maximum: Optional[float] = None
    minimum: Optional[float] = None
    sum: Optional[float] = None
    sample_count: Optional[float] = None
    unit: Optional[str] = None


class MetricStatistics(BaseModel):
    """CloudWatch metric statistics"""
    metric_name: str
    namespace: str
    dimensions: Dict[str, str] = Field(default_factory=dict)
    datapoints: List[MetricDatapoint]

    class Config:
        json_schema_extra = {
            "example": {
                "metric_name": "CPUUtilization",
                "namespace": "AWS/EC2",
                "dimensions": {"InstanceId": "i-1234567890abcdef0"},
                "datapoints": [
                    {
                        "timestamp": "2024-12-01T20:00:00Z",
                        "average": 45.2,
                        "maximum": 78.5,
                        "minimum": 12.3,
                        "unit": "Percent"
                    }
                ]
            }
        }


class CloudWatchAlarm(BaseModel):
    """CloudWatch alarm"""
    alarm_name: str
    alarm_description: Optional[str] = None
    alarm_arn: str
    state_value: Literal["OK", "ALARM", "INSUFFICIENT_DATA"]
    state_reason: str
    state_updated_timestamp: datetime
    metric_name: str
    namespace: str
    threshold: float
    comparison_operator: str

    class Config:
        json_schema_extra = {
            "example": {
                "alarm_name": "high-cpu-alarm",
                "alarm_description": "Triggers when CPU exceeds 80%",
                "alarm_arn": "arn:aws:cloudwatch:us-east-1:123456789012:alarm:high-cpu-alarm",
                "state_value": "ALARM",
                "state_reason": "Threshold Crossed: 1 datapoint [85.0] was greater than the threshold [80.0]",
                "state_updated_timestamp": "2024-12-01T20:00:00Z",
                "metric_name": "CPUUtilization",
                "namespace": "AWS/EC2",
                "threshold": 80.0,
                "comparison_operator": "GreaterThanThreshold"
            }
        }


# ============================================================================
# Audit Log Models
# ============================================================================

class AuditLogEntry(BaseModel):
    """Audit log entry for AWS operations"""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    user_id: str = Field(..., description="User or agent identifier")
    operation: str = Field(..., description="Operation performed (e.g., ec2_start_instance)")
    resource_type: str = Field(..., description="Resource type (e.g., EC2, RDS)")
    resource_id: str = Field(..., description="Resource identifier")
    result: Literal["success", "failure"]
    error_message: Optional[str] = None
    duration_ms: int = Field(..., ge=0, description="Operation duration")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2024-12-01T20:00:00Z",
                "user_id": "agent-claude-001",
                "operation": "ec2_start_instance",
                "resource_type": "EC2",
                "resource_id": "i-1234567890abcdef0",
                "result": "success",
                "duration_ms": 1247,
                "metadata": {
                    "previous_state": "stopped",
                    "current_state": "pending"
                }
            }
        }
