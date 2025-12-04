# Integration Guide

This guide explains how to integrate the Enterprise CI/CD Framework into your projects.

## Table of Contents

1. [GitHub Actions Integration](#github-actions-integration)
2. [GitLab CI Integration](#gitlab-ci-integration)
3. [ArgoCD Setup](#argocd-setup)
4. [Security Scanning Configuration](#security-scanning-configuration)
5. [Monitoring and Observability](#monitoring-and-observability)

## GitHub Actions Integration

### Prerequisites

- GitHub repository with admin access
- Container registry (GitHub Container Registry, Docker Hub, or private registry)
- Kubernetes cluster with ArgoCD installed
- SonarQube instance (optional)

### Step 1: Set Up Secrets

Configure the following secrets in your GitHub repository (Settings → Secrets and variables → Actions):

```bash
# Required secrets
SONAR_TOKEN=your-sonarqube-token
SONAR_HOST_URL=https://sonarqube.example.com
GITOPS_TOKEN=github-token-with-repo-access
SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Optional secrets (if using private registry)
DOCKER_USERNAME=your-username
DOCKER_PASSWORD=your-password
```

### Step 2: Copy Pipeline Template

Choose the appropriate template for your language:

**Python:**
```bash
cp templates/github-actions/python-app.yml .github/workflows/ci-cd.yml
```

**Node.js:**
```bash
cp templates/github-actions/node-app.yml .github/workflows/ci-cd.yml
```

**Go:**
```bash
cp templates/github-actions/go-app.yml .github/workflows/ci-cd.yml
```

### Step 3: Customize Pipeline

Edit `.github/workflows/ci-cd.yml` and update:

```yaml
env:
  REGISTRY: ghcr.io  # Change to your registry
  IMAGE_NAME: ${{ github.repository }}
  # Language version
  PYTHON_VERSION: '3.11'  # or NODE_VERSION, GO_VERSION
```

### Step 4: Add Dockerfile

Copy the example Dockerfile for your language:

```bash
cp examples/python-app/Dockerfile .
```

Customize as needed for your application.

### Step 5: Configure SonarQube

Copy the SonarQube configuration:

```bash
cp config/sonarqube/sonar-project.properties .
```

Update with your project details:

```properties
sonar.projectKey=your-project-key
sonar.organization=your-org
sonar.projectName=Your Project Name
```

### Step 6: Test Pipeline

Push to your repository:

```bash
git add .github/workflows/ci-cd.yml Dockerfile sonar-project.properties
git commit -m "Add CI/CD pipeline"
git push origin main
```

Check the Actions tab in GitHub to see your pipeline running.

## GitLab CI Integration

### Prerequisites

- GitLab repository
- Container registry configured in GitLab
- Kubernetes cluster with ArgoCD
- GitLab Runner with Docker executor

### Step 1: Set Up CI/CD Variables

Configure in GitLab (Settings → CI/CD → Variables):

```
SONAR_TOKEN=your-token
SONAR_HOST_URL=https://sonarqube.example.com
GITOPS_TOKEN=gitlab-token
SLACK_WEBHOOK=webhook-url
DOCKER_AUTH_CONFIG={"auths":{...}}  # For private registries
```

### Step 2: Copy Pipeline Template

```bash
cp templates/gitlab-ci/python-app.yml .gitlab-ci.yml
```

### Step 3: Enable GitLab Security Features

The pipeline includes GitLab's security templates:

- Dependency Scanning
- SAST (Static Application Security Testing)
- Secret Detection
- Container Scanning

These are automatically enabled and will appear in the Security Dashboard.

### Step 4: Configure Registry

Update `.gitlab-ci.yml`:

```yaml
variables:
  IMAGE_TAG: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
  # Or use external registry
  # IMAGE_TAG: docker.io/username/app:$CI_COMMIT_SHORT_SHA
```

### Step 5: Test Pipeline

```bash
git add .gitlab-ci.yml
git commit -m "Add CI/CD pipeline"
git push origin main
```

## ArgoCD Setup

### Prerequisites

- ArgoCD installed in Kubernetes cluster
- GitOps repository for manifests
- Source code repository

### Step 1: Create GitOps Repository

Create a separate repository for Kubernetes manifests:

```bash
mkdir myapp-gitops
cd myapp-gitops
git init
```

Structure:

```
myapp-gitops/
├── base/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── kustomization.yaml
└── overlays/
    ├── dev/
    │   └── kustomization.yaml
    └── prod/
        └── kustomization.yaml
```

### Step 2: Copy ArgoCD Application Manifest

```bash
cp argocd/apps/python-app/application.yaml myapp-gitops/argocd-app.yaml
```

Update the manifest:

```yaml
spec:
  source:
    repoURL: https://github.com/yourorg/myapp-gitops
    targetRevision: main
    path: overlays/prod
  destination:
    server: https://kubernetes.default.svc
    namespace: myapp
```

### Step 3: Apply to ArgoCD

```bash
kubectl apply -f argocd-app.yaml -n argocd
```

### Step 4: Set Up Deployment Strategy

**For Canary Deployments:**

```bash
cp argocd/apps/python-app/rollout-canary.yaml myapp-gitops/base/rollout.yaml
```

**For Blue-Green Deployments:**

```bash
cp argocd/apps/python-app/rollout-bluegreen.yaml myapp-gitops/base/rollout.yaml
```

Install Argo Rollouts:

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
```

### Step 5: Configure CI/CD to Update GitOps Repo

In your CI/CD pipeline (already included in templates), the deploy job will:

1. Clone the GitOps repository
2. Update the image tag using Kustomize
3. Commit and push changes
4. ArgoCD automatically syncs

## Security Scanning Configuration

### Trivy (Container Scanning)

Configure Trivy for your needs:

```bash
cp config/trivy/trivy.yaml .trivy.yaml
```

Customize severity levels and exclusions:

```yaml
scan:
  severity: [CRITICAL, HIGH, MEDIUM, LOW]
vulnerability:
  ignore:
    - id: CVE-2023-12345
      reason: "False positive - not applicable to our use case"
```

### SonarQube (SAST)

Quality gate configuration in `sonar-project.properties`:

```properties
# Coverage requirements
sonar.coverage.exclusions=**/*_test.py,**/tests/**

# Quality gate thresholds (configured in SonarQube UI)
# - Code Coverage > 80%
# - Duplicated Lines < 3%
# - Maintainability Rating = A
# - Reliability Rating = A
# - Security Rating = A
```

### Secret Detection

The pipeline includes TruffleHog for secret detection. Configure `.trufflehog.yaml`:

```yaml
rules:
  - name: custom-api-key
    regex: 'API_KEY=[a-zA-Z0-9]{32,}'
    tags:
      - api-key
      - credentials
```

## Monitoring and Observability

### Prometheus Metrics

Applications should expose metrics on `/metrics`:

**Python (FastAPI):**
```python
from prometheus_client import Counter, Histogram, make_asgi_app

app.mount("/metrics", make_asgi_app())
```

**Node.js (Express):**
```javascript
const promClient = require('prom-client');
const register = new promClient.Registry();
promClient.collectDefaultMetrics({ register });

app.get('/metrics', (req, res) => {
  res.set('Content-Type', register.contentType);
  res.end(register.metrics());
});
```

**Go:**
```go
import "github.com/prometheus/client_golang/prometheus/promhttp"

http.Handle("/metrics", promhttp.Handler())
```

### Service Monitor

Create a ServiceMonitor for Prometheus:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: myapp
spec:
  selector:
    matchLabels:
      app: myapp
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
```

### Grafana Dashboards

Import dashboards for your application:

1. Request metrics (RED method: Rate, Errors, Duration)
2. Resource utilization (CPU, Memory, Network)
3. Deployment tracking (canary progress, rollout status)

### Health Checks

Implement health and readiness probes:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

## Testing the Integration

### Local Testing

**Build and scan locally:**

```bash
# Build image
docker build -t myapp:test .

# Scan with Trivy
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image myapp:test

# Generate SBOM
./scripts/generate-sbom.sh myapp:test

# Sign image (local key-based)
./scripts/sign-image.sh myapp:test
```

### Pipeline Testing

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/test-pipeline
   ```

2. **Make a small change and push:**
   ```bash
   echo "# Test" >> README.md
   git add README.md
   git commit -m "Test CI/CD pipeline"
   git push origin feature/test-pipeline
   ```

3. **Open a Pull Request**
   - Pipeline runs all checks except deploy
   - Review security scan results
   - Check quality gate status

4. **Merge to main:**
   - Full pipeline runs including deployment
   - Image is built, scanned, signed, and pushed
   - GitOps repository is updated
   - ArgoCD syncs to Kubernetes

### Verify Deployment

```bash
# Check ArgoCD application status
argocd app get myapp

# Watch rollout progress
kubectl argo rollouts get rollout myapp --watch

# Check pod status
kubectl get pods -l app=myapp

# View logs
kubectl logs -l app=myapp --tail=100 -f
```

## Troubleshooting

### Common Issues

**Pipeline fails at security scan:**
- Check if vulnerabilities are CRITICAL/HIGH
- Review Trivy output in job logs
- Add exceptions to `.trivy.yaml` if needed (with justification)

**SonarQube quality gate fails:**
- Check coverage threshold
- Review code smells and duplications
- Fix issues or adjust quality gate in SonarQube

**Image signing fails:**
- Ensure COSIGN_PASSWORD is set (if using key-based)
- For keyless: verify OIDC token is available
- Check Cosign is properly installed

**ArgoCD doesn't sync:**
- Verify GitOps repository access
- Check Application manifest is correct
- Review ArgoCD logs: `kubectl logs -n argocd deployment/argocd-application-controller`

**Rollout stuck:**
- Check analysis results: `kubectl argo rollouts status myapp`
- Verify Prometheus is accessible
- Review AnalysisRun: `kubectl get analysisrun`

## Next Steps

1. Set up branch protection rules
2. Configure notification channels (Slack, email, PagerDuty)
3. Create runbooks for common deployment scenarios
4. Implement automated rollback procedures
5. Set up log aggregation and alerting
6. Schedule regular security reviews

## Resources

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Argo Rollouts Documentation](https://argoproj.github.io/argo-rollouts/)
- [Trivy Documentation](https://aquasecurity.github.io/trivy/)
- [SonarQube Documentation](https://docs.sonarqube.org/)
- [Cosign Documentation](https://docs.sigstore.dev/cosign/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitLab CI Documentation](https://docs.gitlab.com/ee/ci/)
