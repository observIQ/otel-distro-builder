#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🏗️  Building container...${NC}"
docker build -t otel-builder -f builder/Dockerfile .

# Debug information
echo -e "\n${YELLOW}Debug Information:${NC}"
echo "Workspace directory: ${PWD}"
echo "Full manifest path: /github/workspace/builder/tests/manifests/contrib-0.117.0.yaml"
echo "Local manifest path: ${PWD}/builder/tests/manifests/contrib-0.117.0.yaml"

# Check if manifest exists locally
if [ -f "${PWD}/builder/tests/manifests/contrib-0.117.0.yaml" ]; then
    echo -e "${GREEN}✅ Manifest file exists locally${NC}"
else
    echo -e "${YELLOW}⚠️  Warning: Manifest file not found locally${NC}"
    ls -la ${PWD}/builder/tests/manifests/
fi

echo -e "\n${BLUE}📝 Testing with test manifest...${NC}"
docker run \
  -v "${PWD}:/github/workspace" \
  -e INPUT_MANIFEST="/github/workspace/builder/tests/manifests/contrib-0.117.0.yaml" \
  -e INPUT_CREATE_RELEASE="true" \
  -e INPUT_UPLOAD_ARTIFACTS="true" \
  -e INPUT_PLATFORMS="linux/amd64" \
  -e INPUT_DEBUG="true" \
  -e INPUT_ARTIFACTS="/github/workspace/artifacts" \
  otel-builder \
  --manifest /github/workspace/builder/tests/manifests/contrib-0.117.0.yaml \
  --artifacts /github/workspace/artifacts

# Verify artifacts were created
if [ -d "artifacts" ]; then
  echo -e "\n${GREEN}✅ Artifacts created:${NC}"
  ls -la artifacts/
else
  echo -e "\n❌ No artifacts created!"
  exit 1
fi

echo -e "\n${GREEN}✅ Test complete!${NC}" 