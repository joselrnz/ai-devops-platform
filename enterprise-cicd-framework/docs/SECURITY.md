# Security Best Practices

This document outlines security best practices for the Enterprise CI/CD Framework.

## Security Scanning Stages

### 1. Pre-Commit (Developer Workstation)

**Tools:**
- Pre-commit hooks with TruffleHog
- Local linting (pylint, eslint, golangci-lint)

**Setup:**

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/trufflesecurity/trufflehog
    rev: v3.63.0
    hooks:
      - id: trufflehog
        name: TruffleHog
        entry: trufflehog filesystem --directory .
        language: system
EOF

# Install hooks
pre-commit install
```

### 2. Pull Request (CI Pipeline)

**Checks performed:**
1. **SAST** - SonarQube static analysis
2. **Dependency scanning** - npm audit, pip-audit, govulncheck
3. **Secret detection** - TruffleHog with regex patterns
4. **License compliance** - Check for incompatible licenses
5. **Code coverage** - Ensure >80% coverage

**Quality Gates:**
- No CRITICAL or HIGH vulnerabilities
- Code coverage ≥ 80%
- No hardcoded secrets
- All tests passing
- Code quality rating ≥ B

### 3. Container Build

**Security measures:**
- Multi-stage builds to minimize image size
- Non-root user execution
- Minimal base images (alpine, distroless, scratch)
- No secrets in layers
- Signed commits only

**Dockerfile best practices:**

```dockerfile
# Use specific versions
FROM python:3.11-slim@sha256:abc123...

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Don't run as root
USER appuser

# Use COPY instead of ADD
COPY --chown=appuser:appuser . /app
```

### 4. Container Scanning

**Tools:**
- Trivy for vulnerability scanning
- Syft for SBOM generation
- Grype for additional vulnerability checks

**Configuration:**

```yaml
# .trivy.yaml
scan:
  security-checks: [vuln, config, secret]
  severity: [CRITICAL, HIGH]
exit-code: 1  # Fail on findings
ignore-unfixed: false  # Report all, even unfixed
```

**SBOM generation:**

```bash
# Generate multiple formats for compatibility
syft image:tag -o spdx-json > sbom.spdx.json
syft image:tag -o cyclonedx-json > sbom.cyclonedx.json
```

### 5. Image Signing

**Cosign (Sigstore):**

Keyless signing in CI/CD:
```bash
# Uses OIDC identity from GitHub/GitLab
cosign sign --yes \
  -a repo=$REPO \
  -a workflow=$WORKFLOW \
  $IMAGE
```

Key-based signing locally:
```bash
# Generate key pair once
cosign generate-key-pair

# Sign with private key
cosign sign --key cosign.key $IMAGE
```

**Verification:**

```yaml
# Kubernetes admission controller (Kyverno)
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-image-signature
spec:
  validationFailureAction: enforce
  rules:
  - name: verify-signature
    match:
      resources:
        kinds:
        - Pod
    verifyImages:
    - imageReferences:
      - "ghcr.io/myorg/*"
      attestors:
      - entries:
        - keyless:
            issuer: "https://token.actions.githubusercontent.com"
```

### 6. Runtime Security

**Admission Control:**
- Pod Security Standards (restricted)
- OPA/Gatekeeper policies
- Image signature verification

**Runtime monitoring:**
- Falco for runtime threat detection
- Network policies for isolation
- RBAC with least privilege

## Secret Management

### Never Commit Secrets

**Use .gitignore:**
```
# Secrets
*.key
*.pem
*.p12
.env
.env.local
secrets.yml
credentials.json
```

**Detection:**
```bash
# Scan history for secrets
trufflehog git file://. --since-commit main --only-verified

# Scan before commit
git diff --cached | trufflehog --no-update
```

### Store Secrets Securely

**GitHub:**
```bash
# Use GitHub Secrets
gh secret set SONAR_TOKEN --body "$TOKEN"
```

**Kubernetes:**
```bash
# Use Sealed Secrets or External Secrets Operator
kubectl create secret generic app-secrets \
  --from-literal=api-key=$API_KEY \
  --dry-run=client -o yaml | \
  kubeseal -o yaml > sealed-secret.yaml
```

**Vault:**
```bash
# HashiCorp Vault for centralized secrets
vault kv put secret/myapp/config \
  api_key=$API_KEY \
  db_password=$DB_PASSWORD
```

### Rotate Secrets Regularly

- API keys: Every 90 days
- Certificates: Before expiration
- Service account tokens: Every 180 days
- Database passwords: Every 90 days

## Dependency Management

### Pin Versions

**Python:**
```txt
# requirements.txt - pin exact versions
fastapi==0.109.0
uvicorn[standard]==0.27.0
```

**Node.js:**
```json
{
  "dependencies": {
    "express": "4.18.2"
  }
}
```

**Go:**
```go
// go.mod - use specific versions
require (
    github.com/gin-gonic/gin v1.9.1
)
```

### Scan Dependencies

```bash
# Python
pip-audit

# Node.js
npm audit
npm audit fix

# Go
govulncheck ./...
```

### Use Dependency Review

**GitHub:**
```yaml
# .github/workflows/dependency-review.yml
on: [pull_request]
jobs:
  dependency-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/dependency-review-action@v4
```

## Network Security

### Isolate Environments

```yaml
# Network Policy - deny all by default
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
---
# Allow specific traffic
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-app-traffic
spec:
  podSelector:
    matchLabels:
      app: myapp
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: nginx-ingress
    ports:
    - protocol: TCP
      port: 8000
```

### TLS Everywhere

```yaml
# Ingress with TLS
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - myapp.example.com
    secretName: myapp-tls
  rules:
  - host: myapp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: myapp
            port:
              number: 80
```

## Access Control

### Principle of Least Privilege

**Kubernetes RBAC:**

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: app-deployer
rules:
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "update", "patch"]
- apiGroups: [""]
  resources: ["services"]
  verbs: ["get", "list"]
```

### Service Accounts

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: myapp
---
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      serviceAccountName: myapp
      automountServiceAccountToken: true
```

## Compliance and Auditing

### Audit Logging

**GitHub Actions:**
```yaml
- name: Audit log
  run: |
    echo "User: ${{ github.actor }}"
    echo "Event: ${{ github.event_name }}"
    echo "Ref: ${{ github.ref }}"
    echo "SHA: ${{ github.sha }}"
```

**Kubernetes:**
```yaml
# Enable audit logging
apiVersion: v1
kind: Policy
rules:
- level: RequestResponse
  verbs: ["create", "update", "patch", "delete"]
  resources:
  - group: ""
    resources: ["secrets", "configmaps"]
```

### Compliance Scanning

**CIS Benchmarks:**
```bash
# Scan Kubernetes cluster
kube-bench run --targets master,node

# Scan container images
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image --compliance k8s-cis $IMAGE
```

## Incident Response

### Detection

1. Monitor security events
2. Alert on anomalies
3. Review audit logs daily
4. Track failed deployments

### Response

1. **Identify** the security issue
2. **Contain** the threat
3. **Eradicate** the vulnerability
4. **Recover** systems
5. **Post-mortem** analysis

### Rollback Procedure

```bash
# Automatic rollback on failed analysis
kubectl argo rollouts abort myapp

# Manual rollback to previous version
kubectl argo rollouts undo myapp

# Revert GitOps commit
git revert HEAD
git push origin main
```

## Security Checklist

### Before Deployment

- [ ] All dependencies scanned and updated
- [ ] No secrets in code or containers
- [ ] Image scanned with Trivy
- [ ] SBOM generated and attached
- [ ] Image signed with Cosign
- [ ] SonarQube quality gate passed
- [ ] All tests passing
- [ ] Security review completed

### Post-Deployment

- [ ] Verify signature in cluster
- [ ] Check runtime security (Falco)
- [ ] Monitor for anomalies
- [ ] Review access logs
- [ ] Verify network policies
- [ ] Test incident response

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [Kubernetes Security Best Practices](https://kubernetes.io/docs/concepts/security/)
- [SLSA Framework](https://slsa.dev/)
- [Sigstore Documentation](https://docs.sigstore.dev/)
