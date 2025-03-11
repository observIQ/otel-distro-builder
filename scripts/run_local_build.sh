#!/bin/bash
set -e

# Default values
OUTPUT_DIR="$(pwd)/artifacts"

# Help message
usage() {
    echo "Usage: $0 -m <manifest_path> [-i <build_id>] [-o <output_dir>]"
    echo
    echo "Build an OpenTelemetry Collector using Google Cloud Build"
    echo
    echo "Required arguments:"
    echo "  -m <manifest_path>    Path to manifest.yaml/yml file"
    echo
    echo "Optional arguments:"
    echo "  -i <build_id>        Build ID for artifact storage (default: auto-generated)"
    echo "  -o <output_dir>      Directory to store build artifacts (default: ./artifacts)"
    echo "  -h                    Show this help message"
    echo
    echo "Example:"
    echo "  $0 -m manifest.yaml -i 9ae45f -o /tmp/artifacts"
    exit 1
}

# Parse command line arguments
while getopts "m:p:i:o:h" opt; do
    case $opt in
        m) MANIFEST_PATH="$OPTARG";;
        i) BUILD_ID="$OPTARG";;
        o) OUTPUT_DIR="$OPTARG";;
        h) usage;;
        ?) usage;;
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

# Build and run the builder container
docker build -t otel-builder -f "$(dirname "$0")/../builder/Dockerfile" "$(dirname "$0")/.." || {
    echo "Failed to build builder image"
    exit 1
}

# Run the builder with mounted volumes
docker run \
    -v "$MANIFEST_PATH:/manifest.yaml:ro" \
    -v "$OUTPUT_DIR:/artifacts" \
    otel-builder --manifest /manifest.yaml --artifacts /artifacts

echo "=== Build complete ==="
echo "Artifacts are available in: $OUTPUT_DIR"