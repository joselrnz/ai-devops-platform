# LLM Security Gateway

Enterprise-grade security gateway for AI/LLM applications with DLP, PII redaction, RBAC, rate limiting, and model routing.

## Overview

The LLM Security Gateway sits between your users and AI models (Claude, GPT-4, local models) to enforce enterprise security policies. It ensures no sensitive data leaves your organization while providing centralized access control, cost management, and audit trails.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          USER/CLIENT                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   API GATEWAY (HTTPS/JWT)                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LLM SECURITY GATEWAY                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  1. AUTHENTICATION & AUTHORIZATION                       │   │
│  │     └─ JWT validation, RBAC (OPA/Rego)                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  2. RATE LIMITING & QUOTA                                │   │
│  │     └─ Redis-based rate limiter, token tracking          │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  3. DLP & PII DETECTION                                  │   │
│  │     └─ Microsoft Presidio (SSN, credit cards, etc.)      │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  4. MODEL ROUTING & POLICY ENGINE                        │   │
│  │     ┌────────────────────────────────────────────────┐   │   │
│  │     │  Load Balancing: Round-Robin │ Weighted │ Least│   │   │
│  │     │  Fallback Chain: Claude → GPT-4 → Ollama       │   │   │
│  │     │  Circuit Breaker: Auto-disable failing models  │   │   │
│  │     │  Health Checks: Continuous availability probe  │   │   │
│  │     │  Capability Match: Route by task type/context  │   │   │
│  │     └────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  5. AUDIT LOGGING                                        │   │
│  │     └─ Log all requests/responses to PostgreSQL          │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
         ▼                  ▼                  ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  Claude API     │ │  GPT-4 API      │ │  Local Models   │
│  (Anthropic)    │ │  (OpenAI)       │ │  (Ollama)       │
│  ┌───────────┐  │ │  ┌───────────┐  │ │  ┌───────────┐  │
│  │ weight:50 │  │ │  │ weight:30 │  │ │  │ weight:20 │  │
│  │ health: ✓ │  │ │  │ health: ✓ │  │ │  │ health: ✓ │  │
│  │ latency:  │  │ │  │ latency:  │  │ │  │ latency:  │  │
│  │   ~200ms  │  │ │  │   ~350ms  │  │ │  │   ~100ms  │  │
│  └───────────┘  │ │  └───────────┘  │ │  └───────────┘  │
└─────────────────┘ └─────────────────┘ └─────────────────┘
         │                  │                  │
         └──────────────────┼──────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MCP CONTROL PLANES                           │
│  └─ [1] AWS │ [3] K8s AgentOps │ [4] CI/CD Framework           │
└─────────────────────────────────────────────────────────────────┘
```

## Features

### 🔒 Data Loss Prevention (DLP)
- **Pattern Matching**: Credit cards, SSN, API keys, passwords
- **Custom Rules**: Define organization-specific sensitive data patterns
- **Action Modes**: Block, redact, or alert on sensitive data
- **Regex Engine**: High-performance pattern detection

### 🛡️ PII Detection & Redaction
- **Microsoft Presidio Integration**: Industry-standard PII detection
- **Entity Types**: Names, emails, phone numbers, addresses, etc.
- **Anonymization**: Replace PII with synthetic data or tokens
- **Reversible Redaction**: Optional de-anonymization for authorized users

### 🔐 Role-Based Access Control (RBAC)
- **OPA (Open Policy Agent)**: Policy-as-code with Rego language
- **Fine-Grained Permissions**: Control access per user, team, or tenant
- **Model Access**: Restrict which models users can access
- **Feature Flags**: Enable/disable features per user group
- **Audit Decisions**: Log all authorization decisions

### ⏱️ Rate Limiting & Quotas
- **Redis-Backed**: High-performance distributed rate limiting
- **Multiple Strategies**: Per-user, per-API-key, per-IP, per-tenant
- **Token Budgets**: Track token usage across models
- **Cost Attribution**: Associate costs with users/teams
- **Graceful Degradation**: Queue requests when near limits

### 🎯 Multi-Model Routing & Policy Engine

The gateway supports sophisticated routing policy configuration enabling enterprise-grade model orchestration:

#### Load Balancing Strategies
- **Round Robin**: Distribute requests evenly across model pool
- **Weighted**: Route based on model capacity/cost weights
- **Least Latency**: Auto-select fastest responding model
- **Least Connections**: Route to model with fewest active requests
- **Cost-Optimized**: Prefer cheaper models meeting quality threshold

#### Fallback & Resilience
- **Fallback Chains**: Define ordered backup models (Claude → GPT-4 → Ollama)
- **Circuit Breaker**: Auto-disable failing models, periodic recovery checks
- **Health Checks**: Continuous model availability monitoring
- **Timeout Handling**: Per-model timeout with automatic retry on fallback
- **Graceful Degradation**: Fall back to cached responses when all models fail

#### Advanced Routing Policies
- **Capability Matching**: Route code tasks to Claude, creative to GPT-4
- **Context-Aware**: Route based on prompt length, complexity, domain
- **A/B Testing**: Split traffic for model evaluation experiments
- **Sticky Sessions**: Keep conversation threads on same model
- **Geographic Routing**: Route to nearest model endpoint for latency

### 🛑 Human-in-the-Loop (HITL) Guardrails

The gateway enforces confirmation workflows for high-risk operations, preventing autonomous actions without explicit user approval:

#### Confirmation Required Actions
- **Destructive Operations**: Delete, terminate, drop, truncate
- **Cost-Impacting**: Scale up, provision new resources, enable services
- **Security-Sensitive**: Modify IAM, change firewall rules, update secrets
- **Data Operations**: Bulk updates, migrations, ETL retries
- **Production Changes**: Any modification to prod environment

#### Anti-Hallucination Safeguards
- **Tool Output Grounding**: Responses must cite actual tool results
- **Fact Verification**: Cross-reference claims against retrieved data
- **Confidence Thresholds**: Flag low-confidence responses for review
- **Source Attribution**: Every claim linked to specific tool output
- **Contradiction Detection**: Alert when response contradicts tool data

#### Interactive Dialogue Flow
```
User: "Delete all stopped EC2 instances"
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  HITL CHECKPOINT TRIGGERED                                   │
│                                                              │
│  🛑 This action requires confirmation.                      │
│                                                              │
│  Action: DELETE EC2 instances                               │
│  Scope: 7 stopped instances found                           │
│  Environment: production (⚠️ HIGH RISK)                     │
│                                                              │
│  Instances to delete:                                        │
│  • i-0a1b2c3d (api-server-old) - stopped 14 days           │
│  • i-1b2c3d4e (test-server) - stopped 3 days               │
│  • ... [5 more]                                              │
│                                                              │
│  Estimated cost savings: $234/month                         │
│                                                              │
│  Type 'confirm delete 7 instances' to proceed               │
│  Type 'cancel' to abort                                      │
│  Type 'show details' for full list                          │
└─────────────────────────────────────────────────────────────┘
                    │
                    ▼
User: "confirm delete 7 instances"
                    │
                    ▼
        [Action executed with full audit trail]
```

#### Guardrail Configuration
```yaml
# config/guardrails.yaml
guardrails:
  # Human confirmation requirements
  hitl:
    enabled: true
    confirmation_required:
      - pattern: "delete|remove|terminate|destroy"
        environments: ["production", "staging"]
        cooldown_seconds: 5  # Prevent accidental double-confirm

      - pattern: "scale|resize|modify"
        min_cost_impact_usd: 50

      - pattern: "iam|security-group|secret"
        always: true
        require_mfa: true

  # Anti-hallucination controls
  grounding:
    enabled: true
    require_tool_citation: true
    max_unsupported_claims: 0
    confidence_threshold: 0.85

  # Response validation
  validation:
    check_tool_output_match: true
    detect_contradictions: true
    flag_speculative_language: true
    blocked_phrases:
      - "I think"
      - "probably"
      - "might be"
      - "I assume"
```

### 📊 Comprehensive Audit Logging
- **Request/Response Logging**: Full audit trail in PostgreSQL
- **Redacted Logs**: Sensitive data removed before storage
- **Metrics Tracking**: Token usage, latency, error rates
- **Cost Tracking**: Per-user, per-team, per-model costs
- **Compliance Reports**: SOC2, GDPR, HIPAA audit trails

## Tech Stack

- **Framework**: FastAPI (async Python)
- **DLP/PII**: Microsoft Presidio, custom regex engine
- **RBAC**: Open Policy Agent (OPA) with Rego
- **Rate Limiting**: Redis with sliding window algorithm
- **Database**: PostgreSQL (audit logs, user metadata)
- **Caching**: Redis (policy cache, rate limits)
- **Auth**: JWT tokens, OAuth2, API keys
- **Deployment**: Docker, Kubernetes

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Redis
- PostgreSQL
- (Optional) OPA server

### Installation

```bash
# Clone repository
cd llm-security-gateway

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment file
cp .env.example .env
# Edit .env with your configuration

# Start dependencies (Redis, PostgreSQL, OPA)
docker-compose up -d

# Run migrations
alembic upgrade head

# Start gateway
python -m src.gateway.main
```

### Docker Deployment

```bash
# Build image
docker build -t llm-security-gateway .

# Run with Docker Compose
docker-compose up
```

## Configuration

### Environment Variables

```bash
# API Settings
API_HOST=0.0.0.0
API_PORT=8080

# Security
JWT_SECRET=your_jwt_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600

# Redis (Rate Limiting)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# PostgreSQL (Audit Logs)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=llm_gateway
DB_USER=gateway_user
DB_PASSWORD=secure_password

# OPA (RBAC)
OPA_URL=http://localhost:8181
OPA_POLICY_PATH=/v1/data/llm/authz/allow

# DLP Settings
DLP_MODE=redact  # block, redact, alert
DLP_ENABLE_PII=true
DLP_ENABLE_SECRETS=true

# Model Endpoints
CLAUDE_API_KEY=your_claude_key
OPENAI_API_KEY=your_openai_key
LOCAL_MODEL_URL=http://localhost:11434  # Ollama

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_USER=100  # requests per minute
RATE_LIMIT_PER_TENANT=1000
```

### OPA Policies

Create RBAC policies in `policies/rego/authz.rego`:

```rego
package llm.authz

# Allow admin users full access
allow {
    input.user.role == "admin"
}

# Allow users to access specific models
allow {
    input.user.role == "user"
    model_allowed[input.request.model]
}

model_allowed["claude-3-sonnet"] {
    input.user.tier == "premium"
}

model_allowed["gpt-4"] {
    input.user.tier == "enterprise"
}
```

## Usage

### REST API

```bash
# Health check
curl http://localhost:8080/health

# Send request to Claude (with JWT)
curl -X POST http://localhost:8080/api/v1/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-sonnet",
    "messages": [
      {"role": "user", "content": "Hello, what is my SSN 123-45-6789?"}
    ]
  }'

# Response (SSN redacted):
{
  "model": "claude-3-sonnet",
  "response": "Hello! I cannot help with SSN information as it contains sensitive PII: <SSN_REDACTED>",
  "metadata": {
    "tokens_used": 45,
    "cost": 0.002,
    "pii_detected": true,
    "pii_entities": ["SSN"]
  }
}
```

### Python SDK

```python
from llm_gateway_sdk import Gateway

# Initialize gateway client
gateway = Gateway(
    api_url="http://localhost:8080",
    api_key="your_api_key"
)

# Send chat request
response = gateway.chat(
    model="claude-3-sonnet",
    messages=[
        {"role": "user", "content": "Analyze this data"}
    ]
)

print(response.content)
print(f"Tokens: {response.tokens_used}")
print(f"Cost: ${response.cost}")
```

## Security Features

### DLP Rules

```yaml
# config/dlp_rules.yaml
rules:
  - name: credit_card
    pattern: '\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
    action: redact
    severity: high

  - name: api_key
    pattern: 'sk-[a-zA-Z0-9]{32,}'
    action: block
    severity: critical

  - name: internal_ip
    pattern: '\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
    action: alert
    severity: medium
```

### Rate Limit Tiers

```yaml
# config/rate_limits.yaml
tiers:
  free:
    requests_per_minute: 10
    tokens_per_month: 100000
    models: ["gpt-3.5-turbo"]

  premium:
    requests_per_minute: 100
    tokens_per_month: 1000000
    models: ["claude-3-sonnet", "gpt-4"]

  enterprise:
    requests_per_minute: 1000
    tokens_per_month: unlimited
    models: ["*"]
```

### Routing Policy Configuration

```yaml
# config/routing_policies.yaml
routing:
  # Default load balancing strategy
  default_strategy: weighted

  # Model pool with health checks
  models:
    claude-sonnet:
      endpoint: https://api.anthropic.com/v1
      weight: 50
      timeout_ms: 30000
      max_concurrent: 100
      health_check:
        enabled: true
        interval_seconds: 30
        failure_threshold: 3

    gpt-4:
      endpoint: https://api.openai.com/v1
      weight: 30
      timeout_ms: 45000
      max_concurrent: 80
      health_check:
        enabled: true
        interval_seconds: 30
        failure_threshold: 3

    ollama-local:
      endpoint: http://ollama:11434
      weight: 20
      timeout_ms: 60000
      max_concurrent: 10
      health_check:
        enabled: true
        interval_seconds: 10
        failure_threshold: 2

  # Fallback chains (ordered priority)
  fallback_chains:
    production:
      - claude-sonnet
      - gpt-4
      - ollama-local

    cost_optimized:
      - ollama-local
      - gpt-4
      - claude-sonnet

    code_tasks:
      - claude-sonnet
      - gpt-4

  # Circuit breaker settings
  circuit_breaker:
    enabled: true
    failure_rate_threshold: 50      # % failures to trip
    wait_duration_seconds: 60       # Time before retry
    permitted_calls_in_half_open: 3 # Test calls after wait

  # Capability-based routing
  capability_routing:
    enabled: true
    rules:
      - match:
          prompt_contains: ["code", "function", "debug", "refactor"]
        route_to: claude-sonnet

      - match:
          prompt_contains: ["creative", "story", "marketing"]
        route_to: gpt-4

      - match:
          token_estimate_gt: 4000
        route_to: claude-sonnet  # Larger context window

      - match:
          user_tier: free
        route_to: ollama-local

  # A/B testing experiments
  experiments:
    - name: claude-vs-gpt4-coding
      enabled: true
      traffic_split:
        claude-sonnet: 70
        gpt-4: 30
      match:
        prompt_contains: ["implement", "write code"]
```

## Architecture Decisions

### Why Presidio for PII?
- Industry-standard, battle-tested
- Supports 50+ PII entity types out-of-the-box
- Extensible with custom recognizers
- Microsoft-backed, actively maintained

### Why OPA for RBAC?
- Policy-as-code (version controlled)
- Rego is expressive and auditable
- Cloud-native, CNCF graduated project
- Decouples policy from application logic

### Why Redis for Rate Limiting?
- Sub-millisecond latency
- Atomic operations (INCR, EXPIRE)
- Sliding window algorithm support
- Distributed (multi-instance support)

## Deployment

### Kubernetes

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-security-gateway
spec:
  replicas: 3
  selector:
    matchLabels:
      app: llm-gateway
  template:
    spec:
      containers:
      - name: gateway
        image: llm-security-gateway:latest
        ports:
        - containerPort: 8080
        env:
        - name: REDIS_HOST
          value: redis-service
        - name: DB_HOST
          value: postgres-service
```

## Monitoring

- **Prometheus Metrics**: Request rate, latency, error rate, PII detections
- **Grafana Dashboards**: Real-time monitoring
- **CloudWatch**: AWS integration for logs and metrics
- **Alerts**: PagerDuty/Slack notifications

## Cost Tracking

```sql
-- Query cost by user
SELECT
    user_id,
    model,
    SUM(tokens_used) as total_tokens,
    SUM(cost_usd) as total_cost
FROM audit_logs
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY user_id, model
ORDER BY total_cost DESC;
```

## License

MIT License - See LICENSE file for details

## Contributing

See CONTRIBUTING.md

## Support

- GitHub Issues: [Report bugs](https://github.com/yourusername/llm-security-gateway/issues)
- Documentation: [Full docs](https://docs.example.com)
- Email: security@example.com

---

**Part of the AI-Augmented DevOps Platform Portfolio**
**Project 2 of 7** | [← Project 1](../mcp-aws-server) | [Project 3 →](../k8s-agentops-platform)
