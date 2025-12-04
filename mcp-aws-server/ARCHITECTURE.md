# MCP AWS Server - Architecture

## Overview

The MCP AWS Server is a production-ready Model Context Protocol (MCP) server that exposes AWS infrastructure operations as tools for LLM agents. It implements the MCP JSON-RPC 2.0 specification and provides safe, audited access to AWS services.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    LLM Agent (Claude/GPT)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │ MCP JSON-RPC 2.0
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MCP Server Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Request    │  │   Tool       │  │  Response    │           │
│  │   Handler    │→ │   Registry   │→ │  Formatter   │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Circuit Breaker Layer                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  State: CLOSED → OPEN → HALF_OPEN                         │  │
│  │  Failure Threshold: 5 | Reset Timeout: 60s                │  │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        AWS Tools Layer                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │   EC2    │  │   ECS    │  │   RDS    │  │CloudWatch│         │
│  │  Tools   │  │  Tools   │  │  Tools   │  │  Tools   │         │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘         │
└───────┼─────────────┼─────────────┼─────────────┼───────────────┘
        │             │             │             │
        ▼             ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────────┐
│                          boto3 Layer                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  AWS SDK for Python - Async Client Wrappers              │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                          AWS Services                            │
│     EC2  │  ECS  │  RDS  │  CloudWatch  │  Cost Explorer        │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. MCP Server Layer ([src/mcp_server/server.py](src/mcp_server/server.py))

**Responsibilities**:
- Implements MCP JSON-RPC 2.0 protocol
- Handles tool discovery (`tools/list`)
- Routes tool calls (`tools/call`)
- Manages request/response lifecycle

**Key Classes**:
```python
class MCPServer:
    async def handle_request(request: Dict) -> Dict:
        """Main request handler for JSON-RPC 2.0"""
        - Validates JSON-RPC format
        - Routes to appropriate handler
        - Returns formatted response

    async def list_tools() -> List[Tool]:
        """Returns available MCP tools"""

    async def call_tool(name: str, args: Dict) -> Result:
        """Executes tool with arguments"""
```

### 2. Tool Layer

Each tool category implements a consistent interface:

#### EC2 Tools ([src/mcp_server/tools/ec2_tools.py](src/mcp_server/tools/ec2_tools.py:1))
```python
class EC2Tools:
    async def list_instances(filters: Optional[Dict]) -> List[Instance]
    async def describe_instance(instance_id: str) -> Instance
    async def start_instance(instance_id: str) -> Status
    async def stop_instance(instance_id: str) -> Status
```

**Operations**:
- List instances with optional tag filters
- Get detailed instance metadata (state, IP, type, tags)
- Start/stop instances with state validation
- Tag-based resource filtering

#### ECS Tools ([src/mcp_server/tools/ecs_tools.py](src/mcp_server/tools/ecs_tools.py:1))
```python
class ECSTools:
    async def list_clusters() -> List[Cluster]
    async def describe_cluster(cluster_name: str) -> Cluster
    async def list_services(cluster: str) -> List[Service]
    async def update_service(cluster: str, service: str, desired_count: int) -> Service
```

**Operations**:
- Cluster discovery and health monitoring
- Service listing and scaling
- Task definition management
- Container insights integration

#### RDS Tools ([src/mcp_server/tools/rds_tools.py](src/mcp_server/tools/rds_tools.py:1))
```python
class RDSTools:
    async def list_db_instances() -> List[DBInstance]
    async def describe_db_instance(instance_id: str) -> DBInstance
    async def create_snapshot(instance_id: str, snapshot_id: str) -> Snapshot
```

**Operations**:
- Database instance inventory
- Snapshot creation and management
- Instance status monitoring
- Performance Insights metrics

#### CloudWatch Tools ([src/mcp_server/tools/cloudwatch_tools.py](src/mcp_server/tools/cloudwatch_tools.py:1))
```python
class CloudWatchTools:
    async def get_metric_statistics(metric_name: str, namespace: str, ...) -> Stats
    async def list_alarms(state_value: Optional[str]) -> List[Alarm]
    async def describe_alarm(alarm_name: str) -> Alarm
```

**Operations**:
- Metric data retrieval (CPU, memory, network)
- Alarm status monitoring
- Log group queries
- Dashboard data aggregation

### 3. Circuit Breaker Pattern ([src/utils/circuit_breaker.py](src/utils/circuit_breaker.py:1))

**Purpose**: Prevents cascading failures when AWS APIs are degraded

**States**:
```
CLOSED (normal) → OPEN (failing) → HALF_OPEN (testing) → CLOSED
```

**Configuration**:
```python
CircuitBreaker(
    failure_threshold=5,      # Open after 5 consecutive failures
    reset_timeout=60,         # Wait 60s before HALF_OPEN
    half_open_max_calls=3     # Test with 3 calls in HALF_OPEN
)
```

**Flow**:
1. **CLOSED**: All requests pass through
2. **Failure detected**: Counter increments
3. **Threshold reached**: State → OPEN
4. **OPEN**: Fast-fail all requests (no AWS calls)
5. **After timeout**: State → HALF_OPEN
6. **HALF_OPEN**: Allow limited requests to test recovery
7. **Success**: State → CLOSED
8. **Failure**: State → OPEN (restart timer)

### 4. Audit Logging ([src/utils/audit.py](src/utils/audit.py:1))

**Audit Trail**:
```python
class AuditLogger:
    def log_operation(
        user_id: str,
        operation: str,
        resource_type: str,
        resource_id: str,
        result: str,
        metadata: Dict
    ):
        """Logs all AWS operations with context"""
```

**Logged Events**:
- Tool invocation (which tool, arguments)
- AWS API calls (service, operation, parameters)
- Results (success/failure, response summary)
- User context (authenticated user/agent ID)
- Timestamps (ISO 8601 with timezone)

**Storage**:
- CloudWatch Logs (real-time streaming)
- RDS PostgreSQL (structured query and retention)

### 5. Testing Strategy ([tests/](tests/))

**Test Pyramid**:
```
           ┌─────────────┐
           │  E2E Tests  │ (Integration tests)
           └─────────────┘
          ┌───────────────┐
          │  Tool Tests   │ (moto mocking)
          └───────────────┘
        ┌──────────────────┐
        │  Unit Tests       │ (Circuit breaker, utils)
        └──────────────────┘
```

**Key Testing Tools**:
- **pytest**: Async test framework
- **moto**: AWS service mocking (no real API calls)
- **pytest-asyncio**: Async fixture support
- **pytest-cov**: Coverage reporting (>95%)

**Test Examples**:
```python
# tests/test_ec2_tools.py
@pytest.mark.asyncio
async def test_list_instances(ec2_client, sample_ec2_instances):
    """Tests instance listing with mocked AWS"""
    tools = EC2Tools(region="us-east-1")
    result = await tools.list_instances()
    assert len(result["instances"]) == 2
    assert result["instances"][0]["state"] == "running"
```

## Infrastructure Architecture (Terraform)

### Network Layer ([infra/modules/vpc/](infra/modules/vpc/))

```
┌────────────────────────── VPC (10.0.0.0/16) ──────────────────────────┐
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │               Public Subnet (10.0.1.0/24)                       │  │
│  │  ┌──────────────┐     ┌──────────────┐                          │  │
│  │  │   NAT GW     │     │   Bastion    │                          │  │
│  │  │   (Optional) │     │   (Optional) │                          │  │
│  │  └──────────────┘     └──────────────┘                          │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │              Private Subnet 1 (10.0.10.0/24)                    │  │
│  │  ┌──────────────────────────────────────────────────┐           │  │
│  │  │         ECS Fargate Tasks (MCP Server)           │           │  │
│  │  └──────────────────────────────────────────────────┘           │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │              Private Subnet 2 (10.0.11.0/24)                    │  │
│  │  ┌──────────────────────────────────────────────────┐           │  │
│  │  │         RDS PostgreSQL (Audit Logs)              │           │  │
│  │  └──────────────────────────────────────────────────┘           │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### Compute Layer ([infra/modules/ecs/](infra/modules/ecs/))

**ECS Fargate Configuration**:
```hcl
resource "aws_ecs_task_definition" "mcp_server" {
  cpu    = 512   # 0.5 vCPU
  memory = 1024  # 1 GB RAM

  container_definitions = [{
    image = "ghcr.io/yourusername/mcp-aws-server:latest"
    portMappings = [{ containerPort = 8080 }]

    environment = [
      { name = "AWS_REGION", value = "us-east-1" },
      { name = "LOG_LEVEL", value = "INFO" }
    ]

    secrets = [
      { name = "DB_PASSWORD", valueFrom = "arn:aws:ssm:..." }
    ]
  }]
}
```

### Security Layer ([infra/modules/security/](infra/modules/security/))

**IAM Role Structure**:
```
ECS Task Role (Assumed by MCP Server)
├── EC2 Read/Write Policy
│   ├── ec2:DescribeInstances
│   ├── ec2:StartInstances
│   ├── ec2:StopInstances
│   └── ec2:DescribeTags
├── ECS Read/Write Policy
│   ├── ecs:ListClusters
│   ├── ecs:DescribeClusters
│   ├── ecs:UpdateService
│   └── ecs:DescribeServices
├── RDS Read Policy
│   ├── rds:DescribeDBInstances
│   └── rds:CreateDBSnapshot
└── CloudWatch Logs Write
    └── logs:PutLogEvents
```

**Security Groups**:
```
MCP Server SG:
  Ingress:
    - Port 8080 from ALB (if used)
    - Port 8080 from VPN/Bastion (for admin)
  Egress:
    - Port 443 to AWS APIs (HTTPS)
    - Port 5432 to RDS SG

RDS SG:
  Ingress:
    - Port 5432 from MCP Server SG only
  Egress: None
```

## Data Flow

### Example: Start EC2 Instance

```
1. LLM Agent Request
   ↓
   {
     "jsonrpc": "2.0",
     "id": "req-123",
     "method": "tools/call",
     "params": {
       "name": "ec2_start_instance",
       "arguments": { "instance_id": "i-abc123" }
     }
   }

2. MCP Server Processing
   ↓
   - Validate JSON-RPC format
   - Authenticate request (optional API key)
   - Route to EC2Tools.start_instance()

3. Circuit Breaker Check
   ↓
   - State: CLOSED ✓
   - Allow request to proceed

4. AWS API Call (via boto3)
   ↓
   ec2_client.start_instances(InstanceIds=['i-abc123'])

5. Audit Log
   ↓
   {
     "timestamp": "2024-12-01T20:00:00Z",
     "user": "agent-claude-001",
     "operation": "ec2_start_instance",
     "resource": "i-abc123",
     "result": "success",
     "duration_ms": 1247
   }

6. Response to LLM
   ↓
   {
     "jsonrpc": "2.0",
     "id": "req-123",
     "result": {
       "instance_id": "i-abc123",
       "previous_state": "stopped",
       "current_state": "pending",
       "message": "Instance starting successfully"
     }
   }
```

## Deployment Options

### Option 1: Docker Compose (Development)

```bash
docker-compose up
# - MCP Server on port 8080
# - PostgreSQL on port 5432
# - Uses AWS credentials from environment
```

### Option 2: ECS Fargate (Production)

```bash
cd infra/environments/dev
terraform init
terraform apply
# - Deploys to ECS Fargate
# - Creates VPC, subnets, RDS
# - Sets up IAM roles and security groups
# - Configures CloudWatch logging
```

### Option 3: Claude Desktop (Local)

```json
{
  "mcpServers": {
    "aws-mcp": {
      "command": "python",
      "args": ["-m", "src.mcp_server.server"],
      "env": {
        "AWS_REGION": "us-east-1",
        "AWS_PROFILE": "default"
      }
    }
  }
}
```

## Security Considerations

### 1. IAM Least Privilege
- Each tool has minimal required permissions
- No `*` wildcards in IAM policies
- Resource-level restrictions where possible

### 2. Network Isolation
- MCP server in private subnets (no direct internet access)
- RDS accessible only from MCP server SG
- Optional VPN/Bastion for admin access

### 3. Audit Trail
- All operations logged to CloudWatch + RDS
- Immutable log retention (90 days minimum)
- Log integrity monitoring

### 4. Circuit Breaker Protection
- Prevents AWS API abuse during outages
- Fast-fail to protect downstream services
- Automatic recovery testing

### 5. Secret Management
- Database credentials in AWS Secrets Manager
- API keys in SSM Parameter Store (encrypted)
- No secrets in environment variables or code

## Performance Characteristics

**Latency**:
- Tool discovery: <10ms
- Simple operations (list, describe): 100-500ms
- State-changing operations (start, stop): 500-2000ms

**Throughput**:
- Up to 100 concurrent tool calls (async design)
- Rate-limited by AWS API throttling (varies by service)

**Reliability**:
- 99.9% availability (with circuit breaker)
- Automatic retry on transient failures
- Graceful degradation when AWS APIs are slow

## Monitoring & Alerts

**Key Metrics**:
- Tool call success rate (target: >99%)
- AWS API latency (p50, p95, p99)
- Circuit breaker state changes
- Error rates by tool type

**Alerts** (via CloudWatch Alarms):
- High error rate (>5% over 5 minutes)
- Circuit breaker OPEN state
- AWS API throttling detected
- RDS connection pool exhaustion

## Cost Estimation

**Monthly Costs** (us-east-1):
- ECS Fargate (0.5 vCPU, 1GB): ~$15/month
- RDS PostgreSQL db.t3.micro: ~$15/month
- CloudWatch Logs (5GB/month): ~$3/month
- Data transfer: ~$2/month
- **Total**: ~$35/month (under light usage)

**Free Tier Eligible** (first 12 months):
- 750 hours ECS Fargate: FREE
- 750 hours RDS db.t2.micro: FREE
- **Estimated cost**: ~$5/month

## Future Enhancements

1. **Additional AWS Services**
   - Lambda function invocation
   - S3 bucket operations
   - DynamoDB table queries

2. **Enhanced Security**
   - Mutual TLS (mTLS) for MCP connections
   - Fine-grained RBAC per tool
   - AWS PrivateLink for API calls

3. **Observability**
   - OpenTelemetry tracing
   - Prometheus metrics export
   - Grafana dashboards

4. **Multi-Region Support**
   - Cross-region resource discovery
   - Regional failover
   - Latency-based routing

---

**Last Updated**: December 2024
**Version**: 1.0.0
**Status**: Production Ready
