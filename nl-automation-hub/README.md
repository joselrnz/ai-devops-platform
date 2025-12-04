# Natural Language Automation Hub

The unified control plane for the AI-Augmented DevOps Platform. Execute infrastructure operations through natural language commands.

## Overview

NL Automation Hub is the orchestration layer (Project 7) that connects to all 6 projects in the portfolio, enabling users to:

- **Manage AWS infrastructure** via natural language (Project 1)
- **Deploy applications** with simple commands (Projects 3, 4)
- **Troubleshoot issues** by querying logs and metrics (Projects 5, 6)
- **Monitor systems** through conversational queries (Project 6)

All LLM calls are routed through the **LLM Security Gateway** (Project 2) for PII detection, rate limiting, and cost tracking.

## Features

- **LangGraph Agent**: State-based workflow with tool execution
- **Multi-Modal Input**: Text chat, voice (Whisper), WebSocket
- **14 Integrated Tools**: Spanning all 6 infrastructure projects
- **Real-Time Updates**: WebSocket streaming for live feedback
- **LangSmith Tracing**: Complete agent execution visibility
- **Production Ready**: Kubernetes manifests, HPA, health checks

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- API keys: Anthropic/OpenAI, LangSmith

### Local Development

```bash
# Clone repository
git clone https://github.com/yourusername/nl-automation-hub.git
cd nl-automation-hub

# Start dependencies
docker-compose up -d postgres redis

# Install Python dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Start backend
uvicorn src.api.main:app --reload --port 8000

# In another terminal, start frontend
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 for the chat interface.

### Docker Compose (Full Stack)

```bash
# Set API keys
export ANTHROPIC_API_KEY=sk-ant-xxx
export LANGCHAIN_API_KEY=lsv2_pt_xxx

# Start everything
docker-compose up --build

# Access
# Frontend: http://localhost:3000
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/chat` | POST | Send a chat message |
| `/api/v1/chat/stream` | POST | Streaming response (SSE) |
| `/ws/{user_id}` | WebSocket | Real-time chat |
| `/api/v1/voice/transcribe` | POST | Voice to text |
| `/api/v1/voice/chat` | POST | Voice input + chat |
| `/api/v1/tools` | GET | List available tools |
| `/health` | GET | Health check |

## Example Usage

### REST API

```bash
# Send a chat message
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me all running EC2 instances in production",
    "user_id": "user-001"
  }'

# Response
{
  "conversation_id": "conv-123",
  "message": "I found 5 running EC2 instances in production...",
  "tools_used": ["ec2_list_instances"],
  "execution_time_ms": 1234
}
```

### WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/user-001');

ws.send(JSON.stringify({
  type: 'chat',
  payload: {
    message: 'Deploy auth-service to staging',
    conversation_id: 'conv-123'
  }
}));

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data); // { type: 'result', payload: {...} }
};
```

## Available Tools

| Tool | Project | Description |
|------|---------|-------------|
| `ec2_list_instances` | 1 | List EC2 instances |
| `ec2_start_instance` | 1 | Start an instance |
| `ec2_stop_instance` | 1 | Stop an instance |
| `rds_describe_instance` | 1 | Get RDS details |
| `cloudwatch_get_metrics` | 1 | Query metrics |
| `k8s_list_agents` | 3 | List K8s agents |
| `k8s_deploy_agent` | 3 | Deploy an agent |
| `k8s_scale_agent` | 3 | Scale replicas |
| `trigger_deployment` | 4 | Trigger pipeline |
| `rollback_deployment` | 4 | Rollback |
| `search_logs` | 5 | Search logs |
| `query_threats` | 5 | Query alerts |
| `get_metrics` | 6 | Prometheus query |
| `query_traces` | 6 | Tempo traces |

## Architecture

```
User Input (Text/Voice/WebSocket)
        │
        ▼
┌─────────────────────────────────────┐
│   FastAPI Application                │
│   ├─ REST API                        │
│   ├─ WebSocket Handler               │
│   └─ Voice Processing (Whisper)      │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│   LangGraph Agent                    │
│   ├─ Intent Parsing                  │
│   ├─ Tool Selection                  │
│   ├─ HITL Checkpoint ◄───────────┐  │
│   └─ Response Synthesis          │  │
└────────────────┬─────────────────┼──┘
                 │                 │
    ┌────────────┴────────────┐    │ User
    ▼                         ▼    │ Confirmation
┌─────────────┐      ┌─────────────────┐
│ LLM Gateway │      │  Tool Registry   │
│ (Project 2) │      │  (Projects 1-6)  │
│ + Guardrails│      └─────────────────┘
└─────────────┘
```

## 🛡️ Human-in-the-Loop (HITL) & Guardrails

The agent implements a conversational confirmation flow to prevent unintended actions and hallucinations.

### LangGraph State Machine with HITL

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LANGGRAPH AGENT STATE MACHINE                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐          │
│   │  START   │────▶│  PARSE   │────▶│  PLAN    │────▶│  CHECK   │          │
│   │          │     │  INTENT  │     │  TOOLS   │     │  RISK    │          │
│   └──────────┘     └──────────┘     └──────────┘     └────┬─────┘          │
│                                                           │                 │
│                         ┌─────────────────────────────────┤                 │
│                         │                                 │                 │
│                         ▼                                 ▼                 │
│              ┌──────────────────┐              ┌──────────────────┐         │
│              │   LOW RISK       │              │   HIGH RISK      │         │
│              │   (Read-only)    │              │   (Mutations)    │         │
│              └────────┬─────────┘              └────────┬─────────┘         │
│                       │                                 │                   │
│                       │                                 ▼                   │
│                       │                    ┌──────────────────────┐         │
│                       │                    │  HITL CHECKPOINT     │         │
│                       │                    │  ┌────────────────┐  │         │
│                       │                    │  │ Show user:     │  │         │
│                       │                    │  │ • Action plan  │  │         │
│                       │                    │  │ • Affected     │  │         │
│                       │                    │  │   resources    │  │         │
│                       │                    │  │ • Impact       │  │         │
│                       │                    │  │ • Reversibility│  │         │
│                       │                    │  └────────────────┘  │         │
│                       │                    └────────┬─────────────┘         │
│                       │                             │                       │
│                       │         ┌───────────────────┼───────────────────┐   │
│                       │         │                   │                   │   │
│                       │         ▼                   ▼                   ▼   │
│                       │  ┌────────────┐     ┌────────────┐     ┌──────────┐│
│                       │  │  CONFIRM   │     │   MODIFY   │     │  CANCEL  ││
│                       │  │  "yes"     │     │  "change X"│     │  "no"    ││
│                       │  └─────┬──────┘     └─────┬──────┘     └────┬─────┘│
│                       │        │                  │                 │      │
│                       │        │                  │                 │      │
│                       │        ▼                  │                 │      │
│                       │  ┌────────────┐           │                 │      │
│                       └─▶│  EXECUTE   │◀──────────┘                 │      │
│                          │   TOOLS    │                             │      │
│                          └─────┬──────┘                             │      │
│                                │                                    │      │
│                                ▼                                    ▼      │
│                          ┌────────────┐                      ┌──────────┐  │
│                          │  VALIDATE  │                      │  ABORT   │  │
│                          │  RESULTS   │                      │  MESSAGE │  │
│                          └─────┬──────┘                      └──────────┘  │
│                                │                                           │
│                                ▼                                           │
│                          ┌────────────┐                                    │
│                          │  RESPOND   │                                    │
│                          │  (Grounded)│                                    │
│                          └────────────┘                                    │
│                                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Example Dialogue: Interactive Confirmation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ CONVERSATION FLOW                                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ 👤 User: "Terminate all EC2 instances tagged as 'test'"                     │
│                                                                              │
│ 🤖 Agent: I found 4 instances matching 'test' tag. Before proceeding,       │
│          let me confirm the details:                                         │
│                                                                              │
│    ┌────────────────────────────────────────────────────────────────────┐   │
│    │ 🛑 ACTION REQUIRES CONFIRMATION                                     │   │
│    │                                                                      │   │
│    │ Operation: TERMINATE EC2 instances                                  │   │
│    │ Environment: Mixed (3 dev, 1 staging)                               │   │
│    │ Reversibility: ❌ IRREVERSIBLE                                      │   │
│    │                                                                      │   │
│    │ Instances to terminate:                                             │   │
│    │ ┌──────────────────┬───────────┬─────────┬────────────────────┐    │   │
│    │ │ Instance ID      │ Type      │ Env     │ Name               │    │   │
│    │ ├──────────────────┼───────────┼─────────┼────────────────────┤    │   │
│    │ │ i-0a1b2c3d4e     │ t3.medium │ dev     │ test-api-server    │    │   │
│    │ │ i-1b2c3d4e5f     │ t3.small  │ dev     │ test-worker-01     │    │   │
│    │ │ i-2c3d4e5f6g     │ t3.small  │ dev     │ test-worker-02     │    │   │
│    │ │ i-3d4e5f6g7h     │ t3.large  │ staging │ test-load-balancer │ ⚠️ │   │
│    │ └──────────────────┴───────────┴─────────┴────────────────────┘    │   │
│    │                                                                      │   │
│    │ ⚠️  Warning: i-3d4e5f6g7h is in STAGING environment                │   │
│    │                                                                      │   │
│    │ Monthly cost savings: ~$45.00                                       │   │
│    └────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│    How would you like to proceed?                                           │
│    • Type "confirm all" to terminate all 4 instances                        │
│    • Type "skip staging" to only terminate dev instances (3)                │
│    • Type "cancel" to abort                                                 │
│    • Ask me anything about these instances                                  │
│                                                                              │
│ ─────────────────────────────────────────────────────────────────────────── │
│                                                                              │
│ 👤 User: "skip staging"                                                     │
│                                                                              │
│ 🤖 Agent: Understood. I'll only terminate the 3 dev instances.             │
│                                                                              │
│    Executing: ec2_terminate_instances([i-0a1b2c3d4e, i-1b2c3d4e5f,         │
│                                        i-2c3d4e5f6g])                       │
│                                                                              │
│    ✅ Successfully terminated 3 instances:                                  │
│    • i-0a1b2c3d4e (test-api-server) - terminated                           │
│    • i-1b2c3d4e5f (test-worker-01) - terminated                            │
│    • i-2c3d4e5f6g (test-worker-02) - terminated                            │
│                                                                              │
│    ℹ️  Skipped: i-3d4e5f6g7h (staging - per your request)                  │
│                                                                              │
│    Estimated monthly savings: ~$32.00                                       │
│                                                                              │
│ ─────────────────────────────────────────────────────────────────────────── │
│                                                                              │
│ 👤 User: "What was the CPU usage on those instances before termination?"    │
│                                                                              │
│ 🤖 Agent: Based on the CloudWatch metrics I retrieved before termination:  │
│                                                                              │
│    │ Instance         │ Avg CPU (7d) │ Peak CPU │ Last Active    │         │
│    │──────────────────│──────────────│──────────│────────────────│         │
│    │ test-api-server  │ 3.2%         │ 12%      │ 2 days ago     │         │
│    │ test-worker-01   │ 0.8%         │ 4%       │ 5 days ago     │         │
│    │ test-worker-02   │ 1.1%         │ 6%       │ 5 days ago     │         │
│                                                                              │
│    📊 Source: CloudWatch metrics (namespace: AWS/EC2)                       │
│    ⏱️  Data retrieved at: 2024-12-02T10:23:45Z                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Anti-Hallucination: Grounded Responses

Every response is grounded in actual tool outputs:

```python
# src/agent/graph.py - Response grounding

class GroundedResponse(BaseModel):
    """Ensures all claims are backed by tool outputs."""

    claims: list[Claim]
    tool_outputs: dict[str, Any]

    @validator('claims')
    def validate_grounding(cls, claims, values):
        tool_outputs = values.get('tool_outputs', {})
        for claim in claims:
            if claim.source not in tool_outputs:
                raise ValueError(f"Claim '{claim.text}' not grounded in tool output")
            if not claim.verify_against(tool_outputs[claim.source]):
                raise ValueError(f"Claim '{claim.text}' contradicts tool output")
        return claims

# Agent response format
{
  "response": "Found 12 running EC2 instances in production.",
  "grounding": {
    "claims": [
      {
        "text": "12 running EC2 instances",
        "source": "ec2_list_instances",
        "evidence": "len(response['Reservations']) == 12"
      },
      {
        "text": "in production",
        "source": "ec2_list_instances",
        "evidence": "all instances have tag Env=production"
      }
    ]
  },
  "confidence": 0.98,
  "tools_used": ["ec2_list_instances"],
  "can_verify": true
}
```

### Guardrail Integration

```yaml
# config/agent_guardrails.yaml
agent:
  # Confirmation thresholds
  hitl:
    always_confirm:
      - terminate
      - delete
      - drop
      - truncate
      - modify_iam
      - update_security_group

    confirm_if:
      - action: scale
        condition: "replicas > current * 2 or cost_delta > 100"
      - action: deploy
        condition: "environment == 'production'"
      - action: rollback
        condition: "always"

    skip_confirmation:
      - list
      - describe
      - get
      - search
      - query

  # Response grounding rules
  grounding:
    require_tool_citation: true
    max_claims_without_source: 0
    confidence_threshold: 0.85

    # Block speculative responses
    block_patterns:
      - "I think"
      - "probably"
      - "might be"
      - "I believe"
      - "it seems"
      - "I assume"

    # Require explicit uncertainty
    uncertainty_handling:
      low_confidence_action: "ask_user"
      missing_data_action: "explain_limitation"

  # Dialogue options
  dialogue:
    enable_clarification: true
    max_clarification_rounds: 3
    allow_partial_execution: true
    allow_scope_modification: true
```

### HITL Checkpoint States

| State | Trigger | User Options |
|-------|---------|--------------|
| `CONFIRM_REQUIRED` | Destructive action detected | confirm, cancel, modify |
| `CLARIFICATION_NEEDED` | Ambiguous intent | provide details, rephrase |
| `SCOPE_VERIFICATION` | Multiple resources affected | confirm all, select subset |
| `COST_APPROVAL` | Significant cost impact | approve, set budget limit |
| `ENVIRONMENT_CHECK` | Production environment | confirm with reason |
| `SECURITY_REVIEW` | IAM/security changes | approve with MFA |

---

## 🤖 Multi-Agent Orchestration

For open-ended or complex queries, the system spawns specialized agents that collaborate to find the best answer.

### When Multi-Agent is Triggered

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         QUERY COMPLEXITY ROUTER                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   User Query                                                                 │
│        │                                                                     │
│        ▼                                                                     │
│   ┌──────────────────────────────────────────────────────────┐              │
│   │              COMPLEXITY CLASSIFIER                        │              │
│   │                                                           │              │
│   │  Analyze query for:                                      │              │
│   │  • Specificity (narrow vs open-ended)                    │              │
│   │  • Domain count (single vs cross-domain)                 │              │
│   │  • Investigation depth required                          │              │
│   │  • Ambiguity level                                       │              │
│   └───────────────────────┬──────────────────────────────────┘              │
│                           │                                                  │
│           ┌───────────────┼───────────────┐                                 │
│           │               │               │                                  │
│           ▼               ▼               ▼                                  │
│   ┌───────────────┐ ┌───────────────┐ ┌───────────────┐                     │
│   │    SIMPLE     │ │   MODERATE    │ │    COMPLEX    │                     │
│   │               │ │               │ │               │                     │
│   │ Single tool   │ │ Multi-tool    │ │ Multi-agent   │                     │
│   │ Single domain │ │ Single domain │ │ Cross-domain  │                     │
│   │ Clear intent  │ │ Clear intent  │ │ Open-ended    │                     │
│   │               │ │               │ │               │                     │
│   │ → 1 Agent     │ │ → 1 Agent     │ │ → N Agents    │                     │
│   └───────────────┘ └───────────────┘ └───────────────┘                     │
│                                                                              │
│   Examples:                                                                  │
│   SIMPLE: "List EC2 instances"                                              │
│   MODERATE: "Deploy and scale auth-service"                                 │
│   COMPLEX: "Why is the system slow?" / "Optimize our infrastructure"       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Specialized Agent Types

| Agent | Specialization | Tools | Role |
|-------|---------------|-------|------|
| `ResearchAgent` | Data gathering | search_logs, get_metrics, query_traces | Collect facts before action |
| `InfraAgent` | AWS/Cloud operations | ec2_*, rds_*, cloudwatch_* | Infrastructure changes |
| `K8sAgent` | Kubernetes operations | k8s_*, deployment tools | Container orchestration |
| `SecurityAgent` | Threat analysis | query_threats, search_logs | Security investigation |
| `CostAgent` | Cost optimization | get_metrics, billing APIs | Financial analysis |
| `ValidatorAgent` | Verification | All read-only tools | Validate other agents' work |

### Multi-Agent Collaboration Example

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ USER: "Why is everything slow today? Can you investigate and fix it?"       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  ORCHESTRATOR: Query is open-ended + cross-domain → Multi-Agent Mode   │ │
│  │                                                                         │ │
│  │  Spawning specialized agents in parallel:                              │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  PHASE 1: PARALLEL INVESTIGATION                                            │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │  INFRA AGENT     │  │  K8S AGENT       │  │  SECURITY AGENT  │          │
│  │                  │  │                  │  │                  │          │
│  │  Checking:       │  │  Checking:       │  │  Checking:       │          │
│  │  • EC2 CPU/mem   │  │  • Pod status    │  │  • Attack logs   │          │
│  │  • RDS perf      │  │  • HPA scaling   │  │  • Threat alerts │          │
│  │  • Network I/O   │  │  • Resource use  │  │  • Auth failures │          │
│  │                  │  │                  │  │                  │          │
│  │  Tools:          │  │  Tools:          │  │  Tools:          │          │
│  │  ec2_list        │  │  k8s_list_agents │  │  query_threats   │          │
│  │  cloudwatch_get  │  │  get_metrics     │  │  search_logs     │          │
│  │  rds_describe    │  │  query_traces    │  │                  │          │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘          │
│           │                     │                     │                     │
│           └──────────┬──────────┴──────────┬──────────┘                     │
│                      │                     │                                │
│                      ▼                     ▼                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  FINDINGS AGGREGATION                                                │   │
│  │                                                                       │   │
│  │  InfraAgent: "RDS prod-postgres-01 at 94% CPU, 847 connections"     │   │
│  │  K8sAgent: "api-gateway pods in CrashLoopBackOff, HPA at max"       │   │
│  │  SecurityAgent: "No attacks detected, normal traffic patterns"      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                      │                                                      │
│                      ▼                                                      │
│  PHASE 2: ROOT CAUSE ANALYSIS                                               │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  RESEARCH AGENT (Deep Dive)                                          │   │
│  │                                                                       │   │
│  │  Correlating findings:                                               │   │
│  │  1. RDS high CPU started at 10:30 AM                                │   │
│  │  2. api-gateway crashes started at 10:32 AM                         │   │
│  │  3. Slow queries in logs: "SELECT * FROM orders WHERE status=..."   │   │
│  │  4. Missing index detected on orders.status                         │   │
│  │                                                                       │   │
│  │  🔍 ROOT CAUSE: Missing database index causing slow queries,         │   │
│  │     which caused connection pool exhaustion, which caused            │   │
│  │     api-gateway to crash waiting for DB connections.                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                      │                                                      │
│                      ▼                                                      │
│  PHASE 3: SOLUTION PROPOSAL (with HITL)                                     │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  🤖 I've identified the issue through multi-agent investigation:     │   │
│  │                                                                       │   │
│  │  **Root Cause Chain:**                                               │   │
│  │  Missing index → Slow queries → DB overload → API crashes           │   │
│  │                                                                       │   │
│  │  **Recommended Fix (3 steps):**                                      │   │
│  │                                                                       │   │
│  │  ┌─────────────────────────────────────────────────────────────┐    │   │
│  │  │ Step 1: [IMMEDIATE] Kill idle DB connections                │    │   │
│  │  │ Step 2: [IMMEDIATE] Scale RDS to db.r5.2xlarge             │    │   │
│  │  │ Step 3: [SCHEDULED] Add index on orders.status (2 AM)      │    │   │
│  │  └─────────────────────────────────────────────────────────────┘    │   │
│  │                                                                       │   │
│  │  **Confidence:** 94% (based on 3 agents, 8 tools, 12 data points)   │   │
│  │                                                                       │   │
│  │  Would you like me to proceed? (confirm/modify/ask questions)       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                      │                                                      │
│                      ▼                                                      │
│  USER: "Yes, but skip the RDS scale-up for now, just fix connections"      │
│                      │                                                      │
│                      ▼                                                      │
│  PHASE 4: EXECUTION + VALIDATION                                            │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                              │
│  ┌──────────────────┐              ┌──────────────────┐                    │
│  │  INFRA AGENT     │              │  VALIDATOR AGENT │                    │
│  │  (Executor)      │              │  (Verifier)      │                    │
│  │                  │              │                  │                    │
│  │  Executing:      │   ──────▶    │  Checking:       │                    │
│  │  • Kill 200 idle │              │  • CPU dropped?  │                    │
│  │    connections   │              │  • Pods healthy? │                    │
│  │  • Schedule idx  │              │  • Latency ok?   │                    │
│  └──────────────────┘              └──────────────────┘                    │
│                                              │                              │
│                                              ▼                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ✅ RESOLUTION VERIFIED                                              │   │
│  │                                                                       │   │
│  │  • DB CPU: 94% → 52% (still elevated, but stable)                   │   │
│  │  • Connections: 847 → 312                                           │   │
│  │  • API pods: 5/5 Running (no more crashes)                          │   │
│  │  • P95 latency: 4200ms → 450ms                                      │   │
│  │                                                                       │   │
│  │  ⚠️ Note: Full resolution requires the scheduled index creation.    │   │
│  │     I'll notify you when it completes at 2 AM.                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Agent Collaboration Patterns

```yaml
# config/multi_agent.yaml
multi_agent:
  enabled: true

  # When to spawn multiple agents
  triggers:
    - query_type: "open_ended"
      keywords: ["why", "what's wrong", "investigate", "optimize", "improve"]
    - query_type: "cross_domain"
      domains_mentioned: 2+
    - query_type: "root_cause"
      keywords: ["slow", "failing", "broken", "not working"]

  # Collaboration patterns
  patterns:
    parallel_investigation:
      description: "Multiple agents investigate different areas simultaneously"
      use_when: "Unknown root cause, need broad search"
      agents: [InfraAgent, K8sAgent, SecurityAgent, CostAgent]

    sequential_deep_dive:
      description: "One agent's findings trigger another"
      use_when: "Initial finding needs deeper investigation"
      flow: ResearchAgent → SpecialistAgent → ValidatorAgent

    consensus_validation:
      description: "Multiple agents must agree before action"
      use_when: "High-risk changes, production systems"
      requires: "2+ agents confirm the diagnosis"

    supervisor_worker:
      description: "Orchestrator delegates to specialists"
      use_when: "Complex multi-step remediation"
      supervisor: OrchestratorAgent
      workers: [InfraAgent, K8sAgent, SecurityAgent]

  # Agent communication
  communication:
    shared_context: true  # Agents can see each other's findings
    can_delegate: true    # Agents can spawn sub-agents
    max_depth: 3          # Maximum agent delegation depth
    timeout_per_agent: 60s

  # Human checkpoints in multi-agent flows
  hitl_checkpoints:
    - after: "investigation"
      show: "aggregated findings from all agents"
    - before: "execution"
      show: "proposed actions with confidence scores"
    - after: "execution"
      show: "validation results"
```

### Open-Ended Query Examples

| User Query | Agent Strategy | Agents Involved |
|------------|---------------|-----------------|
| "Why is prod slow?" | Parallel Investigation | Infra + K8s + Security + Research |
| "Optimize our AWS costs" | Sequential Deep Dive | Cost → Infra → Validator |
| "Is our system secure?" | Consensus Validation | Security + Infra + K8s |
| "Set up monitoring for the new service" | Supervisor-Worker | Orchestrator → K8s + Observability |
| "Something's wrong, help!" | Broad Parallel + HITL | All agents → User clarification |

### Dialogue with Multi-Agent

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ CONVERSATION: Open-ended investigation with human guidance                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ 👤 User: "Our customers are complaining about slowness"                     │
│                                                                              │
│ 🤖 Agent: I'll investigate this across multiple systems. Let me ask a few   │
│          clarifying questions to focus the search:                          │
│                                                                              │
│    1. Which application/service are customers using?                        │
│    2. When did the complaints start?                                        │
│    3. Is it all users or specific regions?                                  │
│                                                                              │
│ ─────────────────────────────────────────────────────────────────────────── │
│                                                                              │
│ 👤 User: "The checkout page, started about an hour ago, mostly US-East"     │
│                                                                              │
│ 🤖 Agent: Perfect. I'm spawning 3 specialized agents to investigate:        │
│                                                                              │
│    ┌───────────────────────────────────────────────────────────────────┐   │
│    │ 🔍 InfraAgent    → Checking us-east-1 infrastructure             │   │
│    │ 🔍 K8sAgent      → Checking checkout-service pods                 │   │
│    │ 🔍 SecurityAgent → Checking for unusual traffic patterns          │   │
│    │                                                                    │   │
│    │ ⏳ Investigation in progress... (typically 30-60 seconds)         │   │
│    └───────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│    [Live updates streaming...]                                              │
│    • InfraAgent: Found - RDS latency spike in us-east-1                    │
│    • K8sAgent: Found - checkout-service p99 latency at 8s                  │
│    • SecurityAgent: Clear - No attack patterns detected                    │
│                                                                              │
│ ─────────────────────────────────────────────────────────────────────────── │
│                                                                              │
│ 🤖 Agent: Investigation complete. Here's what I found:                      │
│                                                                              │
│    **Root Cause:** Database connection pool exhaustion                      │
│                                                                              │
│    **Evidence (from 3 agents):**                                            │
│    │ Source        │ Finding                    │ Confidence │             │
│    │───────────────│────────────────────────────│────────────│             │
│    │ InfraAgent    │ RDS: 950/1000 connections │ 98%        │             │
│    │ K8sAgent      │ Pods waiting on DB         │ 95%        │             │
│    │ SecurityAgent │ No external factors        │ 99%        │             │
│                                                                              │
│    **Would you like me to:**                                                │
│    A) Investigate deeper (why are connections exhausted?)                   │
│    B) Fix immediately (kill idle connections + scale)                       │
│    C) Show me more details first                                            │
│                                                                              │
│ ─────────────────────────────────────────────────────────────────────────── │
│                                                                              │
│ 👤 User: "A - why are connections exhausted?"                               │
│                                                                              │
│ 🤖 Agent: Spawning ResearchAgent for deep dive...                           │
│                                                                              │
│    [Searching logs for connection patterns...]                              │
│                                                                              │
│    **Found:** Connection leak in checkout-service v2.3.4                   │
│    • Deployed 2 hours ago                                                   │
│    • Connections opened but not released on timeout                         │
│    • 400 leaked connections from this version alone                         │
│                                                                              │
│    **Recommended actions:**                                                 │
│    1. Rollback checkout-service to v2.3.3 (fixes leak)                     │
│    2. Kill 400 leaked connections                                          │
│    3. File bug report for v2.3.4                                           │
│                                                                              │
│    Proceed with rollback? (This will take ~2 minutes)                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Kubernetes Deployment

```bash
# Apply manifests
kubectl apply -f k8s/

# Check status
kubectl -n nl-automation-hub get pods

# View logs
kubectl -n nl-automation-hub logs -f deployment/nl-hub-api
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_GATEWAY_URL` | Project 2 URL | `http://llm-security-gateway:8000` |
| `ANTHROPIC_API_KEY` | Claude API key | Required |
| `LANGCHAIN_API_KEY` | LangSmith key | Required for tracing |
| `MCP_AWS_SERVER_URL` | Project 1 URL | `http://mcp-aws-server:8080` |
| `K8S_AGENTOPS_URL` | Project 3 URL | `http://agentops-api:8000` |
| `ENABLE_VOICE` | Enable Whisper | `true` |

See [src/config/settings.py](src/config/settings.py) for all options.

## Project Structure

```
nl-automation-hub/
├── src/
│   ├── agent/graph.py      # LangGraph workflow
│   ├── api/main.py         # FastAPI app
│   ├── config/settings.py  # Configuration
│   ├── models/schemas.py   # Pydantic models
│   └── tools/registry.py   # Tool registry
├── frontend/               # React chat UI
├── k8s/                    # Kubernetes manifests
├── Dockerfile
├── docker-compose.yaml
└── requirements.txt
```

## Related Projects

| # | Project | Description |
|---|---------|-------------|
| 1 | [MCP AWS Server](../mcp-aws-server) | AWS infrastructure tools |
| 2 | [LLM Security Gateway](../llm-security-gateway) | LLM security & routing |
| 3 | [K8s AgentOps](../k8s-agentops-platform) | Kubernetes agent management |
| 4 | [CI/CD Framework](../enterprise-cicd-framework) | Pipeline management |
| 5 | [Logging & Threat](../centralized-logging-threat-analytics) | Log search & SIEM |
| 6 | [Observability](../multi-cloud-observability-fabric) | Metrics & traces |

## License

MIT License - See [LICENSE](LICENSE) for details.
