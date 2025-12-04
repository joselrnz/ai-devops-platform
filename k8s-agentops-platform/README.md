# Kubernetes AgentOps Platform

Production-grade Kubernetes platform for deploying and managing AI agents at scale with built-in observability, auto-scaling, and multi-tenancy.

## Overview

This platform provides a complete solution for running AI agents (LLMs) as containerized workloads in Kubernetes. It handles deployment, scaling, monitoring, and lifecycle management of agent instances with enterprise-grade reliability.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Ingress Controller                            │
│                    (NGINX + Cert-Manager)                            │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Kubernetes Cluster                              │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                  Agent Namespace (tenant-1)                     │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │ │
│  │  │ Agent Pod 1  │  │ Agent Pod 2  │  │ Agent Pod 3  │        │ │
│  │  │ - LLM Model  │  │ - LLM Model  │  │ - LLM Model  │        │ │
│  │  │ - MCP Server │  │ - MCP Server │  │ - MCP Server │        │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘        │ │
│  │                                                                  │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │         Horizontal Pod Autoscaler (HPA)                  │  │ │
│  │  │  Scales: 1-10 pods based on CPU/Memory/Custom metrics   │  │ │
│  │  └──────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                   Platform Components                           │ │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐              │ │
│  │  │ Prometheus │  │  Grafana   │  │   Loki     │              │ │
│  │  │ (Metrics)  │  │(Dashboard) │  │   (Logs)   │              │ │
│  │  └────────────┘  └────────────┘  └────────────┘              │ │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐              │ │
│  │  │   Jaeger   │  │   Vault    │  │  ArgoCD    │              │ │
│  │  │  (Traces)  │  │ (Secrets)  │  │  (GitOps)  │              │ │
│  │  └────────────┘  └────────────┘  └────────────┘              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                   Agent Controller (Go)                         │ │
│  │  - Lifecycle management                                         │ │
│  │  - Health checks & auto-recovery                                │ │
│  │  - Resource quota enforcement                                   │ │
│  │  - Multi-tenancy isolation                                      │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Features

### 🚀 Agent Deployment & Management
- **Helm Charts** - Declarative agent deployments with values overrides
- **Multi-tenancy** - Namespace isolation per tenant with RBAC
- **Custom Resource Definitions (CRDs)** - `AgentDeployment` CRD for simplified management
- **GitOps with ArgoCD** - Automated deployments from Git repositories

### 📊 Observability Stack
- **Prometheus** - Metrics collection (CPU, memory, request rate, latency)
- **Grafana** - Pre-built dashboards for agent performance
- **Loki** - Centralized log aggregation
- **Jaeger** - Distributed tracing for request flows
- **OpenTelemetry** - Instrumentation SDK for all agents

### 🔄 Auto-scaling & Resilience
- **Horizontal Pod Autoscaler (HPA)** - Scale based on CPU, memory, custom metrics
- **Vertical Pod Autoscaler (VPA)** - Right-size resource requests
- **Pod Disruption Budgets** - Ensure availability during updates
- **Readiness/Liveness Probes** - Automatic health checks and restarts

### 🔒 Security & Compliance
- **Network Policies** - Isolate agent traffic
- **Pod Security Policies** - Enforce security standards
- **Secrets Management** - HashiCorp Vault integration
- **RBAC** - Fine-grained access control
- **Image Scanning** - Trivy integration in CI/CD

### 💰 Cost Optimization
- **Resource Quotas** - Per-tenant limits
- **Cluster Autoscaler** - Scale nodes based on demand
- **Spot Instances** - Use spot nodes for dev/test
- **Resource Monitoring** - Track cost per tenant/agent

## Tech Stack

- **Orchestration**: Kubernetes 1.28+
- **Package Manager**: Helm 3.x
- **GitOps**: ArgoCD
- **Controller**: Go 1.21+ with Kubernetes Operator SDK
- **Observability**: Prometheus, Grafana, Loki, Jaeger
- **Secrets**: HashiCorp Vault
- **Ingress**: NGINX Ingress Controller
- **Cert Management**: cert-manager
- **Service Mesh**: Istio (optional for advanced routing)

## Project Structure

```
k8s-agentops-platform/
├── helm/
│   ├── agent-deployment/     # Helm chart for deploying agents
│   ├── platform/             # Platform components (Prometheus, etc.)
│   └── agent-controller/     # Custom controller chart
├── controller/
│   ├── cmd/                  # Controller entry point
│   ├── pkg/
│   │   ├── apis/             # CRD definitions
│   │   ├── controllers/      # Reconciliation logic
│   │   └── utils/            # Helpers
│   └── config/               # RBAC, CRDs
├── manifests/
│   ├── crds/                 # Custom Resource Definitions
│   ├── operators/            # Operator deployments
│   └── examples/             # Example agent deployments
├── monitoring/
│   ├── dashboards/           # Grafana dashboards
│   ├── alerts/               # Prometheus alert rules
│   └── queries/              # PromQL queries
├── argocd/
│   ├── applications/         # ArgoCD app manifests
│   └── app-of-apps/          # App-of-apps pattern
└── docs/                     # Documentation
```

## Quick Start

### Prerequisites

- Kubernetes cluster (1.28+)
- kubectl configured
- Helm 3.x installed
- ArgoCD (optional for GitOps)

### 1. Install Platform Components

```bash
# Add Helm repositories
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add jetstack https://charts.jetstack.io
helm repo update

# Install cert-manager (for TLS)
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true

# Install Prometheus + Grafana
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  -f helm/platform/values-prometheus.yaml

# Install Loki for logs
helm install loki grafana/loki-stack \
  --namespace monitoring \
  -f helm/platform/values-loki.yaml
```

### 2. Deploy Agent Controller

```bash
# Install CRDs
kubectl apply -f manifests/crds/

# Deploy controller
helm install agent-controller helm/agent-controller \
  --namespace agentops-system \
  --create-namespace
```

### 3. Deploy Your First Agent

```bash
# Create tenant namespace
kubectl create namespace tenant-demo

# Deploy agent using Helm
helm install my-agent helm/agent-deployment \
  --namespace tenant-demo \
  --set image.repository=ghcr.io/myorg/llm-agent \
  --set image.tag=v1.0.0 \
  --set resources.requests.memory=2Gi \
  --set resources.requests.cpu=1000m \
  --set autoscaling.enabled=true \
  --set autoscaling.minReplicas=2 \
  --set autoscaling.maxReplicas=10
```

### 4. Access Grafana Dashboard

```bash
# Get Grafana password
kubectl get secret -n monitoring kube-prometheus-stack-grafana \
  -o jsonpath="{.data.admin-password}" | base64 --decode

# Port-forward Grafana
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80

# Open http://localhost:3000
# Username: admin, Password: <from above>
```

## Agent Deployment Configurations

### Basic Agent Deployment

```yaml
# values.yaml
replicaCount: 2

image:
  repository: ghcr.io/myorg/llm-agent
  tag: "v1.0.0"
  pullPolicy: IfNotPresent

resources:
  requests:
    memory: "2Gi"
    cpu: "1000m"
  limits:
    memory: "4Gi"
    cpu: "2000m"

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

serviceMonitor:
  enabled: true
  interval: 30s
```

### High-Performance Agent

```yaml
# values-gpu.yaml
resources:
  requests:
    nvidia.com/gpu: 1
    memory: "16Gi"
    cpu: "4000m"
  limits:
    nvidia.com/gpu: 1
    memory: "32Gi"
    cpu: "8000m"

nodeSelector:
  node.kubernetes.io/instance-type: g4dn.xlarge

tolerations:
  - key: nvidia.com/gpu
    operator: Exists
    effect: NoSchedule
```

## Custom Resource Definition (CRD)

Define agents declaratively with the `AgentDeployment` CRD:

```yaml
apiVersion: agentops.io/v1alpha1
kind: AgentDeployment
metadata:
  name: claude-assistant
  namespace: tenant-demo
spec:
  model: claude-3-sonnet
  replicas: 3
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 10
    metrics:
      - type: Resource
        resource:
          name: cpu
          target:
            type: Utilization
            averageUtilization: 70
  resources:
    requests:
      memory: "2Gi"
      cpu: "1000m"
  securityContext:
    runAsNonRoot: true
    readOnlyRootFilesystem: true
  secrets:
    - name: anthropic-api-key
      key: ANTHROPIC_API_KEY
  monitoring:
    enabled: true
    scrapeInterval: 30s
```

## Monitoring & Alerts

### Pre-configured Dashboards

1. **Agent Overview** - Request rate, latency, error rate
2. **Resource Usage** - CPU, memory, GPU utilization
3. **Cost Dashboard** - Per-tenant resource costs
4. **SLO Dashboard** - Availability, latency percentiles

### Alert Rules

- High error rate (>5% for 5 minutes)
- High latency (p95 >2s for 5 minutes)
- Memory pressure (>90% for 10 minutes)
- Pod crash loops (>3 restarts in 10 minutes)
- Low availability (<99% over 1 hour)

## Cost Estimates

### AWS EKS (3-node cluster)

| Component | Instance Type | Monthly Cost |
|-----------|---------------|--------------|
| Control Plane | EKS managed | $73 |
| Worker Node 1 | t3.xlarge | $121 |
| Worker Node 2 | t3.xlarge | $121 |
| Worker Node 3 | t3.xlarge | $121 |
| EBS Storage (300GB) | gp3 | $24 |
| **Total** | | **~$460/month** |

### Cost Optimization Tips

- Use spot instances for non-production (50-70% savings)
- Enable cluster autoscaler to scale down during low usage
- Use VPA to right-size resource requests
- Archive old logs to S3 (Loki retention: 7 days)

## Documentation

- [Architecture Deep Dive](docs/architecture.md)
- [Agent Controller Design](docs/controller.md)
- [Multi-Tenancy Guide](docs/multi-tenancy.md)
- [Monitoring & Observability](docs/monitoring.md)
- [Security Best Practices](docs/security.md)
- [Troubleshooting Guide](docs/troubleshooting.md)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

**Jose** | DevOps & Cloud Engineer
