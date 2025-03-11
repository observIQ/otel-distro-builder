#!/bin/bash
set -e

# Get the repository root directory (parent of the directory containing this script)
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Default values
OUTPUT_DIR="$(pwd)/artifacts"
OCB_VERSION="0.121.0"
GO_VERSION="1.24.1"

# Help message
usage() {
    echo "Usage: $0 -m <manifest_path> [-i <build_id>] [-o <output_dir>] [-v <ocb_version>] [-g <go_version>]"
    echo
    echo "Build an OpenTelemetry Collector using Google Cloud Build"
    echo
    echo "Required arguments:"
    echo "  -m <manifest_path>    Path to manifest.yaml/yml file"
    echo
    echo "Optional arguments:"
    echo "  -i <build_id>        Build ID for artifact storage (default: auto-generated)"
    echo "  -o <output_dir>      Directory to store build artifacts (default: ./artifacts)"
    echo "  -v <ocb_version>     OpenTelemetry Collector Builder version (default: ${OCB_VERSION})"
    echo "  -g <go_version>      Go version to use (default: ${GO_VERSION})"
    echo "  -h                    Show this help message"
    echo
    echo "Example:"
    echo "  $0 -m manifest.yaml -i 9ae45f -o /tmp/artifacts -v 0.121.0 -g 1.24.1"
    exit 1
}

# Parse command line arguments
while getopts "m:p:i:o:v:g:h" opt; do
    case $opt in
        m) MANIFEST_PATH="$OPTARG";;
        i) BUILD_ID="$OPTARG";;
        o) OUTPUT_DIR="$OPTARG";;
        v) OCB_VERSION="$OPTARG";;
        g) GO_VERSION="$OPTARG";;
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
echo "OCB Version: $OCB_VERSION"
echo "Go Version: $GO_VERSION"
echo "Artifacts will be saved to: $OUTPUT_DIR"
echo

# Build and run the builder container
docker build -t otel-builder -f "$REPO_ROOT/builder/Dockerfile" "$REPO_ROOT" || {
    echo "Failed to build builder image"
    exit 1
}

# Run the builder with mounted volumes
docker run \
    -v "$MANIFEST_PATH:/manifest.yaml:ro" \
    -v "$OUTPUT_DIR:/artifacts" \
    otel-builder --manifest /manifest.yaml --artifacts /artifacts --ocb-version "$OCB_VERSION" --go-version "$GO_VERSION"

echo "=== Build complete ==="
echo "Artifacts are available in: $OUTPUT_DIR"