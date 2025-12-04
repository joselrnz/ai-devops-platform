#!/bin/bash
# Generate Software Bill of Materials (SBOM) with Syft
# Supports multiple output formats

set -e

# Configuration
IMAGE_NAME="${1:-myapp:latest}"
OUTPUT_DIR="${2:-./sbom}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Generating SBOM for ${IMAGE_NAME}${NC}"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Check if Syft is installed
if ! command -v syft &> /dev/null; then
    echo -e "${RED}Error: Syft is not installed${NC}"
    echo "Install with: curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin"
    exit 1
fi

# Generate SPDX JSON format (Software Package Data Exchange)
echo -e "${YELLOW}Generating SPDX JSON format...${NC}"
syft "$IMAGE_NAME" -o spdx-json > "$OUTPUT_DIR/sbom.spdx.json"
echo -e "${GREEN}✓ SPDX JSON saved to $OUTPUT_DIR/sbom.spdx.json${NC}"

# Generate CycloneDX JSON format
echo -e "${YELLOW}Generating CycloneDX JSON format...${NC}"
syft "$IMAGE_NAME" -o cyclonedx-json > "$OUTPUT_DIR/sbom.cyclonedx.json"
echo -e "${GREEN}✓ CycloneDX JSON saved to $OUTPUT_DIR/sbom.cyclonedx.json${NC}"

# Generate human-readable table
echo -e "${YELLOW}Generating human-readable table...${NC}"
syft "$IMAGE_NAME" -o table > "$OUTPUT_DIR/sbom.txt"
echo -e "${GREEN}✓ Table saved to $OUTPUT_DIR/sbom.txt${NC}"

# Generate Syft JSON (most detailed)
echo -e "${YELLOW}Generating Syft JSON format...${NC}"
syft "$IMAGE_NAME" -o syft-json > "$OUTPUT_DIR/sbom.syft.json"
echo -e "${GREEN}✓ Syft JSON saved to $OUTPUT_DIR/sbom.syft.json${NC}"

echo -e "${GREEN}✓ SBOM generation complete!${NC}"
echo -e "Files generated in: $OUTPUT_DIR"

# Summary
echo ""
echo -e "${YELLOW}Summary:${NC}"
syft "$IMAGE_NAME" -o table | head -20

echo ""
echo -e "${YELLOW}Total packages:${NC}"
syft "$IMAGE_NAME" -o json -q | jq '.artifacts | length'
