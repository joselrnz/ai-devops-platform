#!/bin/bash
# Sign container image with Cosign (sigstore)
# Provides cryptographic proof of image authenticity

set -e

# Configuration
IMAGE="${1}"
KEY_FILE="${2:-cosign.key}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ -z "$IMAGE" ]; then
    echo -e "${RED}Error: Image name required${NC}"
    echo "Usage: $0 <image> [key-file]"
    echo "Example: $0 ghcr.io/myorg/myapp:v1.0.0"
    exit 1
fi

echo -e "${GREEN}Signing image: ${IMAGE}${NC}"

# Check if Cosign is installed
if ! command -v cosign &> /dev/null; then
    echo -e "${RED}Error: Cosign is not installed${NC}"
    echo "Install with: brew install cosign (macOS) or see https://docs.sigstore.dev/cosign/installation/"
    exit 1
fi

# Check if running in keyless mode (GitHub Actions, GitLab CI)
if [ -n "$GITHUB_ACTIONS" ] || [ -n "$GITLAB_CI" ]; then
    echo -e "${YELLOW}Running in CI/CD - using keyless signing${NC}"

    # Keyless signing (uses OIDC)
    cosign sign --yes "$IMAGE"

    echo -e "${GREEN}✓ Image signed with keyless signature${NC}"

    # Verify signature
    echo -e "${YELLOW}Verifying signature...${NC}"
    cosign verify \
        --certificate-identity-regexp=".*" \
        --certificate-oidc-issuer-regexp=".*" \
        "$IMAGE"

    echo -e "${GREEN}✓ Signature verified${NC}"

else
    # Key-based signing (local development)
    if [ ! -f "$KEY_FILE" ]; then
        echo -e "${YELLOW}Key file not found. Generating new key pair...${NC}"
        cosign generate-key-pair
        echo -e "${GREEN}✓ Key pair generated: cosign.key, cosign.pub${NC}"
    fi

    # Sign with private key
    echo -e "${YELLOW}Signing with private key...${NC}"
    cosign sign --key "$KEY_FILE" "$IMAGE"

    echo -e "${GREEN}✓ Image signed${NC}"

    # Verify signature with public key
    echo -e "${YELLOW}Verifying signature...${NC}"
    cosign verify --key "${KEY_FILE%.key}.pub" "$IMAGE"

    echo -e "${GREEN}✓ Signature verified${NC}"
fi

# Attach SBOM to signature (optional)
if [ -f "sbom.spdx.json" ]; then
    echo -e "${YELLOW}Attaching SBOM to signature...${NC}"
    cosign attach sbom --sbom sbom.spdx.json "$IMAGE"
    echo -e "${GREEN}✓ SBOM attached${NC}"
fi

echo -e "${GREEN}✓ Image signing complete!${NC}"
echo ""
echo -e "${YELLOW}To verify this image later:${NC}"
if [ -n "$GITHUB_ACTIONS" ] || [ -n "$GITLAB_CI" ]; then
    echo "cosign verify --certificate-identity-regexp='.*' --certificate-oidc-issuer-regexp='.*' $IMAGE"
else
    echo "cosign verify --key ${KEY_FILE%.key}.pub $IMAGE"
fi
