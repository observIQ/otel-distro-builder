#!/bin/bash
set -e

# Default values
OUTPUT_DIR="$(pwd)/artifacts"
OCB_VERSION="0.121.0"
SUPERVISOR_VERSION="0.122.0"
GO_VERSION="1.24.1"
DOCKER_IMAGE="otel-distro-builder"

# Help message
usage() {
    echo "Usage: $0 -m <manifest_path> [-i <build_id>] [-o <output_dir>] [-v <ocb_version>] [-g <go_version>]"
    echo
    echo "Build an OpenTelemetry Collector Distribution using local Docker"
    echo
    echo "Required arguments:"
    echo "  -m <manifest_path>          Path to manifest.yaml/yml file"
    echo
    echo "Optional arguments:"
    echo "  -o <output_dir>             Directory to store build artifacts (default: ./artifacts)"
    echo "  -v <ocb_version>            OpenTelemetry Collector Builder version (default: ${OCB_VERSION})"
    echo "  -s <supervisor_version>     OpenTelemetry Collector Supervisor version (default: ${SUPERVISOR_VERSION})"
    echo "  -g <go_version>             Go version to use (default: ${GO_VERSION})"
    echo "  -h                          Show this help message"
    echo
    echo "Example:"
    echo "  $0 -m manifest.yaml -i 9ae45f -o /tmp/artifacts -v 0.121.0 -s 0.122.0 -g 1.24.1"
    exit 1
}

# Parse command line arguments
while getopts "m:p:i:o:v:g:s:h" opt; do
    case $opt in
    m) MANIFEST_PATH="$OPTARG" ;;
    o) OUTPUT_DIR="$OPTARG" ;;
    v) OCB_VERSION="$OPTARG" ;;
    g) GO_VERSION="$OPTARG" ;;
    s) SUPERVISOR_VERSION="$OPTARG" ;;
    h) usage ;;
    ?) usage ;;
    esac
done

# Validate required arguments
if [ -z "$MANIFEST_PATH" ]; then
    echo "Error: Manifest path is required. Use -m <path>"
    usage
fi

if [ ! -f "$MANIFEST_PATH" ]; then
    echo "Error: Manifest file not found: $MANIFEST_PATH"
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Get absolute paths
MANIFEST_PATH=$(realpath "$MANIFEST_PATH")
OUTPUT_DIR=$(realpath "$OUTPUT_DIR")

echo "=== Running local build ==="
echo "Manifest: $MANIFEST_PATH"
echo "OCB Version: $OCB_VERSION"
echo "Supervisor Version: $SUPERVISOR_VERSION"
echo "Go Version: $GO_VERSION"
echo "Artifacts will be saved to: $OUTPUT_DIR"
echo

# Always build the latest version of the image
echo "Building Docker image..."
if ! (cd builder && docker build -t "$DOCKER_IMAGE" .); then
    echo "Error: Failed to build Docker image."
    exit 1
fi

# Run the builder with mounted volumes
docker run \
    -v "$MANIFEST_PATH:/manifest.yaml:ro" \
    -v "$OUTPUT_DIR:/artifacts" \
    "$DOCKER_IMAGE" \
    --manifest /manifest.yaml \
    --artifacts /artifacts \
    --ocb-version "$OCB_VERSION" \
    --go-version "$GO_VERSION" \
    --supervisor-version "$SUPERVISOR_VERSION" \
    --debug

echo "=== Build complete ==="
echo "Artifacts are available in: $OUTPUT_DIR"
