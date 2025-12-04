# Enterprise CI/CD Framework

Standardized CI/CD pipelines with security scanning (SAST/DAST), container hardening, SBOM generation, and GitOps deployment strategies.

## Overview

This framework provides production-ready CI/CD pipeline templates for modern DevOps workflows. It enforces security best practices, generates Software Bill of Materials (SBOM), signs artifacts, and deploys via GitOps with ArgoCD.

## Features

### 🔒 Security-First Pipelines
- **SAST (Static Application Security Testing)**: SonarQube integration
- **DAST (Dynamic Application Security Testing)**: OWASP ZAP scanning
- **Container Scanning**: Trivy vulnerability detection
- **Dependency Scanning**: Snyk, Dependabot
- **Secret Detection**: GitLeaks, TruffleHog
- **SBOM Generation**: Syft for software composition analysis
- **Image Signing**: Cosign with sigstore

### 🚀 Deployment Strategies
- **Blue-Green Deployment**: Zero-downtime releases
- **Canary Deployment**: Gradual rollout with traffic shifting
- **Rolling Updates**: Kubernetes-native updates
- **GitOps**: ArgoCD-driven declarative deployments
- **Automated Rollback**: Failure detection and auto-recovery

### 📦 Multi-Platform Support
- **GitHub Actions**: Cloud-native CI/CD
- **GitLab CI**: Self-hosted or GitLab.com
- **Jenkins**: Enterprise automation server
- **Azure DevOps**: Microsoft ecosystem
- **CircleCI**: Fast, scalable pipelines

### 🛠️ Language/Framework Templates
- **Python**: pytest, black, mypy, bandit
- **Node.js**: npm, jest, eslint, prettier
- **Go**: go test, golangci-lint, gosec
- **Java/Spring**: Maven, JUnit, SpotBugs
- **Docker**: Multi-stage builds, layer caching
- **Kubernetes**: Helm charts, Kustomize

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      DEVELOPER WORKFLOW                         │
│  1. Code → 2. Commit → 3. Push → 4. Pull Request                │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      CI PIPELINE (GitHub Actions / GitLab CI)   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  STAGE 1: BUILD & TEST                                   │   │
│  │  - Checkout code                                         │   │
│  │  - Install dependencies                                  │   │
│  │  - Run unit tests                                        │   │
│  │  - Generate coverage report                              │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  STAGE 2: SECURITY SCANNING                              │   │
│  │  - SAST (SonarQube)                                      │   │
│  │  - Dependency scanning (Snyk)                            │   │
│  │  - Secret detection (GitLeaks)                           │   │
│  │  - License compliance check                              │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  STAGE 3: DOCKER BUILD                                   │   │
│  │  - Build multi-stage Docker image                        │   │
│  │  - Scan image with Trivy                                 │   │
│  │  - Generate SBOM with Syft                               │   │
│  │  - Sign image with Cosign                                │   │
│  │  - Push to registry (GHCR, ECR, ACR)                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  STAGE 4: GITOPS DEPLOYMENT                              │   │
│  │  - Update ArgoCD application manifest                    │   │
│  │  - Create Git tag for release                            │   │
│  │  - Trigger ArgoCD sync                                   │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ARGOCD (GITOPS ENGINE)                     │
│  - Monitors Git repository for changes                          │
│  - Compares desired state (Git) vs actual state (Kubernetes)    │
│  - Auto-syncs or manual approval for deployment                 │
│  - Supports blue-green and canary strategies                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      KUBERNETES CLUSTER                         │
│  - Deploys application via Helm or Kustomize                    │
│  - Monitors health checks and rollout status                    │
│  - Auto-rollback on failure                                     │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Choose Your CI Platform

#### GitHub Actions
```bash
# Copy template to your repository
cp templates/github-actions/python-app.yml .github/workflows/ci.yml

# Customize for your project
# Edit: image name, registry, deployment target
```

#### GitLab CI
```bash
# Copy template to your repository
cp templates/gitlab-ci/python-app.yml .gitlab-ci.yml

# Configure GitLab CI/CD variables
# - DOCKER_REGISTRY
# - SONAR_TOKEN
# - ARGOCD_TOKEN
```

### 2. Configure Security Scanning

#### SonarQube (SAST)
```yaml
# sonar-project.properties
sonar.projectKey=my-project
sonar.organization=my-org
sonar.sources=src
sonar.tests=tests
sonar.python.coverage.reportPaths=coverage.xml
```

#### Trivy (Container Scanning)
```yaml
# .trivyignore (optional)
# Ignore specific CVEs
CVE-2023-12345
```

### 3. Set Up GitOps with ArgoCD

```bash
# Install ArgoCD CLI
brew install argocd

# Login to ArgoCD
argocd login argocd.example.com

# Create application
argocd app create my-app \
  --repo https://github.com/myorg/my-repo \
  --path argocd/apps/my-app \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace production
```

## Pipeline Templates

### Python Application

**GitHub Actions**: `templates/github-actions/python-app.yml`

Features:
- Python 3.11+ support
- pytest with coverage
- Black, Ruff, MyPy linting
- Bandit security scanning
- Docker build & push
- ArgoCD deployment

**GitLab CI**: `templates/gitlab-ci/python-app.yml`

Features:
- Multi-stage pipeline
- Parallel job execution
- Cache optimization
- GitLab Container Registry

### Node.js Application

**GitHub Actions**: `templates/github-actions/nodejs-app.yml`

Features:
- npm/yarn/pnpm support
- Jest testing
- ESLint + Prettier
- npm audit for vulnerabilities
- Docker build with node_modules caching

### Go Application

**GitHub Actions**: `templates/github-actions/go-app.yml`

Features:
- Go modules caching
- golangci-lint
- gosec security scanning
- Multi-arch Docker builds (amd64, arm64)

## Security Scanning Tools

### SAST (Static Analysis)

#### SonarQube
```yaml
- name: SonarQube Scan
  uses: sonarsource/sonarqube-scan-action@master
  env:
    SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
    SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}
```

**Configuration**: See `config/sonarqube/sonar-project.properties`

### Container Scanning

#### Trivy
```yaml
- name: Run Trivy vulnerability scanner
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: 'myapp:latest'
    format: 'sarif'
    output: 'trivy-results.sarif'
    severity: 'CRITICAL,HIGH'
```

**Configuration**: See `config/trivy/trivy.yaml`

### Dependency Scanning

#### Snyk
```yaml
- name: Run Snyk to check for vulnerabilities
  uses: snyk/actions/node@master
  env:
    SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
```

### Secret Detection

#### GitLeaks
```yaml
- name: Gitleaks scan
  uses: gitleaks/gitleaks-action@v2
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## SBOM Generation

### Syft (Anchore)

```yaml
- name: Generate SBOM
  uses: anchore/sbom-action@v0
  with:
    image: myapp:latest
    format: spdx-json
    output-file: sbom.spdx.json

- name: Upload SBOM
  uses: actions/upload-artifact@v3
  with:
    name: sbom
    path: sbom.spdx.json
```

**Why SBOM?**
- Compliance (Executive Order 14028)
- Vulnerability tracking
- License compliance
- Supply chain security

## Image Signing

### Cosign (sigstore)

```yaml
- name: Install Cosign
  uses: sigstore/cosign-installer@v3

- name: Sign container image
  run: |
    cosign sign --key cosign.key \
      ghcr.io/myorg/myapp:${{ github.sha }}
  env:
    COSIGN_PASSWORD: ${{ secrets.COSIGN_PASSWORD }}

- name: Verify signature
  run: |
    cosign verify --key cosign.pub \
      ghcr.io/myorg/myapp:${{ github.sha }}
```

**Generate Keys**:
```bash
cosign generate-key-pair
# Stores: cosign.key, cosign.pub
```

## Deployment Strategies

### Blue-Green Deployment

```yaml
# argocd/apps/myapp/blue-green.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: myapp
spec:
  strategy:
    blueGreen:
      activeService: myapp-active
      previewService: myapp-preview
      autoPromotionEnabled: false
      scaleDownDelaySeconds: 30
```

**Workflow**:
1. Deploy new version (green)
2. Test green environment
3. Switch traffic to green
4. Scale down blue

### Canary Deployment

```yaml
# argocd/apps/myapp/canary.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: myapp
spec:
  strategy:
    canary:
      steps:
      - setWeight: 20
      - pause: {duration: 5m}
      - setWeight: 50
      - pause: {duration: 5m}
      - setWeight: 80
      - pause: {duration: 5m}
```

**Workflow**:
1. Deploy canary (20% traffic)
2. Monitor metrics
3. Gradually increase to 50%, 80%, 100%
4. Rollback if errors detected

## ArgoCD Integration

### Application Manifest

```yaml
# argocd/apps/myapp/application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/myorg/myapp
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
```

### Auto-Sync vs Manual Approval

**Auto-Sync** (recommended for dev/staging):
```yaml
syncPolicy:
  automated:
    prune: true
    selfHeal: true
```

**Manual Approval** (recommended for production):
```yaml
syncPolicy:
  automated: null  # Disable auto-sync
```

## Best Practices

### 1. **Fail Fast**
- Run fastest tests first (unit tests before integration)
- Fail build on security vulnerabilities (CRITICAL/HIGH)
- Cache dependencies aggressively

### 2. **Security Gates**
- **No secrets in code**: Use GitLeaks pre-commit hook
- **Vulnerability threshold**: Fail on CRITICAL, warn on HIGH
- **SBOM required**: Must generate and upload SBOM
- **Signed images only**: All production images must be signed

### 3. **Performance Optimization**
- **Docker layer caching**: Cache build layers between runs
- **Dependency caching**: Cache npm_modules, pip packages, Go modules
- **Parallel jobs**: Run linting, testing, security scans in parallel
- **Conditional workflows**: Skip unnecessary steps (e.g., skip Docker build for docs-only changes)

### 4. **GitOps Principles**
- **Git is source of truth**: All config in Git
- **Declarative**: Define desired state, not imperative steps
- **Automated sync**: ArgoCD auto-syncs on Git changes
- **Versioned**: Every deployment is a Git commit

## Cost Optimization

### GitHub Actions

- **Self-hosted runners**: Free, but requires infrastructure
- **Public repos**: Unlimited minutes
- **Private repos**: 2,000 minutes/month (free tier)

**Optimization Tips**:
```yaml
# Use concurrency to cancel old runs
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

# Skip duplicate work
if: github.event_name != 'pull_request' || github.event.pull_request.head.repo.full_name != github.repository
```

### GitLab CI

- **Shared runners**: 400 minutes/month (free tier)
- **Self-hosted runners**: Unlimited

### Docker Registry

- **GHCR (GitHub Container Registry)**: Free for public images
- **ECR (AWS)**: $0.10/GB/month storage
- **DockerHub**: Free for public images (rate limited)

## Monitoring & Observability

### Pipeline Metrics

Track:
- Build success rate
- Build duration (P50, P95)
- Security scan findings over time
- Deployment frequency
- Mean time to recovery (MTTR)

### Integration with Observability Stack

```yaml
# Send metrics to Prometheus
- name: Report metrics
  run: |
    echo "build_duration_seconds $(date +%s - $START_TIME)" | curl --data-binary @- \
      http://prometheus-pushgateway:9091/metrics/job/ci-pipeline
```

## Examples

See `examples/` directory for complete working examples:

- [Python FastAPI app](examples/python-fastapi/)
- [Node.js Express app](examples/nodejs-express/)
- [Go microservice](examples/go-microservice/)
- [Java Spring Boot app](examples/java-springboot/)

## Contributing

See CONTRIBUTING.md

## License

MIT License - See LICENSE file

---

**Part of the AI-Augmented DevOps Platform Portfolio**
**Project 4 of 7** | [← Project 3](../k8s-agentops-platform) | [Project 5 →](../logging-threat-analytics)
