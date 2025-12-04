# Multi-Cloud Observability Fabric - Architecture

## Overview

The Multi-Cloud Observability Fabric is a unified observability platform covering the three pillars (metrics, logs, traces) across AWS, Azure, and GCP with long-term storage, SLO/SLI dashboards, and cost attribution.

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      Cloud Providers                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │     AWS      │  │    Azure     │  │     GCP      │           │
│  │  CloudWatch  │  │Azure Monitor │  │Cloud Monitor │           │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │
└─────────┼──────────────────┼──────────────────┼───────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Cloud Exporters                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  CloudWatch  │  │    Azure     │  │     GCP      │           │
│  │   Exporter   │  │   Exporter   │  │   Exporter   │           │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │
└─────────┼──────────────────┼──────────────────┼───────────────────┘
          │                  │                  │
          └──────────────────┴──────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                  Prometheus (HA Setup)                            │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Prometheus Server 1 (Active)                              │  │
│  │  - Scrape interval: 15s                                    │  │
│  │  - Local retention: 15 days                                │  │
│  │  - Remote write to Thanos                                  │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Prometheus Server 2 (Active)                              │  │
│  │  - Scrape interval: 15s                                    │  │
│  │  - Local retention: 15 days                                │  │
│  │  - Remote write to Thanos                                  │  │
│  └─────────────────────┬──────────────────────────────────────┘  │
└────────────────────────┼─────────────────────────────────────────┘
                         │ Remote Write
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                   Thanos (Long-Term Storage)                      │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Thanos Receive                                            │  │
│  │  - Accepts remote write from Prometheus                    │  │
│  │  - Replicates to S3                                        │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Thanos Store Gateway                                      │  │
│  │  - Queries historical data from S3                         │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Thanos Query (Unified Query Layer)                        │  │
│  │  - Aggregates Prometheus + S3 data                         │  │
│  │  - Deduplication                                           │  │
│  │  - PromQL API                                              │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                  Loki (Log Aggregation)                           │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Loki Distributor                                          │  │
│  │  - Receives logs from applications                         │  │
│  │  - Hashes labels for consistent routing                    │  │
│  └─────────────────────┬──────────────────────────────────────┘  │
│                        ▼                                          │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Loki Ingester                                             │  │
│  │  - Buffers logs in memory                                  │  │
│  │  - Flushes chunks to S3                                    │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Loki Querier                                              │  │
│  │  - LogQL query engine                                      │  │
│  │  - Reads from ingesters + S3                               │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                 Tempo (Distributed Tracing)                       │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Tempo Distributor                                         │  │
│  │  - Receives traces (OTLP, Jaeger, Zipkin)                  │  │
│  │  - Hash-based routing                                      │  │
│  └─────────────────────┬──────────────────────────────────────┘  │
│                        ▼                                          │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Tempo Ingester                                            │  │
│  │  - Buffers traces in memory                                │  │
│  │  - Creates bloom filters for fast lookup                   │  │
│  │  - Flushes to S3                                           │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Tempo Metrics Generator                                   │  │
│  │  - Generates span metrics (RED: Rate, Errors, Duration)    │  │
│  │  - Remote writes to Prometheus                             │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Tempo Querier                                             │  │
│  │  - TraceQL query engine                                    │  │
│  │  - Reads from ingesters + S3                               │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│            OpenTelemetry Collector (Unified Ingestion)            │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Receivers                                                  │  │
│  │  - OTLP (gRPC, HTTP)                                        │  │
│  │  - Jaeger, Zipkin                                           │  │
│  │  - Prometheus (scrape)                                      │  │
│  └─────────────────────┬──────────────────────────────────────┘  │
│                        ▼                                          │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Processors                                                 │  │
│  │  - Batch (reduce API calls)                                 │  │
│  │  - Attributes (add/remove metadata)                         │  │
│  │  - Resource detection (cloud provider, K8s)                 │  │
│  │  - Sampling (head-based, tail-based)                        │  │
│  └─────────────────────┬──────────────────────────────────────┘  │
│                        ▼                                          │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Exporters                                                  │  │
│  │  - Prometheus (remote write)                                │  │
│  │  - Loki                                                     │  │
│  │  - Tempo                                                    │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                      Grafana (Visualization)                      │
│  - Multi-cloud overview dashboards                               │
│  - SLO/SLI tracking                                              │
│  - Alert visualization                                           │
│  - Unified query (Prometheus, Loki, Tempo)                       │
└──────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Prometheus HA Setup ([helm/kube-prometheus-stack/values.yaml](helm/kube-prometheus-stack/values.yaml))

**Configuration**:
```yaml
prometheus:
  prometheusSpec:
    replicas: 2
    retention: 15d
    retentionSize: "50GB"

    externalLabels:
      cluster: prod-us-west-2
      environment: production

    # Remote write to Thanos
    remoteWrite:
      - url: http://thanos-receive:19291/api/v1/receive
        writeRelabelConfigs:
          - sourceLabels: [__name__]
            regex: 'up|container_.*|node_.*'
            action: keep

    # Service discovery
    additionalScrapeConfigs:
      # AWS CloudWatch exporter
      - job_name: 'cloudwatch-exporter'
        static_configs:
          - targets: ['cloudwatch-exporter:9106']
        relabel_configs:
          - target_label: cloud_provider
            replacement: aws

      # Azure Monitor exporter
      - job_name: 'azure-exporter'
        static_configs:
          - targets: ['azure-exporter:9276']
        relabel_configs:
          - target_label: cloud_provider
            replacement: azure

      # GCP exporter
      - job_name: 'stackdriver-exporter'
        static_configs:
          - targets: ['stackdriver-exporter:9255']
        relabel_configs:
          - target_label: cloud_provider
            replacement: gcp

      # Kubernetes pods with annotations
      - job_name: 'kubernetes-pods'
        kubernetes_sd_configs:
          - role: pod
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
            action: keep
            regex: true
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
            action: replace
            target_label: __metrics_path__
            regex: (.+)
          - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
            action: replace
            regex: ([^:]+)(?::\d+)?;(\d+)
            replacement: $1:$2
            target_label: __address__
```

**Deduplication Strategy**:
```yaml
thanos:
  query:
    replicaLabel:
      - prometheus_replica
      - replica
    dedup: true  # Enable deduplication
```

### 2. Thanos Long-Term Storage

**Thanos Receive** (Remote Write Endpoint):
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: thanos-receive
spec:
  serviceName: thanos-receive
  replicas: 3
  template:
    spec:
      containers:
      - name: thanos
        image: quay.io/thanos/thanos:v0.33.0
        args:
          - receive
          - --tsdb.path=/var/thanos/receive
          - --objstore.config-file=/etc/thanos/objstore.yaml
          - --label=receive_replica="$(NAME)"
          - --receive.replication-factor=2
          - --receive.hashrings-file=/etc/thanos/hashrings.json
        volumeMounts:
          - name: data
            mountPath: /var/thanos/receive
          - name: objstore-config
            mountPath: /etc/thanos/objstore.yaml
            subPath: objstore.yaml
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi
```

**S3 Configuration** (objstore.yaml):
```yaml
type: S3
config:
  bucket: thanos-metrics
  endpoint: s3.us-east-1.amazonaws.com
  access_key: ${AWS_ACCESS_KEY_ID}
  secret_key: ${AWS_SECRET_ACCESS_KEY}
  sse_config:
    type: SSE-S3
```

**Thanos Query** (Unified Query Layer):
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: thanos-query
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: thanos
        image: quay.io/thanos/thanos:v0.33.0
        args:
          - query
          - --http-address=0.0.0.0:9090
          - --grpc-address=0.0.0.0:10901
          - --store=dnssrv+_grpc._tcp.thanos-receive:10901
          - --store=dnssrv+_grpc._tcp.thanos-store:10901
          - --store=dnssrv+_grpc._tcp.prometheus-operated:10901
          - --query.replica-label=prometheus_replica
          - --query.replica-label=replica
```

### 3. Loki Distributed ([helm/loki/values.yaml](helm/loki/values.yaml))

**Architecture**:
```yaml
loki:
  structuredConfig:
    auth_enabled: false

    server:
      http_listen_port: 3100
      grpc_listen_port: 9096

    distributor:
      ring:
        kvstore:
          store: memberlist

    ingester:
      wal:
        enabled: true
        dir: /loki/wal
      lifecycler:
        ring:
          kvstore:
            store: memberlist
          replication_factor: 3
      chunk_idle_period: 5m
      chunk_retain_period: 30s
      max_chunk_age: 1h

    schema_config:
      configs:
        - from: 2024-01-01
          store: boltdb-shipper
          object_store: s3
          schema: v11
          index:
            prefix: loki_index_
            period: 24h

    storage_config:
      boltdb_shipper:
        active_index_directory: /loki/index
        cache_location: /loki/cache
        shared_store: s3
      aws:
        s3: s3://us-east-1/loki-chunks
        s3forcepathstyle: false

    limits_config:
      enforce_metric_name: false
      reject_old_samples: true
      reject_old_samples_max_age: 168h  # 7 days
      retention_period: 744h  # 31 days
      max_query_length: 721h  # 30 days
      max_query_series: 100000
      max_query_parallelism: 32

    compactor:
      working_directory: /loki/compactor
      shared_store: s3
      compaction_interval: 10m
      retention_enabled: true
      retention_delete_delay: 2h
      retention_delete_worker_count: 150

    query_scheduler:
      max_outstanding_requests_per_tenant: 4096

    frontend:
      max_outstanding_per_tenant: 4096
```

**LogQL Query Examples**:
```logql
# All logs from production namespace
{namespace="production"}

# Error logs with rate
rate({app="api"} |= "error" [5m])

# Metrics from logs (count by HTTP status)
sum by (status_code) (
  rate({app="api"} | json | __error__="" [5m])
)

# P99 latency from logs
histogram_quantile(0.99,
  sum by (le) (
    rate({app="api"} | json | unwrap response_time [5m])
  )
)
```

### 4. Tempo Distributed Tracing ([helm/tempo/values.yaml](helm/tempo/values.yaml))

**Configuration**:
```yaml
tempo:
  structuredConfig:
    distributor:
      receivers:
        otlp:
          protocols:
            grpc:
              endpoint: 0.0.0.0:4317
            http:
              endpoint: 0.0.0.0:4318
        jaeger:
          protocols:
            grpc:
              endpoint: 0.0.0.0:14250
            thrift_http:
              endpoint: 0.0.0.0:14268

    ingester:
      trace_idle_period: 30s
      max_block_duration: 10m
      max_block_bytes: 1048576  # 1MB

    storage:
      trace:
        backend: s3
        s3:
          bucket: tempo-traces
          endpoint: s3.us-east-1.amazonaws.com
        pool:
          max_workers: 100
          queue_depth: 10000

    overrides:
      defaults:
        metrics_generator:
          processors:
            - service-graphs
            - span-metrics
          generate_native_histograms: true
          storage:
            remote_write:
              - url: http://prometheus:9090/api/v1/write
                send_exemplars: true

metricsGenerator:
  enabled: true
  config:
    processor:
      span_metrics:
        dimensions:
          - name: http.method
          - name: http.status_code
          - name: service.name
        histogram_buckets: [0.1, 0.25, 0.5, 1, 2.5, 5, 10]
      service_graphs:
        dimensions:
          - service.name
          - service.namespace
```

**Generated Metrics**:
```
# Request rate
traces_spanmetrics_calls_total{service_name="api", http_method="GET", http_status_code="200"}

# Latency histogram
traces_spanmetrics_latency_bucket{service_name="api", http_method="GET", le="0.5"}

# Service graph metrics
traces_service_graph_request_total{client="frontend", server="api"}
```

**TraceQL Query Examples**:
```traceql
# Find traces with errors
{status=error}

# Traces for specific service and operation
{service.name="api" && name="GET /users"}

# Slow traces (duration > 1s)
{duration > 1s}

# Complex query with aggregation
{service.name="api"} | avg(duration) by (http.method) > 500ms
```

### 5. OpenTelemetry Collector ([helm/opentelemetry-collector/values.yaml](helm/opentelemetry-collector/values.yaml))

**Configuration**:
```yaml
config:
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: 0.0.0.0:4317
        http:
          endpoint: 0.0.0.0:4318

    prometheus:
      config:
        scrape_configs:
          - job_name: 'otel-collector'
            scrape_interval: 10s
            static_configs:
              - targets: ['0.0.0.0:8888']

  processors:
    batch:
      timeout: 10s
      send_batch_size: 1024

    attributes:
      actions:
        - key: environment
          value: production
          action: upsert
        - key: cluster
          value: ${CLUSTER_NAME}
          action: upsert

    resource:
      attributes:
        - key: service.instance.id
          from_attribute: k8s.pod.uid
          action: insert

    k8sattributes:
      auth_type: "serviceAccount"
      extract:
        metadata:
          - k8s.namespace.name
          - k8s.deployment.name
          - k8s.pod.name
          - k8s.node.name

    probabilistic_sampler:
      sampling_percentage: 10  # Sample 10% of traces

    tail_sampling:
      decision_wait: 10s
      policies:
        - name: error-traces
          type: status_code
          status_code:
            status_codes: [ERROR]
        - name: slow-traces
          type: latency
          latency:
            threshold_ms: 1000
        - name: sample-others
          type: probabilistic
          probabilistic:
            sampling_percentage: 1

  exporters:
    prometheus:
      endpoint: "0.0.0.0:8889"

    prometheusremotewrite:
      endpoint: http://prometheus:9090/api/v1/write

    loki:
      endpoint: http://loki-distributor:3100/loki/api/v1/push

    otlp:
      endpoint: tempo-distributor:4317
      tls:
        insecure: true

  service:
    pipelines:
      traces:
        receivers: [otlp, jaeger, zipkin]
        processors: [k8sattributes, batch, resource, tail_sampling]
        exporters: [otlp]

      metrics:
        receivers: [otlp, prometheus]
        processors: [k8sattributes, batch, attributes]
        exporters: [prometheusremotewrite]

      logs:
        receivers: [otlp]
        processors: [k8sattributes, batch, attributes]
        exporters: [loki]
```

### 6. Alerting ([alerts/infrastructure.yaml](alerts/infrastructure.yaml) + [alerts/applications.yaml](alerts/applications.yaml))

**Infrastructure Alerts**:
```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: infrastructure-alerts
spec:
  groups:
  - name: infrastructure
    interval: 30s
    rules:
    - alert: HighCPUUsage
      expr: |
        100 - (avg by (instance, cloud_provider) (
          irate(node_cpu_seconds_total{mode="idle"}[5m])
        ) * 100) > 80
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High CPU usage on {{ $labels.instance }}"
        description: "CPU usage is {{ $value }}%"

    - alert: HighMemoryUsage
      expr: |
        (1 - (
          node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes
        )) * 100 > 90
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "High memory usage on {{ $labels.instance }}"

    - alert: DiskSpaceRunningOut
      expr: |
        (node_filesystem_avail_bytes{mountpoint="/"} /
         node_filesystem_size_bytes{mountpoint="/"}) * 100 < 10
      for: 10m
      labels:
        severity: critical
      annotations:
        summary: "Disk space running out on {{ $labels.instance }}"
        description: "Only {{ $value }}% free"
```

**Application Alerts**:
```yaml
- alert: HighErrorRate
  expr: |
    (sum(rate(http_requests_total{status=~"5.."}[5m])) by (service, cloud_provider) /
     sum(rate(http_requests_total[5m])) by (service, cloud_provider)) > 0.05
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "High error rate for {{ $labels.service }}"
    description: "Error rate is {{ $value | humanizePercentage }}"

- alert: SlowResponseTime
  expr: |
    histogram_quantile(0.99,
      sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service)
    ) > 1
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "Slow response time for {{ $labels.service }}"
    description: "P99 latency is {{ $value }}s"

- alert: HighLLMTokenUsage
  expr: |
    sum(rate(llm_tokens_total[5m])) by (model, service) > 1000000
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "High LLM token usage for {{ $labels.model }}"
    description: "Using {{ $value }} tokens/sec"

- alert: HighLLMCosts
  expr: |
    sum(rate(llm_cost_usd_total[1h])) > 100
  for: 1h
  labels:
    severity: critical
  annotations:
    summary: "LLM costs are unusually high"
    description: "Spending ${{ $value }}/hour"
```

### 7. Dashboards

#### Multi-Cloud Overview ([dashboards/infrastructure/multi-cloud-overview.json](dashboards/infrastructure/multi-cloud-overview.json))

**Panels**:
1. **Total Resources by Provider** (Pie Chart)
   ```promql
   count(up{cloud_provider!=""}) by (cloud_provider)
   ```

2. **CPU Usage by Cloud Provider** (Time Series)
   ```promql
   avg by (cloud_provider) (
     100 - (avg by (instance, cloud_provider) (
       irate(node_cpu_seconds_total{mode="idle"}[5m])
     ) * 100)
   )
   ```

3. **Network Traffic by Provider** (Stacked Area)
   ```promql
   sum by (cloud_provider) (
     rate(node_network_transmit_bytes_total[5m])
   )
   ```

4. **Cost by Provider** (Bar Gauge)
   ```promql
   sum by (cloud_provider) (
     increase(cloud_cost_usd_total[24h])
   )
   ```

#### RED Dashboard ([dashboards/applications/red-dashboard.json](dashboards/applications/red-dashboard.json))

**RED Metrics** (Rate, Errors, Duration):
1. **Request Rate**
   ```promql
   sum by (service) (
     rate(http_requests_total[5m])
   )
   ```

2. **Error Rate**
   ```promql
   sum by (service) (
     rate(http_requests_total{status=~"5.."}[5m])
   ) /
   sum by (service) (
     rate(http_requests_total[5m])
   )
   ```

3. **Duration (P50, P95, P99)**
   ```promql
   histogram_quantile(0.50, sum by (le, service) (
     rate(http_request_duration_seconds_bucket[5m])
   ))

   histogram_quantile(0.95, sum by (le, service) (
     rate(http_request_duration_seconds_bucket[5m])
   ))

   histogram_quantile(0.99, sum by (le, service) (
     rate(http_request_duration_seconds_bucket[5m])
   ))
   ```

## Data Flow Example

### End-to-End Trace

```
1. User Request
   ↓
   HTTP GET /api/users

2. Application (Instrumented with OTEL SDK)
   ↓
   - Create span: "GET /api/users"
   - Add attributes: http.method, http.route, http.status_code
   - Emit metrics: http_requests_total, http_request_duration_seconds
   - Emit logs: "Processing request for user list"
   - Send to OpenTelemetry Collector

3. OpenTelemetry Collector
   ↓
   Traces → processors → Tempo
   Metrics → processors → Prometheus
   Logs → processors → Loki

4. Storage
   ↓
   Tempo: Trace stored in S3 with bloom filter
   Prometheus: Metrics stored locally (15d) + remote write to Thanos
   Loki: Logs stored in chunks on S3

5. Query (Grafana)
   ↓
   User queries: "Show all requests with duration > 1s"

   Grafana → Tempo:
     TraceQL: {duration > 1s && service.name="api"}

   Returns trace IDs → Exemplar links to Prometheus

   Prometheus:
     PromQL: http_request_duration_seconds{service="api"}

   Returns metrics with exemplar → Link to trace

   Loki:
     LogQL: {service="api"} | json | duration > 1000

   Returns logs with trace_id → Link to trace

6. Correlation
   ↓
   Single pane of glass:
   - Trace visualization (span waterfall)
   - Metrics for that time range
   - Logs for that trace_id
   - All correlated by trace_id
```

## Multi-Cloud Cost Attribution

**Cost Metric Collection**:
```yaml
# AWS cost (CloudWatch exporter)
aws_cost_usd_total{service="EC2", region="us-east-1"} 45.67

# Azure cost (Azure exporter)
azure_cost_usd_total{service="VirtualMachines", location="eastus"} 32.45

# GCP cost (Stackdriver exporter)
gcp_cost_usd_total{service="compute", region="us-central1"} 28.90

# Aggregate
sum by (cloud_provider) (
  aws_cost_usd_total or
  azure_cost_usd_total or
  gcp_cost_usd_total
)
```

## Deployment

### Docker Compose ([docker-compose.yml](docker-compose.yml))

```bash
docker-compose up
# Access Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
# Loki: http://localhost:3100
# Tempo: http://localhost:3200
```

### Kubernetes

```bash
# Add Helm repos
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Install Prometheus
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --values helm/kube-prometheus-stack/values.yaml

# Install Loki
helm install loki grafana/loki-distributed \
  --namespace monitoring \
  --values helm/loki/values.yaml

# Install Tempo
helm install tempo grafana/tempo-distributed \
  --namespace monitoring \
  --values helm/tempo/values.yaml

# Install OpenTelemetry Collector
helm install otel-collector open-telemetry/opentelemetry-collector \
  --namespace monitoring \
  --values helm/opentelemetry-collector/values.yaml
```

## Performance Characteristics

**Ingestion**:
- Metrics: 1M samples/sec per Prometheus instance
- Logs: 1GB/sec per Loki ingester
- Traces: 10K spans/sec per Tempo ingester

**Query Latency**:
- Metrics (PromQL): <100ms (p95) for simple queries
- Logs (LogQL): <500ms (p95) with proper labels
- Traces (TraceQL): <200ms (p95) for trace ID lookup

**Storage**:
- Metrics: ~1KB per series per hour
- Logs: ~100GB/day (10K logs/sec, avg 1KB/log)
- Traces: ~50GB/day (1K traces/sec, avg 50KB/trace)

## Cost Estimation

**Infrastructure** (per month):
- Prometheus HA (2x r6g.xlarge): ~$200
- Thanos (3x r6g.large): ~$120
- Loki (3x r6g.xlarge): ~$300
- Tempo (3x r6g.xlarge): ~$300
- S3 storage (5TB): ~$115
- Data transfer: ~$100
- **Total**: ~$1,135/month

---

**Last Updated**: December 2024
**Version**: 1.0.0
**Status**: Production Ready
