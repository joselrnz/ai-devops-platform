# NL Automation Hub - Architecture Documentation

## Overview

The Natural Language Automation Hub is the unified control plane for the AI-Augmented DevOps Platform. It enables users to interact with all 6 infrastructure projects through natural language commands via text or voice.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACES                                 │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐                │
│  │ Web Chat  │  │   Voice   │  │   Slack   │  │    API    │                │
│  │  (React)  │  │ (Whisper) │  │   Bot     │  │   Client  │                │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘                │
└────────┼──────────────┼──────────────┼──────────────┼───────────────────────┘
         │              │              │              │
         └──────────────┴──────────────┴──────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    NL AUTOMATION HUB (Project 7)                             │
│                    Kubernetes: nl-automation-hub                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     FastAPI Application                              │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │    │
│  │  │ REST API     │  │  WebSocket   │  │  Voice API   │               │    │
│  │  │ /api/v1/chat │  │  /ws/{user}  │  │ /api/v1/voice│               │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │    │
│  └────────────────────────────┬────────────────────────────────────────┘    │
│                               │                                              │
│  ┌────────────────────────────▼────────────────────────────────────────┐    │
│  │                    LangGraph Agent Engine                            │    │
│  │  ┌────────────────────────────────────────────────────────────┐     │    │
│  │  │                   State Machine                             │     │    │
│  │  │  ┌────────┐    ┌────────────┐    ┌────────────┐            │     │    │
│  │  │  │ Parse  │ →  │   Route    │ →  │  Execute   │            │     │    │
│  │  │  │ Intent │    │  to Tool   │    │   Tools    │            │     │    │
│  │  │  └────────┘    └────────────┘    └────────────┘            │     │    │
│  │  │       ↑                                  │                  │     │    │
│  │  │       └──────────────────────────────────┘                  │     │    │
│  │  │                    (loop until done)                        │     │    │
│  │  └────────────────────────────────────────────────────────────┘     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                               │                                              │
│  ┌────────────────────────────▼────────────────────────────────────────┐    │
│  │                      Tool Registry                                   │    │
│  │  ┌───────────────────────────────────────────────────────────────┐  │    │
│  │  │  Project 1     Project 3     Project 4     Project 5     P6   │  │    │
│  │  │  ─────────     ─────────     ─────────     ─────────     ──   │  │    │
│  │  │  ec2_list      k8s_list      deploy        search_logs  get   │  │    │
│  │  │  ec2_start     k8s_deploy    rollback      query_threats metrics│  │    │
│  │  │  ec2_stop      k8s_scale                                traces│  │    │
│  │  │  rds_describe                                                  │  │    │
│  │  │  cloudwatch                                                    │  │    │
│  │  └───────────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                               │
└────────────────────────────────────────────────────────────────────────────┘
                                │
                 ┌──────────────┼──────────────┐
                 │              │              │
                 ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CONNECTED PROJECTS                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │              PROJECT 2: LLM SECURITY GATEWAY (ALL LLM CALLS)          │   │
│  │  • PII Detection & Redaction        • Rate Limiting                   │   │
│  │  • Prompt Injection Detection       • Cost Tracking                   │   │
│  │  • Multi-Model Routing              • Audit Logging                   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                               │                                              │
│  ┌───────────────┐  ┌────────▼────────┐  ┌───────────────────────────────┐ │
│  │   Project 1   │  │   LLM APIs      │  │          Project 3            │ │
│  │  MCP AWS      │  │  Claude/GPT-4   │  │       K8s AgentOps            │ │
│  │  Server       │  │  Cohere/Local   │  │       Platform                │ │
│  │               │  └─────────────────┘  │                               │ │
│  │  • EC2 ops    │                       │  • Agent deployment           │ │
│  │  • ECS ops    │                       │  • Auto-scaling               │ │
│  │  • RDS ops    │                       │  • CRD management             │ │
│  │  • CloudWatch │                       │                               │ │
│  └───────────────┘                       └───────────────────────────────┘ │
│                                                                               │
│  ┌───────────────┐  ┌───────────────────┐  ┌────────────────────────────┐  │
│  │   Project 4   │  │    Project 5      │  │        Project 6           │  │
│  │  CI/CD        │  │   Logging &       │  │     Observability          │  │
│  │  Framework    │  │   Threat          │  │     Fabric                 │  │
│  │               │  │   Analytics       │  │                            │  │
│  │  • Deployments│  │  • Log search     │  │  • Prometheus metrics      │  │
│  │  • Rollbacks  │  │  • Sigma rules    │  │  • Tempo traces            │  │
│  │  • ArgoCD     │  │  • OpenSearch     │  │  • Grafana dashboards      │  │
│  └───────────────┘  └───────────────────┘  └────────────────────────────┘  │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL SERVICES                                    │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐                   │
│  │   LangSmith   │  │  Anthropic    │  │    OpenAI     │                   │
│  │   (Traces)    │  │  Claude API   │  │   GPT-4 API   │                   │
│  └───────────────┘  └───────────────┘  └───────────────┘                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. FastAPI Application Layer

The main API server handling all user interactions:

```python
# Endpoints
POST /api/v1/chat           # Natural language chat
POST /api/v1/chat/stream    # Streaming response (SSE)
WS   /ws/{user_id}          # WebSocket for real-time chat
POST /api/v1/voice/transcribe  # Voice to text
POST /api/v1/voice/chat     # Voice input + chat
GET  /api/v1/tools          # List available tools
GET  /health                # Health check with project status
```

### 2. LangGraph Agent Engine

State-based agent workflow with conditional routing:

```
┌─────────────────────────────────────────────────────────────────┐
│                    LangGraph State Machine                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  State Definition:                                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  {                                                       │    │
│  │    messages: List[Message],      # Conversation history  │    │
│  │    user_id: str,                 # User identifier       │    │
│  │    conversation_id: str,         # Session ID            │    │
│  │    current_intent: AgentIntent,  # Parsed intent         │    │
│  │    tools_called: List[str],      # Tools executed        │    │
│  │    error: Optional[str]          # Error if any          │    │
│  │  }                                                       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
│  Workflow:                                                       │
│                                                                   │
│  ┌──────────┐                                                    │
│  │  START   │                                                    │
│  └────┬─────┘                                                    │
│       │                                                          │
│       ▼                                                          │
│  ┌──────────┐    has_tool_calls?     ┌──────────┐               │
│  │  AGENT   │ ─────────────────────→ │  TOOLS   │               │
│  │  (LLM)   │         yes            │ (Execute)│               │
│  └────┬─────┘                        └────┬─────┘               │
│       │ no                                │                      │
│       ▼                                   │                      │
│  ┌──────────┐                             │                      │
│  │   END    │ ←───────────────────────────┘                      │
│  └──────────┘                                                    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 3. Tool Registry

Unified interface to all 6 projects:

| Tool Name | Project | Description |
|-----------|---------|-------------|
| `ec2_list_instances` | 1 - MCP AWS | List EC2 instances with filters |
| `ec2_start_instance` | 1 - MCP AWS | Start a stopped instance |
| `ec2_stop_instance` | 1 - MCP AWS | Stop a running instance |
| `rds_describe_instance` | 1 - MCP AWS | Get RDS details |
| `cloudwatch_get_metrics` | 1 - MCP AWS | Query CloudWatch metrics |
| `k8s_list_agents` | 3 - K8s AgentOps | List deployed agents |
| `k8s_deploy_agent` | 3 - K8s AgentOps | Deploy new agent |
| `k8s_scale_agent` | 3 - K8s AgentOps | Scale agent replicas |
| `trigger_deployment` | 4 - CI/CD | Trigger pipeline |
| `rollback_deployment` | 4 - CI/CD | Rollback deployment |
| `search_logs` | 5 - Logging | Search OpenSearch logs |
| `query_threats` | 5 - Logging | Query security alerts |
| `get_metrics` | 6 - Observability | Query Prometheus |
| `query_traces` | 6 - Observability | Search Tempo traces |

## Data Flow Examples

### Example 1: AWS Infrastructure Query

```
User: "Show me all production EC2 instances with high CPU"

┌─────────────────────────────────────────────────────────────────┐
│ Step 1: User Input                                              │
│ POST /api/v1/chat                                               │
│ Body: { message: "Show me all production EC2 instances..." }    │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: LangGraph Agent                                         │
│ • Parse intent: "list_ec2_with_metrics"                         │
│ • Select tools: [ec2_list_instances, cloudwatch_get_metrics]    │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: LLM Call (via Project 2)                                │
│ POST http://llm-security-gateway:8000/v1/chat/completions       │
│ • PII checked                                                   │
│ • Rate limit checked                                            │
│ • Cost tracked                                                  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 4: Tool Execution (Project 1)                              │
│ POST http://mcp-aws-server:8080/tools/call                      │
│ { method: "tools/call", params: { name: "ec2_list_instances" }} │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 5: Response Formatting                                     │
│ LLM formats human-readable response with instance details       │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 6: Return to User                                          │
│ { message: "I found 5 production instances...",                 │
│   tools_used: ["ec2_list_instances"],                           │
│   execution_time_ms: 1234 }                                     │
└─────────────────────────────────────────────────────────────────┘
```

### Example 2: Multi-Project Troubleshooting

```
User: "Why is my API returning 500 errors?"

┌─────────────────────────────────────────────────────────────────┐
│ Agent Reasoning Chain:                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ Step 1: Check metrics (Project 6)                               │
│ Tool: get_metrics                                                │
│ Query: http_requests_total{status="500"}                        │
│ Result: 234 errors in last hour, mostly /api/v1/users           │
│                                                                   │
│ Step 2: Search logs (Project 5)                                 │
│ Tool: search_logs                                                │
│ Query: status:500 AND service:api                               │
│ Result: "Database connection timeout" errors                    │
│                                                                   │
│ Step 3: Check database (Project 1)                              │
│ Tool: rds_describe_instance                                      │
│ Target: production-db                                            │
│ Result: CPU 95%, connections 500/500                            │
│                                                                   │
│ Step 4: Synthesize response                                     │
│ "Your API is returning 500s due to database overload.           │
│  RDS CPU is at 95% and connection pool is exhausted.            │
│  Recommend: Scale RDS or increase connection pool."             │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Infrastructure Architecture

### Kubernetes Deployment

```
┌────────────────────────────────────────────────────────────────┐
│              Kubernetes Cluster (EKS/GKE/AKS)                   │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Namespace: nl-automation-hub                                   │
│  ┌────────────────────────────────────────────────────────────┐│
│  │  Deployment: nl-hub-api                                    ││
│  │  ├─ Replicas: 3 (HPA: 2-10)                               ││
│  │  ├─ Resources: 1 vCPU, 2GB RAM per pod                    ││
│  │  └─ Image: nl-automation-hub:latest                        ││
│  │                                                             ││
│  │  Deployment: nl-hub-frontend                               ││
│  │  ├─ Replicas: 2                                            ││
│  │  ├─ Resources: 0.25 vCPU, 512MB RAM                       ││
│  │  └─ Image: nl-automation-hub-frontend:latest               ││
│  │                                                             ││
│  │  Services:                                                  ││
│  │  ├─ nl-hub-api (ClusterIP, port 8000)                     ││
│  │  └─ nl-hub-frontend (ClusterIP, port 80)                  ││
│  │                                                             ││
│  │  Ingress: nl-hub.your-domain.com                          ││
│  │  ├─ /api/* → nl-hub-api                                   ││
│  │  ├─ /ws/* → nl-hub-api (WebSocket)                        ││
│  │  └─ /* → nl-hub-frontend                                   ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ConfigMap: nl-hub-config                                       │
│  ├─ Project URLs (internal K8s services)                       │
│  ├─ Feature flags                                               │
│  └─ Logging configuration                                       │
│                                                                  │
│  Secret: nl-hub-secrets                                         │
│  ├─ ANTHROPIC_API_KEY                                          │
│  ├─ LANGCHAIN_API_KEY                                          │
│  └─ POSTGRES_PASSWORD                                           │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

### Service Mesh Integration

```
┌────────────────────────────────────────────────────────────────┐
│                   Service Communication                         │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  nl-hub-api                                                     │
│      │                                                          │
│      ├──→ llm-security-gateway.llm-gateway:8000 (LLM calls)   │
│      ├──→ mcp-aws-server.mcp-aws:8080 (AWS tools)             │
│      ├──→ agentops-api.agentops-system:8000 (K8s tools)       │
│      ├──→ cicd-api.cicd:8000 (CI/CD tools)                    │
│      ├──→ opensearch.logging:9200 (Log queries)               │
│      ├──→ prometheus.observability:9090 (Metrics)              │
│      └──→ tempo.observability:3200 (Traces)                   │
│                                                                  │
│  All communication:                                             │
│  • mTLS encrypted (Istio/Linkerd)                              │
│  • Automatic retries (3x)                                       │
│  • Circuit breaker (5 failures → open)                         │
│  • Timeout: 30 seconds                                         │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

## Security Architecture

### Authentication & Authorization

```
┌────────────────────────────────────────────────────────────────┐
│                    Security Layers                              │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Ingress Layer                                               │
│     ├─ TLS termination (Let's Encrypt)                         │
│     ├─ WAF rules                                                │
│     └─ Rate limiting (NGINX)                                   │
│                                                                  │
│  2. API Layer                                                   │
│     ├─ JWT validation                                           │
│     ├─ RBAC enforcement                                         │
│     └─ Input validation (Pydantic)                             │
│                                                                  │
│  3. LLM Gateway (Project 2)                                    │
│     ├─ PII detection & redaction                               │
│     ├─ Prompt injection detection                              │
│     ├─ Content policy enforcement                              │
│     └─ Cost-based rate limiting                                │
│                                                                  │
│  4. Tool Execution                                              │
│     ├─ Least privilege (per-project RBAC)                      │
│     ├─ Audit logging                                           │
│     └─ Confirmation for destructive ops                        │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

## Observability

### Metrics (Prometheus)

```yaml
# Custom metrics exposed
nl_hub_requests_total{method, endpoint, status}
nl_hub_request_duration_seconds{method, endpoint}
nl_hub_tool_calls_total{tool_name, project, status}
nl_hub_tool_duration_seconds{tool_name, project}
nl_hub_llm_tokens_total{model, type}  # prompt/completion
nl_hub_llm_cost_total{model}
nl_hub_active_conversations
nl_hub_active_websockets
```

### Tracing (LangSmith)

All LangGraph executions are traced to LangSmith:
- Complete agent reasoning chain
- Each tool call with inputs/outputs
- LLM calls with prompts and responses
- Token counts and costs
- Latency breakdown

### Logging (Structured)

```json
{
  "timestamp": "2024-12-01T20:00:00Z",
  "level": "INFO",
  "service": "nl-automation-hub",
  "trace_id": "abc123",
  "user_id": "user-001",
  "conversation_id": "conv-456",
  "message": "Tool executed",
  "tool_name": "ec2_list_instances",
  "project": 1,
  "duration_ms": 234,
  "status": "success"
}
```

## Cost Estimation

### Monthly Infrastructure Costs

| Component | Specification | Monthly Cost |
|-----------|--------------|--------------|
| Backend Pods (3x) | 1 vCPU, 2GB RAM | $50 |
| Frontend Pods (2x) | 0.25 vCPU, 512MB | $20 |
| PostgreSQL (RDS) | db.t4g.micro, 20GB | $15 |
| Redis (ElastiCache) | cache.t4g.micro | $15 |
| Load Balancer | ALB | $20 |
| **Subtotal Infrastructure** | | **$120** |

### External Services

| Service | Plan | Monthly Cost |
|---------|------|--------------|
| LangSmith | Pro | $39 |
| Anthropic API | ~50k tokens/day | $50-150 |
| OpenAI API (fallback) | As needed | $20-50 |
| **Subtotal External** | | **$109-239** |

### Total

**~$229-359/month** for Project 7 alone

## Deployment

### Local Development

```bash
# Start dependencies
docker-compose up -d postgres redis

# Start backend
cd nl-automation-hub
pip install -r requirements.txt
uvicorn src.api.main:app --reload

# Start frontend
cd frontend
npm install
npm run dev
```

### Production (Kubernetes)

```bash
# Apply manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml
```

## File Structure

```
nl-automation-hub/
├── src/
│   ├── agent/
│   │   ├── __init__.py
│   │   └── graph.py           # LangGraph agent workflow
│   ├── api/
│   │   ├── __init__.py
│   │   └── main.py            # FastAPI application
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py        # Pydantic settings
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py         # Pydantic models
│   └── tools/
│       ├── __init__.py
│       └── registry.py        # Tool registry
├── frontend/
│   ├── src/
│   │   ├── App.tsx            # React chat component
│   │   ├── main.tsx           # Entry point
│   │   └── index.css          # Tailwind styles
│   ├── package.json
│   └── Dockerfile
├── k8s/
│   ├── namespace.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── ingress.yaml
│   └── hpa.yaml
├── Dockerfile
├── docker-compose.yaml
├── requirements.txt
├── ARCHITECTURE.md
└── README.md
```
