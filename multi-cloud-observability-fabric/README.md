# Multi-Cloud Observability Fabric

Unified observability platform for monitoring AI/LLM infrastructure across multiple clouds with metrics, logs, and distributed tracing.

## Overview

This platform provides complete observability for cloud-native AI applications running on AWS, Azure, GCP, and on-premises infrastructure. It implements the three pillars of observability: metrics (Prometheus), logs (Loki), and traces (Tempo), all visualized through Grafana.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Data Sources                                    │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐          │
│  │   AWS    │  Azure   │   GCP    │   K8s    │ On-Prem  │          │
│  │ Services │ Services │ Services │ Clusters │  Servers │          │
│  └────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬─────┘          │
└───────┼──────────┼──────────┼──────────┼──────────┼────────────────┘
        │          │          │          │          │
        │ Metrics  │ Logs     │ Traces   │          │
        │          │          │          │          │
        └──────────┴──────────┴──────────┴──────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Collection Layer                                  │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                  Prometheus Exporters                           │ │
│  │  - Node Exporter (system metrics)                              │ │
│  │  - Kube State Metrics (K8s metrics)                            │ │
│  │  - CloudWatch Exporter (AWS)                                   │ │
│  │  - Azure Monitor Exporter                                      │ │
│  │  - Stackdriver Exporter (GCP)                                  │ │
│  │  - Custom application metrics                                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                  OpenTelemetry Collector                        │ │
│  │  - Metrics pipeline                                             │ │
│  │  - Logs pipeline                                                │ │
│  │  - Traces pipeline                                              │ │
│  │  - Multi-cloud service discovery                               │ │
│  └────────────────────────────────────────────────────────────────┘ │
└───────────────────────────┼─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Storage & Query Layer                             │
│  ┌───────────────────┬──────────────────┬────────────────────────┐ │
│  │   Prometheus      │      Loki        │       Tempo            │ │
│  │   (Metrics)       │      (Logs)      │      (Traces)          │ │
│  │  ┌─────────────┐  │  ┌────────────┐  │  ┌──────────────────┐ │ │
│  │  │ TSDB        │  │  │ Chunks     │  │  │ Trace Blocks     │ │ │
│  │  │ - 15d local │  │  │ - 7d local │  │  │ - 7d local       │ │ │
│  │  │ - 90d remote│  │  │ - S3 backup│  │  │ - S3 backup      │ │ │
│  │  └─────────────┘  │  └────────────┘  │  └──────────────────┘ │ │
│  │  PromQL queries   │  LogQL queries   │  TraceQL queries      │ │
│  └───────────────────┴──────────────────┴────────────────────────┘ │
└───────────────────────────┼─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Visualization Layer                               │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                      Grafana                                    │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │  Unified Dashboards                                      │  │ │
│  │  │  - Metrics + Logs + Traces correlation                   │  │ │
│  │  │  - Multi-cloud infrastructure view                       │  │ │
│  │  │  - Application performance (RED/USE)                     │  │ │
│  │  │  - Cost analysis dashboard                               │  │ │
│  │  │  - SLO/SLA tracking                                      │  │ │
│  │  └──────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────┘ │
└───────────────────────────┼─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Alerting & Incident Response                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                  Alertmanager                                   │ │
│  │  - Alert routing & grouping                                     │ │
│  │  - Deduplication & silencing                                    │ │
│  │  - Multi-channel notifications (Slack, PagerDuty, Email)       │ │
│  │  - Alert escalation policies                                    │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Features

### 📊 Metrics Collection & Storage
- **Prometheus** - Time-series database with PromQL
- **Long-term storage** - Thanos/Cortex for 90-day retention
- **Multi-cloud exporters** - AWS CloudWatch, Azure Monitor, GCP Stackdriver
- **Custom metrics** - Application instrumentation with Prometheus client libraries
- **Service discovery** - Automatic target discovery across clouds

### 📝 Log Aggregation
- **Loki** - Horizontally scalable log aggregation
- **LogQL** - Powerful query language for log exploration
- **Label-based indexing** - Efficient storage and querying
- **Multi-tenancy** - Isolated log streams per tenant
- **S3 storage** - Cost-effective long-term retention

### 🔍 Distributed Tracing
- **Tempo** - High-scale distributed tracing backend
- **OpenTelemetry** - Vendor-neutral instrumentation
- **TraceQL** - Query language for trace exploration
- **Service graph** - Visualize service dependencies
- **Trace to logs correlation** - Jump from traces to related logs

### 📈 Visualization & Dashboards
- **Grafana** - Unified visualization platform
- **Pre-built dashboards** - Infrastructure, applications, business metrics
- **Explore** - Ad-hoc querying across metrics, logs, traces
- **Alerting** - Unified alert management
- **Variables & templating** - Dynamic, reusable dashboards

### 🔔 Alerting & SLOs
- **Prometheus Alertmanager** - Alert routing and grouping
- **Recording rules** - Pre-computed aggregations
- **SLO tracking** - Error budget monitoring
- **Alert templates** - Customizable notifications
- **Runbooks** - Linked remediation guides

### 🌍 Multi-Cloud Support
- **AWS** - EC2, ECS, EKS, Lambda, RDS, CloudWatch
- **Azure** - VMs, AKS, App Service, Azure Monitor
- **GCP** - GCE, GKE, Cloud Run, Stackdriver
- **Kubernetes** - Any K8s cluster (EKS, AKS, GKE, on-prem)
- **On-premises** - Physical servers, VMs

## Tech Stack

- **Metrics**: Prometheus 2.48+, Thanos 0.33+
- **Logs**: Loki 2.9+, Promtail 2.9+
- **Traces**: Tempo 2.3+, OpenTelemetry Collector 0.91+
- **Visualization**: Grafana 10.2+
- **Alerting**: Alertmanager 0.26+
- **Orchestration**: Kubernetes 1.28+, Helm 3.x
- **Storage**: S3, Azure Blob, GCS

## Project Structure

```
multi-cloud-observability-fabric/
├── helm/
│   ├── kube-prometheus-stack/    # Prometheus + Grafana + Alertmanager
│   ├── loki/                      # Log aggregation
│   ├── tempo/                     # Distributed tracing
│   ├── opentelemetry-collector/  # OTEL collector
│   └── thanos/                    # Long-term metrics storage
├── dashboards/
│   ├── infrastructure/            # Cloud infrastructure dashboards
│   ├── applications/              # Application performance
│   ├── business/                  # Business metrics
│   └── slo/                       # SLO tracking
├── alerts/
│   ├── infrastructure.yaml        # Infrastructure alerts
│   ├── applications.yaml          # Application alerts
│   └── slo.yaml                   # SLO/SLA alerts
├── exporters/
│   ├── cloudwatch/                # AWS CloudWatch exporter
│   ├── azure-monitor/             # Azure Monitor exporter
│   └── stackdriver/               # GCP Stackdriver exporter
├── grafana/
│   ├── datasources/               # Data source configs
│   ├── dashboards/                # Dashboard provisioning
│   └── plugins/                   # Custom plugins
├── otel-collector/
│   ├── configs/                   # OTEL collector configs
│   └── processors/                # Custom processors
└── docs/                          # Documentation
```

## Quick Start

### 1. Deploy Prometheus Stack

```bash
# Add Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install kube-prometheus-stack
helm install kube-prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  -f helm/kube-prometheus-stack/values.yaml \
  --wait
```

### 2. Deploy Loki

```bash
# Add Grafana Helm repository
helm repo add grafana https://grafana.github.io/helm-charts

# Install Loki
helm install loki grafana/loki-distributed \
  --namespace monitoring \
  -f helm/loki/values.yaml \
  --wait

# Install Promtail (log shipper)
helm install promtail grafana/promtail \
  --namespace monitoring \
  -f helm/loki/promtail-values.yaml
```

### 3. Deploy Tempo

```bash
# Install Tempo
helm install tempo grafana/tempo-distributed \
  --namespace monitoring \
  -f helm/tempo/values.yaml \
  --wait
```

### 4. Deploy OpenTelemetry Collector

```bash
# Add OpenTelemetry Helm repository
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts

# Install OTEL Collector
helm install otel-collector open-telemetry/opentelemetry-collector \
  --namespace monitoring \
  -f helm/opentelemetry-collector/values.yaml
```

### 5. Access Grafana

```bash
# Get Grafana admin password
kubectl get secret -n monitoring kube-prometheus-grafana \
  -o jsonpath="{.data.admin-password}" | base64 --decode

# Port-forward Grafana
kubectl port-forward -n monitoring svc/kube-prometheus-grafana 3000:80

# Open http://localhost:3000
# Username: admin
# Password: <from above>
```

## Pre-configured Dashboards

### Infrastructure Dashboards
1. **Multi-Cloud Overview** - All clouds in one view
2. **Kubernetes Cluster** - Node, pod, container metrics
3. **AWS Infrastructure** - EC2, RDS, ELB, Lambda
4. **Azure Infrastructure** - VMs, AKS, App Services
5. **GCP Infrastructure** - GCE, GKE, Cloud Functions

### Application Dashboards
6. **RED Dashboard** - Rate, Errors, Duration
7. **USE Dashboard** - Utilization, Saturation, Errors
8. **Service Dependencies** - Service mesh topology
9. **API Gateway** - Request rates, latencies, errors
10. **LLM Inference** - Token usage, latencies, costs

### Business Dashboards
11. **Cost Dashboard** - Multi-cloud cost breakdown
12. **SLO Dashboard** - Error budgets, burn rates
13. **User Analytics** - Active users, sessions, retention
14. **Revenue Metrics** - API usage, billing

## Alerting Rules

### Infrastructure Alerts
- **Node down** - Instance unreachable
- **High CPU** - CPU >80% for 5 minutes
- **High memory** - Memory >85% for 5 minutes
- **Disk space low** - <10% free space
- **Pod crash loops** - >3 restarts in 10 minutes

### Application Alerts
- **High error rate** - >5% errors for 5 minutes
- **High latency** - p95 >2s for 5 minutes
- **Low throughput** - <10 req/s for 10 minutes
- **Service down** - 0 healthy instances
- **Database connections** - >80% pool utilization

### SLO Alerts
- **Error budget exhausted** - <10% remaining
- **Fast burn rate** - Will exhaust budget in 24h
- **Slow burn rate** - Will exhaust budget in 7d

## Multi-Cloud Exporters

### AWS CloudWatch Exporter
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cloudwatch-exporter-config
data:
  config.yml: |
    region: us-east-1
    metrics:
      - aws_namespace: AWS/EC2
        aws_metric_name: CPUUtilization
        aws_dimensions: [InstanceId]
        aws_statistics: [Average]
      - aws_namespace: AWS/RDS
        aws_metric_name: DatabaseConnections
        aws_dimensions: [DBInstanceIdentifier]
```

### Azure Monitor Exporter
```yaml
metrics:
  - resource_type: Microsoft.Compute/virtualMachines
    metrics:
      - Percentage CPU
      - Network In Total
      - Network Out Total
  - resource_type: Microsoft.ContainerService/managedClusters
    metrics:
      - node_cpu_usage_percentage
      - node_memory_working_set_percentage
```

### GCP Stackdriver Exporter
```yaml
metrics:
  - compute.googleapis.com/instance/cpu/utilization
  - compute.googleapis.com/instance/network/received_bytes_count
  - container.googleapis.com/container/cpu/core_usage_time
```

## Cost Estimates

### Self-Managed on Kubernetes (AWS EKS)

| Component | Instances | Storage | Monthly Cost |
|-----------|-----------|---------|--------------|
| Prometheus (3 replicas) | t3.large | 500GB EBS | $315 |
| Loki (3 nodes) | t3.medium | 300GB EBS | $220 |
| Tempo (3 nodes) | t3.medium | 200GB EBS | $200 |
| Grafana (2 replicas) | t3.small | 20GB EBS | $60 |
| Thanos (S3 storage) | N/A | 2TB S3 | $46 |
| Data Transfer | Outbound | 500GB | $45 |
| **Total** | | | **~$886/month** |

### Managed Services

| Service | Plan | Monthly Cost |
|---------|------|--------------|
| Grafana Cloud (Metrics) | Pro - 10M samples/month | $299 |
| Grafana Cloud (Logs) | Pro - 100GB/month | $199 |
| Grafana Cloud (Traces) | Pro - 50GB/month | $149 |
| **Total** | | **~$647/month** |

## Documentation

- [Architecture Deep Dive](docs/architecture.md)
- [Multi-Cloud Setup Guide](docs/multi-cloud-setup.md)
- [Dashboard Creation Guide](docs/dashboards.md)
- [Alert Configuration](docs/alerting.md)
- [OpenTelemetry Instrumentation](docs/instrumentation.md)
- [Troubleshooting Guide](docs/troubleshooting.md)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

**Jose** | DevOps & Cloud Engineer
