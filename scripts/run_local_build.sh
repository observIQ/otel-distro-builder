#!/bin/bash
set -e

# Default values
OUTPUT_DIR="$(pwd)/artifacts"
DOCKER_IMAGE="otel-distro-builder"

# Help message
usage() {
    echo "Usage: $0 -m <manifest_path> [-o <output_dir>]"
    echo
    echo "Build an OpenTelemetry Collector Distribution using local Docker"
    echo
    echo "Required arguments:"
    echo "  -m <manifest_path>          Path to manifest.yaml/yml file"
    echo
    echo "Optional arguments:"
    echo "  -o <output_dir>             Directory to store build artifacts (default: ./artifacts)"
    echo "  -h                          Show this help message"
    echo "  -s <boolean>                Run goreleaser in snapshot mode (default: true)"
    echo
    echo "Example:"
    echo "  $0 -m manifest.yaml -o /tmp/artifacts"
    exit 1
}

# Parse command line arguments
while getopts "m:o:s:h" opt; do
    case $opt in
    m) MANIFEST_PATH="$OPTARG" ;;
    o) OUTPUT_DIR="$OPTARG" ;;
    s) SNAPSHOT="$OPTARG" ;;
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
echo "Artifacts will be saved to: $OUTPUT_DIR"
echo

# Always build the latest version of the image
echo "Building Docker image..."
if ! (cd builder && docker build -t "$DOCKER_IMAGE" .); then
    echo "Error: Failed to build Docker image."
    exit 1
fi

if [ -z "$SNAPSHOT" ]; then
    SNAPSHOT="true"
fi

# Run the builder with mounted volumes
docker run \
    -v "$MANIFEST_PATH:/manifest.yaml:ro" \
    -v "$OUTPUT_DIR:/artifacts" \
    "$DOCKER_IMAGE" \
    --manifest /manifest.yaml \
    --snapshot "$SNAPSHOT"

echo "=== Build complete ==="
echo "Artifacts are available in: $OUTPUT_DIR"
