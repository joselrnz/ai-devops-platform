#!/bin/bash
# Deployment script for Centralized Logging & Threat Analytics Platform

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deploying Logging & Threat Analytics${NC}"
echo -e "${GREEN}========================================${NC}"

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"
command -v kubectl >/dev/null 2>&1 || { echo -e "${RED}kubectl is required but not installed${NC}"; exit 1; }
command -v helm >/dev/null 2>&1 || { echo -e "${RED}helm is required but not installed${NC}"; exit 1; }

# Create namespace
echo -e "${YELLOW}Creating namespace...${NC}"
kubectl create namespace logging --dry-run=client -o yaml | kubectl apply -f -

# Add Helm repositories
echo -e "${YELLOW}Adding Helm repositories...${NC}"
helm repo add opensearch https://opensearch-project.github.io/helm-charts/
helm repo add fluent https://fluent.github.io/helm-charts
helm repo update

# Deploy OpenSearch
echo -e "${YELLOW}Deploying OpenSearch cluster...${NC}"
helm upgrade --install opensearch opensearch/opensearch \
  --namespace logging \
  -f helm/opensearch/values.yaml \
  --wait \
  --timeout 10m

# Wait for OpenSearch to be ready
echo -e "${YELLOW}Waiting for OpenSearch to be ready...${NC}"
kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/name=opensearch \
  -n logging \
  --timeout=600s

# Deploy Fluent Bit
echo -e "${YELLOW}Deploying Fluent Bit...${NC}"
helm upgrade --install fluent-bit fluent/fluent-bit \
  --namespace logging \
  -f helm/fluent-bit/values.yaml \
  --wait

# Deploy OpenSearch Dashboards
echo -e "${YELLOW}Deploying OpenSearch Dashboards...${NC}"
helm upgrade --install opensearch-dashboards opensearch/opensearch-dashboards \
  --namespace logging \
  --set opensearchHosts=http://opensearch-cluster-master:9200 \
  --wait

# Import dashboards
echo -e "${YELLOW}Importing dashboards...${NC}"
./scripts/import-dashboards.sh

# Deploy Sigma rules
echo -e "${YELLOW}Deploying Sigma rules...${NC}"
kubectl apply -f sigma-rules/ -n logging

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Access OpenSearch Dashboards:${NC}"
echo "kubectl port-forward -n logging svc/opensearch-dashboards 5601:5601"
echo "Then open: http://localhost:5601"
echo ""
echo -e "${YELLOW}OpenSearch API:${NC}"
echo "kubectl port-forward -n logging svc/opensearch-cluster-master 9200:9200"
echo ""
echo -e "${YELLOW}View logs:${NC}"
echo "kubectl logs -n logging -l app.kubernetes.io/name=fluent-bit -f"
