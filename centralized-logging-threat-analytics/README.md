# Centralized Logging & Threat Analytics Platform

Enterprise-grade SIEM (Security Information and Event Management) platform for aggregating logs, detecting threats, and providing security analytics for AI/LLM infrastructure.

## Overview

This platform provides comprehensive security monitoring and threat detection for cloud-native AI applications. It collects logs from all infrastructure components, applies Sigma detection rules, and provides real-time alerting and forensic capabilities.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Data Sources                                    │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐          │
│  │   K8s    │   AWS    │  Apps    │  Network │   Auth   │          │
│  │   Logs   │   Logs   │   Logs   │   Logs   │   Logs   │          │
│  └─────┬────┴────┬─────┴────┬─────┴────┬─────┴────┬─────┘          │
└────────┼─────────┼──────────┼──────────┼──────────┼────────────────┘
         │         │          │          │          │
         └─────────┴──────────┴──────────┴──────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Log Collection Layer                              │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                      Fluent Bit                                 │ │
│  │  - DaemonSet on each K8s node                                  │ │
│  │  - Tail pod logs, system logs                                  │ │
│  │  - Parse, filter, enrich                                       │ │
│  │  - Multi-line parsing                                          │ │
│  │  - Kubernetes metadata enrichment                              │ │
│  └────────────────────────┬───────────────────────────────────────┘ │
└───────────────────────────┼─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Processing Layer                                  │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                      Logstash                                   │ │
│  │  - Grok parsing                                                 │ │
│  │  - GeoIP enrichment                                            │ │
│  │  - Field normalization (ECS format)                            │ │
│  │  - Sigma rule evaluation                                       │ │
│  │  - Threat intelligence lookup                                  │ │
│  └────────────────────────┬───────────────────────────────────────┘ │
└───────────────────────────┼─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Storage & Search Layer                            │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                   OpenSearch Cluster                            │ │
│  │  ┌──────────────┬──────────────┬──────────────┐               │ │
│  │  │ Master Node  │ Data Node 1  │ Data Node 2  │               │ │
│  │  │ (Coordinating│ (Hot Storage)│ (Warm Storage│               │ │
│  │  └──────────────┴──────────────┴──────────────┘               │ │
│  │  - Index lifecycle management (ILM)                            │ │
│  │  - 7-day hot, 30-day warm, 90-day cold                        │ │
│  │  - S3 archival for compliance (1 year)                        │ │
│  └────────────────────────────────────────────────────────────────┘ │
└───────────────────────────┼─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Analytics & Visualization                         │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                OpenSearch Dashboards                            │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │  Security Operations Center (SOC) Dashboard              │  │ │
│  │  │  - Threat detection overview                             │  │ │
│  │  │  - Alert timeline                                        │  │ │
│  │  │  - Top attackers/targets                                 │  │ │
│  │  │  - Geographic threat map                                 │  │ │
│  │  └──────────────────────────────────────────────────────────┘  │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │  Compliance Dashboard                                    │  │ │
│  │  │  - Audit log review                                      │  │ │
│  │  │  - Access patterns                                       │  │ │
│  │  │  - Data exfiltration monitoring                          │  │ │
│  │  └──────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────┘ │
└───────────────────────────┼─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Alerting & Response                               │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                  Alert Manager                                  │ │
│  │  - Slack notifications                                          │ │
│  │  - PagerDuty integration                                        │ │
│  │  - Email alerts                                                 │ │
│  │  - Webhook for SOAR integration                                │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Features

### 🔍 Log Collection & Aggregation
- **Fluent Bit DaemonSet** - Lightweight log shipper on every K8s node
- **Multi-source collection** - Application logs, system logs, audit logs, network flows
- **Log parsing** - JSON, syslog, CEF, custom formats
- **Enrichment** - Kubernetes metadata, GeoIP, threat intelligence
- **Buffering & reliability** - Persistent queues, retry logic

### 🛡️ Threat Detection
- **Sigma Rules** - 200+ pre-configured detection rules
- **Custom rules** - YAML-based rule definitions
- **MITRE ATT&CK mapping** - Tactics and techniques coverage
- **Real-time detection** - Sub-second alert generation
- **False positive tuning** - Allowlisting and thresholds

### 📊 Security Analytics
- **Pre-built dashboards** - SOC overview, compliance, forensics
- **Search & investigation** - Full-text search with ECS schema
- **Threat hunting** - Ad-hoc queries and saved searches
- **Reporting** - Scheduled reports (daily, weekly, monthly)
- **Data retention** - Hot (7d), Warm (30d), Cold (90d), Archive (1yr)

### 🚨 Alerting & Incident Response
- **Multi-channel notifications** - Slack, PagerDuty, email, webhooks
- **Alert prioritization** - Critical, high, medium, low
- **Alert grouping** - Reduce noise with intelligent deduplication
- **Incident tracking** - Link to ticketing systems (Jira, ServiceNow)
- **Playbook automation** - Automated response actions

### 📈 Performance & Scalability
- **Distributed architecture** - Scales horizontally
- **Index lifecycle management** - Automatic data tiering
- **Query optimization** - Caching, aggregations
- **Retention policies** - Cost-effective storage tiers
- **Monitoring** - Prometheus metrics for all components

## Tech Stack

- **Log Collection**: Fluent Bit 2.2+
- **Log Processing**: Logstash 8.11+
- **Storage**: OpenSearch 2.11+
- **Visualization**: OpenSearch Dashboards 2.11+
- **Detection**: Sigma Rules (YAML)
- **Alerting**: OpenSearch Alerting Plugin
- **Orchestration**: Kubernetes 1.28+, Helm 3.x
- **Infrastructure**: Terraform (AWS EBS volumes)

## Project Structure

```
centralized-logging-threat-analytics/
├── helm/
│   ├── opensearch/           # OpenSearch cluster chart
│   ├── fluent-bit/           # Log collection chart
│   ├── logstash/             # Log processing chart
│   └── dashboards/           # OpenSearch Dashboards
├── sigma-rules/
│   ├── authentication/       # Auth-related detections
│   ├── lateral-movement/     # Lateral movement detections
│   ├── data-exfiltration/    # Data theft detections
│   ├── malware/              # Malware detections
│   └── custom/               # Custom rules
├── dashboards/
│   ├── soc-overview.ndjson   # Security operations dashboard
│   ├── compliance.ndjson     # Compliance monitoring
│   ├── forensics.ndjson      # Investigation dashboard
│   └── threat-hunting.ndjson # Threat hunting workspace
├── fluent-bit/
│   ├── configs/              # Fluent Bit configurations
│   └── parsers/              # Log parsers
├── logstash/
│   ├── pipelines/            # Logstash pipelines
│   └── filters/              # Grok patterns, filters
├── terraform/
│   ├── opensearch/           # OpenSearch infrastructure
│   └── storage/              # EBS volumes, S3 buckets
└── docs/                     # Documentation
```

## Quick Start

### 1. Deploy OpenSearch Cluster

```bash
# Add Helm repository
helm repo add opensearch https://opensearch-project.github.io/helm-charts/
helm repo update

# Install OpenSearch
helm install opensearch helm/opensearch \
  --namespace logging \
  --create-namespace \
  -f helm/opensearch/values.yaml

# Wait for cluster to be ready
kubectl wait --for=condition=ready pod \
  -l app=opensearch-cluster-master \
  -n logging \
  --timeout=300s
```

### 2. Deploy Fluent Bit

```bash
# Install Fluent Bit DaemonSet
helm install fluent-bit helm/fluent-bit \
  --namespace logging \
  -f helm/fluent-bit/values.yaml

# Verify pods running on all nodes
kubectl get pods -n logging -l app.kubernetes.io/name=fluent-bit
```

### 3. Deploy Logstash (Optional)

```bash
# Install Logstash for advanced processing
helm install logstash helm/logstash \
  --namespace logging \
  -f helm/logstash/values.yaml
```

### 4. Deploy OpenSearch Dashboards

```bash
# Install Dashboards
helm install opensearch-dashboards helm/dashboards \
  --namespace logging \
  -f helm/dashboards/values.yaml

# Port-forward to access UI
kubectl port-forward -n logging svc/opensearch-dashboards 5601:5601

# Open http://localhost:5601
# Username: admin
# Password: (from secret)
```

### 5. Import Dashboards & Rules

```bash
# Import pre-built dashboards
./scripts/import-dashboards.sh

# Deploy Sigma rules
kubectl apply -f sigma-rules/
```

## Security Detection Rules

### Pre-configured Sigma Rules

#### Authentication Attacks
- **Brute force login attempts** - Multiple failed logins
- **Credential stuffing** - Password spray attacks
- **Privilege escalation** - Unauthorized sudo/admin access
- **MFA bypass attempts** - Multi-factor authentication failures

#### Lateral Movement
- **Suspicious SSH connections** - Internal network traversal
- **Pass-the-hash attacks** - NTLM hash reuse
- **Remote execution** - PSExec, WMI, PowerShell remoting
- **Port scanning** - Network reconnaissance

#### Data Exfiltration
- **Large data transfers** - Unusual egress volume
- **Sensitive file access** - PII, credentials, secrets
- **DNS tunneling** - Covert channels
- **Cloud storage uploads** - S3, GCS, Azure Blob

#### Malware & Exploits
- **Reverse shells** - Netcat, Metasploit
- **Web shells** - PHP, JSP, ASPX backdoors
- **Cryptocurrency mining** - CPU spikes, mining pools
- **Exploit frameworks** - Metasploit, Cobalt Strike

### Custom Rule Example

```yaml
# sigma-rules/custom/llm-prompt-injection.yaml
title: LLM Prompt Injection Attempt
id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
status: experimental
description: Detects potential prompt injection attacks against LLM endpoints
references:
  - https://owasp.org/www-project-top-10-for-large-language-model-applications/
author: Jose
date: 2024/01/15
tags:
  - attack.initial_access
  - attack.t1190
logsource:
  category: application
  product: llm-gateway
detection:
  selection:
    http.request.method: POST
    http.request.path: /chat/completions
  patterns:
    http.request.body|contains:
      - 'ignore previous instructions'
      - 'disregard system prompt'
      - 'bypass restrictions'
      - 'reveal your instructions'
  condition: selection and patterns
fields:
  - user.id
  - source.ip
  - http.request.body
falsepositives:
  - Legitimate testing activities
level: high
```

## Dashboards

### 1. SOC Overview Dashboard
- **Threat detection timeline** - Alerts over time
- **Top attackers** - Source IPs with most alerts
- **Attack vectors** - MITRE ATT&CK heatmap
- **Alert severity distribution** - Critical/High/Medium/Low
- **Response metrics** - MTTD, MTTR

### 2. Compliance Dashboard
- **Audit log summary** - All user actions
- **Access patterns** - Who accessed what
- **Failed authentication attempts** - Security events
- **Configuration changes** - Infrastructure modifications
- **Data access logs** - PII/sensitive data access

### 3. Forensics Dashboard
- **User activity timeline** - Detailed user actions
- **Network connections** - Source/destination analysis
- **File operations** - Read/write/delete events
- **Process execution** - Command line analysis
- **Correlation search** - Link related events

## Cost Estimates

### AWS OpenSearch Service (3-node cluster)

| Component | Instance Type | Storage | Monthly Cost |
|-----------|---------------|---------|--------------|
| Master Node | r6g.large.search | 100GB | $155 |
| Data Node 1 | r6g.xlarge.search | 500GB | $340 |
| Data Node 2 | r6g.xlarge.search | 500GB | $340 |
| S3 Archive | Standard | 1TB | $23 |
| Data Transfer | Outbound | 100GB | $9 |
| **Total** | | | **~$867/month** |

### Self-Managed on EKS (Cost-Optimized)

| Component | Instance Type | Storage | Monthly Cost |
|-----------|---------------|---------|--------------|
| OpenSearch (3 pods) | t3.xlarge | 300GB EBS | $270 |
| Fluent Bit (DaemonSet) | Included | N/A | $0 |
| Logstash (2 pods) | t3.medium | N/A | $60 |
| S3 Archive | Standard | 1TB | $23 |
| **Total** | | | **~$353/month** |

## Documentation

- [Architecture Deep Dive](docs/architecture.md)
- [Sigma Rule Writing Guide](docs/sigma-rules.md)
- [Dashboard Creation](docs/dashboards.md)
- [Tuning & Optimization](docs/tuning.md)
- [Incident Response Playbooks](docs/playbooks.md)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

**Jose** | DevOps & Cloud Engineer
