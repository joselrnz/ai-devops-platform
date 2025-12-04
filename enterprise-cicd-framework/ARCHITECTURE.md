# Enterprise CI/CD Framework - Architecture

## Overview

The Enterprise CI/CD Framework provides SLSA Level 3 compliant pipelines with comprehensive security scanning, SBOM generation, image signing, and GitOps deployment. It supports multiple platforms (GitHub Actions, GitLab CI) and languages (Python, Node.js, Go).

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                       Source Code Repository                      │
│                    (GitHub / GitLab / Bitbucket)                  │
└────────────────────────────┬─────────────────────────────────────┘
                             │ Git Push / PR
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                         CI/CD Pipeline                            │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  STAGE 1: Build                                            │  │
│  │  - Checkout code                                           │  │
│  │  - Install dependencies                                    │  │
│  │  - Run unit tests                                          │  │
│  │  - Build artifacts                                         │  │
│  │  - Build Docker image                                      │  │
│  └─────────────────────┬──────────────────────────────────────┘  │
│                        ▼                                          │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  STAGE 2: Security Scanning                                │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  SAST (SonarQube)                                     │  │  │
│  │  │  - Code quality analysis                              │  │  │
│  │  │  - Security vulnerabilities                           │  │  │
│  │  │  - Code smells & tech debt                            │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  Dependency Scanning                                  │  │  │
│  │  │  - npm audit / pip-audit / govulncheck               │  │  │
│  │  │  - Known vulnerability detection                      │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  Secret Detection (TruffleHog)                        │  │  │
│  │  │  - API keys, passwords, tokens                        │  │  │
│  │  │  - Git history scanning                               │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  Container Scanning (Trivy)                           │  │  │
│  │  │  - OS package vulnerabilities                         │  │  │
│  │  │  - Application dependencies                           │  │  │
│  │  │  - Misconfiguration detection                         │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  └─────────────────────┬──────────────────────────────────────┘  │
│                        ▼                                          │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  STAGE 3: SBOM & Signing                                   │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  SBOM Generation (Syft)                               │  │  │
│  │  │  - CycloneDX / SPDX format                            │  │  │
│  │  │  - Upload to S3 / Artifact registry                   │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  Image Signing (Cosign)                               │  │  │
│  │  │  - Sign with private key / keyless                    │  │  │
│  │  │  - Attach SBOM attestation                            │  │  │
│  │  │  - Push signature to registry                         │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  └─────────────────────┬──────────────────────────────────────┘  │
│                        ▼                                          │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  STAGE 4: Deploy                                           │  │
│  │  - Update GitOps repository                                │  │
│  │  - Create ArgoCD Application                               │  │
│  │  - Trigger deployment (canary/blue-green)                  │  │
│  │  - Send notifications (Slack/Email)                        │  │
│  └────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                          ArgoCD (GitOps)                          │
│  - Continuous sync from Git repository                           │
│  - Progressive delivery (canary, blue-green)                     │
│  - Automated rollback on failure                                 │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                      Kubernetes Cluster                           │
│             (Production / Staging / Development)                  │
└──────────────────────────────────────────────────────────────────┘
```

## Pipeline Stages

### Stage 1: Build ([templates/github-actions/python-app.yml](templates/github-actions/python-app.yml))

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full git history for SBOM

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run tests
        run: |
          pytest tests/ \
            --cov=src \
            --cov-report=xml \
            --cov-report=html \
            --junitxml=junit.xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml

      - name: Build Docker image
        run: |
          docker build \
            --tag ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} \
            --tag ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest \
            --build-arg VERSION=${{ github.sha }} \
            --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
            .
```

### Stage 2: Security Scanning

#### SAST with SonarQube ([config/sonarqube/sonar-project.properties](config/sonarqube/sonar-project.properties))

```yaml
- name: SonarQube Scan
  uses: sonarsource/sonarqube-scan-action@master
  env:
    SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
    SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}
  with:
    args: >
      -Dsonar.projectKey=${{ github.repository_owner }}_${{ github.event.repository.name }}
      -Dsonar.python.coverage.reportPaths=coverage.xml
      -Dsonar.tests=tests/
      -Dsonar.sources=src/
      -Dsonar.qualitygate.wait=true

- name: Check Quality Gate
  run: |
    # Fail if quality gate fails
    if [ "${{ steps.sonarqube.outputs.quality-gate-status }}" != "PASSED" ]; then
      echo "Quality gate failed"
      exit 1
    fi
```

**SonarQube Rules**:
- Security Hotspots (injection, XSS, path traversal)
- Bugs (null pointer, resource leaks)
- Code Smells (complexity, duplication)
- Coverage threshold: 80%

#### Dependency Scanning

```yaml
- name: Python dependency check
  run: |
    pip install pip-audit
    pip-audit --require-hashes --requirement requirements.txt

- name: Node.js dependency check
  run: |
    npm audit --audit-level=high --production

- name: Go vulnerability check
  run: |
    go install golang.org/x/vuln/cmd/govulncheck@latest
    govulncheck ./...
```

#### Secret Detection

```yaml
- name: TruffleHog secret scanning
  uses: trufflesecurity/trufflehog@main
  with:
    path: ./
    base: ${{ github.event.repository.default_branch }}
    head: HEAD
    extra_args: --only-verified
```

**Detected Secrets**:
- API keys (AWS, GitHub, Stripe, etc.)
- Private keys (RSA, SSH, PGP)
- OAuth tokens
- Database credentials
- JWT secrets

#### Container Scanning (Trivy)

```yaml
- name: Run Trivy vulnerability scanner
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: '${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}'
    format: 'sarif'
    output: 'trivy-results.sarif'
    severity: 'CRITICAL,HIGH'
    exit-code: '1'  # Fail on CRITICAL/HIGH

- name: Upload Trivy results to GitHub Security tab
  uses: github/codeql-action/upload-sarif@v2
  with:
    sarif_file: 'trivy-results.sarif'
```

**Trivy Checks**:
- OS packages (Debian, Alpine, Red Hat)
- Language-specific dependencies (pip, npm, gem)
- IaC misconfigurations (Kubernetes, Terraform, Dockerfile)
- Secrets in layers

### Stage 3: SBOM & Signing

#### SBOM Generation ([scripts/generate-sbom.sh](scripts/generate-sbom.sh))

```bash
#!/bin/bash
set -e

IMAGE=$1
OUTPUT_DIR=${2:-./sbom}

# Install Syft
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin

# Generate SBOM in multiple formats
syft $IMAGE \
  -o cyclonedx-json=$OUTPUT_DIR/sbom.cyclonedx.json \
  -o spdx-json=$OUTPUT_DIR/sbom.spdx.json \
  -o table=$OUTPUT_DIR/sbom.txt

# Upload to S3
aws s3 cp $OUTPUT_DIR/sbom.cyclonedx.json \
  s3://$S3_SBOM_BUCKET/$IMAGE/sbom-$(date +%Y%m%d-%H%M%S).json

echo "SBOM generated and uploaded successfully"
```

**SBOM Contents** (CycloneDX):
```json
{
  "bomFormat": "CycloneDX",
  "specVersion": "1.4",
  "version": 1,
  "metadata": {
    "component": {
      "type": "container",
      "name": "my-app",
      "version": "1.2.3"
    }
  },
  "components": [
    {
      "type": "library",
      "name": "requests",
      "version": "2.31.0",
      "purl": "pkg:pypi/requests@2.31.0",
      "licenses": [{"license": {"id": "Apache-2.0"}}],
      "hashes": [{"alg": "SHA-256", "content": "..."}]
    }
  ],
  "dependencies": [...],
  "vulnerabilities": [...]
}
```

#### Image Signing (Cosign) ([scripts/sign-image.sh](scripts/sign-image.sh))

```bash
#!/bin/bash
set -e

IMAGE=$1
SBOM_PATH=$2

# Install Cosign
curl -sSfL https://github.com/sigstore/cosign/releases/download/v2.2.0/cosign-linux-amd64 \
  -o /usr/local/bin/cosign
chmod +x /usr/local/bin/cosign

# Option 1: Keyless signing (OIDC)
cosign sign --yes $IMAGE

# Option 2: Key-based signing
cosign sign --yes \
  --key /path/to/cosign.key \
  $IMAGE

# Attach SBOM as attestation
cosign attest --yes \
  --predicate $SBOM_PATH \
  --type cyclonedx \
  $IMAGE

# Verify signature
cosign verify \
  --certificate-identity-regexp ".*" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  $IMAGE

echo "Image signed and verified successfully"
```

**Signature Verification** (in production):
```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: app
    image: ghcr.io/myorg/myapp:v1.2.3
    # Pod will only start if signature is valid
    # Enforced by Kubernetes admission controller (Kyverno/Gatekeeper)
```

### Stage 4: Deploy (GitOps)

#### ArgoCD Application ([argocd/apps/python-app/application.yaml](argocd/apps/python-app/application.yaml))

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-app
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  source:
    repoURL: https://github.com/myorg/my-app-config.git
    targetRevision: HEAD
    path: k8s/overlays/production
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

#### Canary Deployment ([argocd/apps/python-app/rollout-canary.yaml](argocd/apps/python-app/rollout-canary.yaml))

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: my-app
spec:
  replicas: 10
  strategy:
    canary:
      steps:
      - setWeight: 10      # 10% traffic to canary
      - pause: {duration: 2m}
      - setWeight: 25      # 25% traffic
      - pause: {duration: 5m}
      - setWeight: 50      # 50% traffic
      - pause: {duration: 5m}
      - setWeight: 75      # 75% traffic
      - pause: {duration: 5m}
      # 100% rollout
      canaryService: my-app-canary
      stableService: my-app-stable
      trafficRouting:
        nginx:
          stableIngress: my-app-stable
      analysis:
        templates:
        - templateName: success-rate
        - templateName: latency
        args:
        - name: service-name
          value: my-app-canary
```

**Analysis Template** (Prometheus metrics):
```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
spec:
  metrics:
  - name: success-rate
    interval: 30s
    failureLimit: 3
    successCondition: result[0] >= 0.95
    provider:
      prometheus:
        address: http://prometheus:9090
        query: |
          sum(rate(http_requests_total{status=~"2..",service="{{args.service-name}}"}[5m]))
          /
          sum(rate(http_requests_total{service="{{args.service-name}}"}[5m]))
```

#### Blue-Green Deployment ([argocd/apps/python-app/rollout-bluegreen.yaml](argocd/apps/python-app/rollout-bluegreen.yaml))

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: my-app
spec:
  replicas: 3
  revisionHistoryLimit: 2
  strategy:
    blueGreen:
      activeService: my-app-active
      previewService: my-app-preview
      autoPromotionEnabled: false  # Manual approval required
      scaleDownDelaySeconds: 300   # Keep old version for 5min
      prePromotionAnalysis:
        templates:
        - templateName: smoke-tests
      postPromotionAnalysis:
        templates:
        - templateName: integration-tests
```

## Multi-Platform Support

### GitHub Actions ([templates/github-actions/](templates/github-actions/))

**Supported Languages**:
- Python ([python-app.yml](templates/github-actions/python-app.yml))
- Node.js ([node-app.yml](templates/github-actions/node-app.yml))
- Go ([go-app.yml](templates/github-actions/go-app.yml))

### GitLab CI ([templates/gitlab-ci/python-app.yml](templates/gitlab-ci/python-app.yml))

```yaml
stages:
  - build
  - test
  - scan
  - sign
  - deploy

variables:
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERTDIR: "/certs"

build:
  stage: build
  image: python:3.11
  script:
    - pip install -r requirements.txt
    - pytest tests/ --cov=src
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

security:sast:
  stage: scan
  image: sonarqube:latest
  script:
    - sonar-scanner \
        -Dsonar.projectKey=$CI_PROJECT_PATH_SLUG \
        -Dsonar.sources=src/

security:container_scanning:
  stage: scan
  image: aquasec/trivy:latest
  script:
    - trivy image --severity CRITICAL,HIGH $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

deploy:production:
  stage: deploy
  image: argoproj/argocd:latest
  script:
    - argocd app sync my-app --prune
  only:
    - main
```

## Security & Compliance

### SLSA Level 3 Compliance

**Requirements Met**:
1. ✅ **Source**: Git repository with branch protection
2. ✅ **Build**: Ephemeral, isolated build environment
3. ✅ **Provenance**: SBOM and build metadata attached
4. ✅ **Verification**: Signature verification at deploy time

**Build Provenance** (in-toto format):
```json
{
  "_type": "https://in-toto.io/Statement/v0.1",
  "subject": [{
    "name": "ghcr.io/myorg/myapp",
    "digest": {"sha256": "abc123..."}
  }],
  "predicateType": "https://slsa.dev/provenance/v0.2",
  "predicate": {
    "builder": {"id": "https://github.com/actions"},
    "buildType": "https://github.com/actions@v1",
    "invocation": {
      "configSource": {
        "uri": "git+https://github.com/myorg/myapp@refs/heads/main",
        "digest": {"sha1": "def456..."},
        "entryPoint": ".github/workflows/ci.yml"
      }
    },
    "metadata": {
      "buildStartedOn": "2024-12-01T20:00:00Z",
      "buildFinishedOn": "2024-12-01T20:05:30Z"
    },
    "materials": [...]
  }
}
```

### Policy Enforcement (OPA Gatekeeper)

```yaml
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequireSignedImages
metadata:
  name: require-cosign-signatures
spec:
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
    namespaces: ["production"]
  parameters:
    publicKey: |
      -----BEGIN PUBLIC KEY-----
      ...
      -----END PUBLIC KEY-----
```

## Monitoring & Notifications

### Slack Notifications

```yaml
- name: Notify Slack on success
  if: success()
  uses: slackapi/slack-github-action@v1
  with:
    payload: |
      {
        "text": "✅ Deployment successful",
        "blocks": [{
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": "*${{ github.repository }}* deployed to production\n*Commit*: ${{ github.sha }}\n*Author*: ${{ github.actor }}"
          }
        }]
      }
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### Metrics

**Pipeline Metrics** (Prometheus):
```
# Build duration
ci_build_duration_seconds{status="success"} 245
ci_build_duration_seconds{status="failure"} 180

# Deployment frequency
ci_deployments_total{environment="production"} 127

# Failure rate
ci_build_failures_total / ci_builds_total = 0.02

# Lead time for changes
ci_lead_time_seconds_sum / ci_lead_time_seconds_count = 3600
```

**DORA Metrics**:
- Deployment Frequency: Daily
- Lead Time for Changes: <1 hour
- Change Failure Rate: <5%
- Time to Restore Service: <1 hour

## Cost Estimation

**CI/CD Infrastructure** (per month):
- GitHub Actions (Enterprise): ~$200
- SonarQube server: ~$50
- ArgoCD (self-hosted): ~$30
- S3 SBOM storage: ~$5
- **Total**: ~$285/month

**Per-Pipeline Costs**:
- Small pipeline (5 min): ~$0.10
- Medium pipeline (15 min): ~$0.30
- Large pipeline (30 min): ~$0.60

---

**Last Updated**: December 2024
**Version**: 1.0.0
**Status**: Production Ready
