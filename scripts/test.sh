#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🏗️  Building container...${NC}"
docker build -t otel-builder .

echo -e "\n${BLUE}📝 Testing with test manifest...${NC}"
docker run \
  -v "${PWD}:/github/workspace" \
  -e INPUT_MANIFEST="test-manifest.yaml" \
  -e INPUT_CREATE_RELEASE="true" \
  -e INPUT_UPLOAD_ARTIFACTS="true" \
  -e INPUT_PLATFORMS="linux/amd64" \
  -e INPUT_DEBUG="true" \
  otel-builder

# Verify artifacts were created
if [ -d "artifacts" ]; then
  echo -e "\n${GREEN}✅ Artifacts created:${NC}"
  ls -la artifacts/
else
  echo -e "\n❌ No artifacts created!"
  exit 1
fi

echo -e "\n${GREEN}✅ Test complete!${NC}" 