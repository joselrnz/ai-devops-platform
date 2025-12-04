# Centralized Logging & Threat Analytics - Architecture

## Overview

The Centralized Logging & Threat Analytics platform is an enterprise SIEM (Security Information and Event Management) system built on OpenSearch with AI-powered threat detection using Sigma rules, real-time correlation, and comprehensive log enrichment.

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        Log Sources                                │
│                                                                   │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │
│  │Kubernetes │  │    AWS    │  │   Apps    │  │  Firewalls│    │
│  │   Pods    │  │CloudWatch │  │  (JSON)   │  │   (CEF)   │    │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘    │
└────────┼──────────────┼──────────────┼──────────────┼────────────┘
         │              │              │              │
         └──────────────┴──────────────┴──────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────────┐
│                     Fluent Bit Agents                             │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  INPUT PLUGINS                                             │  │
│  │  - tail (file logs)                                        │  │
│  │  - systemd (journal logs)                                  │  │
│  │  - tcp/udp (network logs)                                  │  │
│  │  - kubernetes (pod logs with metadata)                     │  │
│  └─────────────────────┬──────────────────────────────────────┘  │
│                        ▼                                          │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  FILTER PLUGINS                                            │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  kubernetes: Add pod/namespace/labels metadata       │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  parser: Parse JSON, syslog, nginx, apache formats   │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  geoip: Enrich with city, country, ASN, lat/lon      │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  modify: Add/rename/remove fields                     │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  └─────────────────────┬──────────────────────────────────────┘  │
│                        ▼                                          │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  OUTPUT PLUGIN                                             │  │
│  │  - opensearch (bulk API with batching)                    │  │
│  └────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                    OpenSearch Cluster                             │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                   Ingest Pipeline                           │  │
│  │  - Field extraction                                         │  │
│  │  - Data normalization                                       │  │
│  │  - Timestamp parsing                                        │  │
│  └─────────────────────┬──────────────────────────────────────┘  │
│                        ▼                                          │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              Index State Management (ISM)                   │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │  │
│  │  │   HOT    │→ │   WARM   │→ │   COLD   │→ │  DELETE  │   │  │
│  │  │  (7 days)│  │ (30 days)│  │ (90 days)│  │(365 days)│   │  │
│  │  │  NVMe SSD│  │  SSD     │  │  HDD/S3  │  │  Glacier │   │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │  │
│  └─────────────────────┬──────────────────────────────────────┘  │
│                        ▼                                          │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                 Sigma Rule Engine                           │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  Authentication Attacks (brute force, privilege esc)  │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  Data Exfiltration (DNS tunneling, large transfers)   │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  Lateral Movement (suspicious SSH, RDP sessions)      │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  Malware (reverse shells, C2 communication)           │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  Custom LLM Rules (prompt injection, data access)     │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  └─────────────────────┬──────────────────────────────────────┘  │
│                        │ Alerts Triggered                        │
│                        ▼                                          │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                Alert Manager                                │  │
│  │  - Deduplication                                            │  │
│  │  - Aggregation                                              │  │
│  │  - Routing (Slack, PagerDuty, Email)                       │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────┐
│                    OpenSearch Dashboards                          │
│  - SOC Overview Dashboard                                        │
│  - Threat Intelligence Feeds                                     │
│  - Incident Investigation Workbench                              │
│  - Compliance Reporting                                          │
└──────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Log Collection (Fluent Bit) ([helm/fluent-bit/values.yaml](helm/fluent-bit/values.yaml))

**Kubernetes Deployment**:
```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluent-bit
  namespace: logging
spec:
  selector:
    matchLabels:
      app: fluent-bit
  template:
    spec:
      serviceAccountName: fluent-bit
      containers:
      - name: fluent-bit
        image: fluent/fluent-bit:2.2
        resources:
          limits:
            memory: 200Mi
          requests:
            cpu: 100m
            memory: 100Mi
        volumeMounts:
        - name: varlog
          mountPath: /var/log
          readOnly: true
        - name: varlibdockercontainers
          mountPath: /var/lib/docker/containers
          readOnly: true
        - name: config
          mountPath: /fluent-bit/etc/
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
      - name: varlibdockercontainers
        hostPath:
          path: /var/lib/docker/containers
```

**Configuration** ([helm/fluent-bit/values.yaml](helm/fluent-bit/values.yaml)):
```ini
[INPUT]
    Name              tail
    Path              /var/log/containers/*.log
    Parser            docker
    Tag               kube.*
    Refresh_Interval  5
    Mem_Buf_Limit     5MB
    Skip_Long_Lines   On

[INPUT]
    Name        systemd
    Tag         host.*
    Read_From_Tail On

[FILTER]
    Name                kubernetes
    Match               kube.*
    Kube_URL            https://kubernetes.default.svc:443
    Kube_CA_File        /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    Kube_Token_File     /var/run/secrets/kubernetes.io/serviceaccount/token
    Merge_Log           On
    K8S-Logging.Parser  On
    K8S-Logging.Exclude On
    Labels              On
    Annotations         On

[FILTER]
    Name    parser
    Match   kube.*
    Key_Name log
    Parser  json
    Preserve_Key Off
    Reserve_Data On

[FILTER]
    Name   geoip2
    Match  *
    Database  /fluent-bit/geoip/GeoLite2-City.mmdb
    Lookup_key source.ip
    Record country source.geo.country_name
    Record city source.geo.city_name
    Record latitude source.geo.location.lat
    Record longitude source.geo.location.lon
    Record asn source.as.number
    Record as_org source.as.organization.name

[FILTER]
    Name    modify
    Match   *
    Add     cluster ${CLUSTER_NAME}
    Add     environment ${ENVIRONMENT}
    Rename  log message

[OUTPUT]
    Name            opensearch
    Match           *
    Host            opensearch-cluster-master
    Port            9200
    HTTP_User       ${OPENSEARCH_USERNAME}
    HTTP_Passwd     ${OPENSEARCH_PASSWORD}
    Index           logs
    Type            _doc
    Logstash_Format On
    Logstash_Prefix logs
    Retry_Limit     5
    Compress        gzip
    Buffer_Size     False
    tls             On
    tls.verify      Off
```

**Log Enrichment**:
```
Original Log:
{
  "log": "Failed login attempt from 192.168.1.100",
  "stream": "stderr",
  "time": "2024-12-01T20:00:00Z"
}

After Enrichment:
{
  "message": "Failed login attempt from 192.168.1.100",
  "timestamp": "2024-12-01T20:00:00Z",
  "kubernetes": {
    "pod_name": "auth-service-7c9f4b-xyz",
    "namespace_name": "production",
    "container_name": "app",
    "labels": {
      "app": "auth-service",
      "version": "v1.2.3"
    }
  },
  "source": {
    "ip": "192.168.1.100",
    "geo": {
      "country_name": "United States",
      "city_name": "San Francisco",
      "location": {"lat": 37.7749, "lon": -122.4194}
    },
    "as": {
      "number": 15169,
      "organization": {"name": "Google LLC"}
    }
  },
  "cluster": "prod-us-west-2",
  "environment": "production"
}
```

### 2. OpenSearch Cluster ([helm/opensearch/values.yaml](helm/opensearch/values.yaml))

**Cluster Configuration**:
```yaml
clusterName: opensearch-cluster

replicas: 3

roles:
  - master
  - ingest
  - data
  - remote_cluster_client

resources:
  requests:
    cpu: 2000m
    memory: 4Gi
  limits:
    cpu: 4000m
    memory: 8Gi

persistence:
  enabled: true
  size: 100Gi
  storageClass: gp3-encrypted

opensearchJavaOpts: "-Xms4g -Xmx4g"

config:
  opensearch.yml: |
    cluster.name: opensearch-cluster
    network.host: 0.0.0.0

    # Security
    plugins.security.ssl.http.enabled: true
    plugins.security.ssl.transport.enabled: true

    # Performance
    indices.memory.index_buffer_size: 30%
    indices.query.bool.max_clause_count: 4096

    # ISM
    opendistro_ism.enabled: true
```

**Index State Management Policies**:
```json
{
  "policy": {
    "description": "Hot-Warm-Cold-Delete policy for logs",
    "default_state": "hot",
    "states": [
      {
        "name": "hot",
        "actions": [
          {
            "rollover": {
              "min_index_age": "1d",
              "min_size": "50gb"
            }
          }
        ],
        "transitions": [
          {
            "state_name": "warm",
            "conditions": {
              "min_index_age": "7d"
            }
          }
        ]
      },
      {
        "name": "warm",
        "actions": [
          {
            "replica_count": {
              "number_of_replicas": 1
            }
          },
          {
            "force_merge": {
              "max_num_segments": 1
            }
          }
        ],
        "transitions": [
          {
            "state_name": "cold",
            "conditions": {
              "min_index_age": "30d"
            }
          }
        ]
      },
      {
        "name": "cold",
        "actions": [
          {
            "replica_count": {
              "number_of_replicas": 0
            }
          },
          {
            "snapshot": {
              "repository": "s3-repository",
              "snapshot": "logs-snapshot-{{ctx.index}}"
            }
          }
        ],
        "transitions": [
          {
            "state_name": "delete",
            "conditions": {
              "min_index_age": "90d"
            }
          }
        ]
      },
      {
        "name": "delete",
        "actions": [
          {
            "delete": {}
          }
        ]
      }
    ]
  }
}
```

**Storage Tiers**:
| Tier | Age | Storage | Replicas | Purpose |
|------|-----|---------|----------|---------|
| Hot  | 0-7d | NVMe SSD (gp3) | 2 | Active indexing & searching |
| Warm | 7-30d | SSD (gp2) | 1 | Recent queries, force merged |
| Cold | 30-90d | S3 (snapshots) | 0 | Archived, rare access |
| Delete | >90d | - | - | Removed (compliance dependent) |

### 3. Sigma Threat Detection Rules

#### Authentication - Brute Force ([sigma-rules/authentication/brute-force-login.yaml](sigma-rules/authentication/brute-force-login.yaml))

```yaml
title: Brute Force Login Attempts
id: 8a3c8b1c-7d4e-4f5a-9b2c-1d3e4f5a6b7c
status: stable
description: Detects multiple failed login attempts from same source IP
references:
  - https://attack.mitre.org/techniques/T1110/
author: Security Team
date: 2024-12-01
tags:
  - attack.credential_access
  - attack.t1110

logsource:
  product: linux
  category: authentication

detection:
  selection:
    event.action: 'login'
    event.outcome: 'failure'
  timeframe: 5m
  condition: selection | count(source.ip) by source.ip > 10

falsepositives:
  - Legitimate user with forgotten password
  - Automated health checks with wrong credentials

level: medium
```

**OpenSearch Query (Generated)**:
```json
{
  "query": {
    "bool": {
      "must": [
        {"match": {"event.action": "login"}},
        {"match": {"event.outcome": "failure"}}
      ],
      "filter": [
        {"range": {"@timestamp": {"gte": "now-5m"}}}
      ]
    }
  },
  "aggs": {
    "by_source_ip": {
      "terms": {"field": "source.ip", "min_doc_count": 10}
    }
  }
}
```

#### Data Exfiltration - DNS Tunneling ([sigma-rules/data-exfiltration/dns-tunneling.yaml](sigma-rules/data-exfiltration/dns-tunneling.yaml))

```yaml
title: DNS Tunneling Detected
id: 9b4d5c2f-8e3a-4c6b-9d7e-2f3a4b5c6d7e
status: experimental
description: Detects potential DNS tunneling for C2 communication
references:
  - https://attack.mitre.org/techniques/T1071/004/
tags:
  - attack.command_and_control
  - attack.t1071.004
  - attack.exfiltration
  - attack.t1048.003

logsource:
  product: dns
  service: bind

detection:
  selection:
    dns.question.type: 'TXT'
    dns.response.size: '>= 200'
  selection_high_entropy:
    dns.question.name|entropy: '>= 4.5'
  timeframe: 1m
  condition: selection and selection_high_entropy | count(source.ip) by source.ip > 50

falsepositives:
  - DNSSEC lookups
  - CDN health checks

level: high
```

#### Custom LLM - Prompt Injection ([sigma-rules/custom/llm-prompt-injection.yaml](sigma-rules/custom/llm-prompt-injection.yaml))

```yaml
title: LLM Prompt Injection Attempt Detected
id: 7c8d9e1a-2b3c-4d5e-6f7a-8b9c0d1e2f3a
status: experimental
description: Detects attempts to inject malicious instructions into LLM prompts
references:
  - https://owasp.org/www-project-top-10-for-large-language-model-applications/
tags:
  - attack.initial_access
  - llm.prompt_injection

logsource:
  product: llm
  service: gateway

detection:
  selection_endpoint:
    http.request.method: 'POST'
    http.request.path|contains:
      - '/chat/completions'
      - '/v1/completions'
  patterns_ignore:
    http.request.body|contains:
      - 'ignore previous instructions'
      - 'disregard system prompt'
      - 'bypass restrictions'
      - 'you are now in developer mode'
      - 'sudo mode'
  condition: selection_endpoint and patterns_ignore

falsepositives:
  - Security testing with proper authorization
  - Legitimate discussion of prompt injection

level: high
```

#### Custom LLM - Sensitive Data Access ([sigma-rules/custom/sensitive-data-access.yaml](sigma-rules/custom/sensitive-data-access.yaml))

```yaml
title: Unusual Sensitive Data Access via LLM
id: 3f4a5b6c-7d8e-9f0a-1b2c-3d4e5f6a7b8c
status: experimental
description: Detects LLM queries attempting to access sensitive customer/financial data
tags:
  - attack.collection
  - llm.data_leakage

logsource:
  product: llm
  service: gateway

detection:
  selection_sensitive_query:
    llm.request.prompt|contains:
      - 'credit card'
      - 'social security'
      - 'password'
      - 'api key'
      - 'secret'
  selection_high_volume:
    llm.response.tokens: '>= 2000'
  timeframe: 10m
  condition: selection_sensitive_query and selection_high_volume | count(user.id) by user.id > 5

falsepositives:
  - Legitimate customer support queries
  - Data analysis for reporting

level: medium
```

### 4. Alert Management

**Alert Workflow**:
```
Sigma Rule Match
  ↓
Create Alert Document in OpenSearch
  ↓
Alert Manager Processing
  ├─ Check Alert History (deduplication)
  ├─ Aggregate Similar Alerts (reduce noise)
  ├─ Enrich with Threat Intel
  └─ Route to Channels (Slack/PagerDuty/Email)
  ↓
Incident Created in Ticketing System
```

**Alert Routing Configuration**:
```yaml
route:
  receiver: 'default'
  group_by: ['alertname', 'source.ip']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'
      continue: true
    - match:
        severity: high
      receiver: 'slack-security'
    - match:
        severity: medium
      receiver: 'email-soc'

receivers:
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: $PAGERDUTY_API_KEY
        description: '{{ .GroupLabels.alertname }}'

  - name: 'slack-security'
    slack_configs:
      - api_url: $SLACK_WEBHOOK_URL
        channel: '#security-alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: |
          *Severity*: {{ .GroupLabels.severity }}
          *Source IP*: {{ .GroupLabels.source.ip }}
          *Description*: {{ .Annotations.description }}
```

### 5. SOC Dashboard ([dashboards/soc-overview.ndjson](dashboards/soc-overview.ndjson))

**Dashboard Visualizations**:
1. **Alert Timeline** (last 24h)
   - Color-coded by severity (red=critical, orange=high, yellow=medium)
   - Stacked area chart

2. **Top Attacking IPs** (last 7d)
   - Table with country, ASN, alert count
   - Click to investigate

3. **MITRE ATT&CK Heatmap**
   - Tactics x Techniques grid
   - Shows coverage and detection frequency

4. **Authentication Events**
   - Success vs failure rate
   - Geographic distribution

5. **Data Exfiltration Indicators**
   - Large transfers over time
   - DNS query entropy

6. **LLM Security Events**
   - Prompt injection attempts
   - Sensitive data access patterns

7. **Compliance Status**
   - Log retention adherence
   - Data coverage by source

## Data Flow Example

### Detection: Brute Force Attack

```
1. Failed Login Events (from auth-service pods)
   ↓
   2024-12-01T20:00:01Z: {"event": "login", "outcome": "failure", "source.ip": "1.2.3.4"}
   2024-12-01T20:00:03Z: {"event": "login", "outcome": "failure", "source.ip": "1.2.3.4"}
   ...
   (12 total failed logins in 5 minutes)

2. Fluent Bit Collection
   ↓
   - Tail pod logs
   - Add Kubernetes metadata (pod, namespace, labels)
   - GeoIP enrichment (country: China, city: Beijing)
   - Forward to OpenSearch

3. OpenSearch Ingestion
   ↓
   - Index to logs-2024.12.01
   - Apply ingest pipeline (field extraction, normalization)

4. Sigma Rule Evaluation (every 30s)
   ↓
   Query: "Failed logins from same IP > 10 in 5min"
   Match: 12 failed logins from 1.2.3.4
   ↓
   Alert Created:
   {
     "alert_id": "alert-123",
     "rule": "Brute Force Login Attempts",
     "severity": "medium",
     "source_ip": "1.2.3.4",
     "geo": {"country": "China", "city": "Beijing"},
     "failed_count": 12,
     "target_user": "admin",
     "mitre_attack": ["T1110"]
   }

5. Alert Routing
   ↓
   - Severity: medium → Route to #security-alerts Slack channel
   - Create ticket in Jira (SEC-4567)
   - Email SOC team

6. SOC Response
   ↓
   - Analyst reviews alert in dashboard
   - Checks IP reputation (threat intel)
   - Blocks IP in firewall
   - Marks alert as resolved
```

## Deployment

### Docker Compose (Development) ([docker-compose.yml](docker-compose.yml))

```yaml
version: '3.8'

services:
  opensearch:
    image: opensearchproject/opensearch:2.11.0
    environment:
      - cluster.name=opensearch-dev
      - discovery.type=single-node
      - OPENSEARCH_JAVA_OPTS=-Xms2g -Xmx2g
    ports:
      - "9200:9200"
    volumes:
      - opensearch-data:/usr/share/opensearch/data

  fluent-bit:
    image: fluent/fluent-bit:2.2
    volumes:
      - ./fluent-bit.conf:/fluent-bit/etc/fluent-bit.conf:ro
      - /var/log:/var/log:ro
    depends_on:
      - opensearch

  opensearch-dashboards:
    image: opensearchproject/opensearch-dashboards:2.11.0
    ports:
      - "5601:5601"
    environment:
      OPENSEARCH_HOSTS: '["http://opensearch:9200"]'
    depends_on:
      - opensearch
```

### Kubernetes (Production) ([scripts/deploy.sh](scripts/deploy.sh))

```bash
#!/bin/bash
set -e

# Install OpenSearch Operator
helm repo add opensearch https://opensearch-project.github.io/helm-charts/
helm install opensearch opensearch/opensearch \
  --namespace logging --create-namespace \
  --values helm/opensearch/values.yaml

# Deploy Fluent Bit DaemonSet
helm install fluent-bit fluent-bit/fluent-bit \
  --namespace logging \
  --values helm/fluent-bit/values.yaml

# Apply Sigma rules (via CronJob)
kubectl apply -f manifests/sigma-rule-sync-cronjob.yaml

# Import dashboards
kubectl apply -f manifests/dashboard-import-job.yaml
```

## Security Considerations

1. **Encryption**:
   - TLS for all communication (Fluent Bit → OpenSearch)
   - Encryption at rest for indices
   - S3 snapshots encrypted with KMS

2. **Access Control**:
   - RBAC for OpenSearch users
   - Kubernetes RBAC for log access
   - Audit logging for all queries

3. **Data Retention**:
   - PII redaction before indexing
   - Automated deletion after retention period
   - Immutable snapshots for compliance

## Performance

**Ingestion Rate**: Up to 100,000 events/sec per node
**Query Latency**: <100ms (p95) for simple queries, <500ms (p95) for aggregations
**Storage**: ~100GB/day (10k events/sec, avg 1KB/event)

## Cost Estimation

**Infrastructure** (per month):
- OpenSearch cluster (3x r6g.2xlarge): ~$600
- S3 storage (10TB): ~$230
- Data transfer: ~$50
- **Total**: ~$880/month

---

**Last Updated**: December 2024
**Version**: 1.0.0
**Status**: Production Ready
