#!/bin/bash
set -e

# Default values
OUTPUT_DIR="$(pwd)/artifacts"
DOCKER_IMAGE="otel-distro-builder"

# Help message
usage() {
    echo "Usage: $0 -m <manifest_path> [-o <output_dir>] [-p <platform>] [-n <parallelism>]"
    echo
    echo "Build an OpenTelemetry Collector Distribution using local Docker"
    echo
    echo "Required arguments:"
    echo "  -m <manifest_path>          Path to manifest.yaml/yml file"
    echo
    echo "Optional arguments:"
    echo "  -o <output_dir>             Directory to store build artifacts (default: ./artifacts)"
    echo "  -p <platform>               Docker build platform(s), comma-delimited (e.g. linux/arm64,linux/amd64)."
    echo "                              Use host platform to avoid emulation (e.g. linux/arm64 on Apple Silicon)."
    echo "  -n <parallelism>            Number of parallel Goreleaser build tasks (default: builder default 14; use 1 to reduce memory)"
    echo "  -v <ocb_version>            OCB version (passed to builder)"
    echo "  -g <go_version>             Go version (passed to builder)"
    echo "  -s <supervisor_version>     Supervisor version (passed to builder)"
    echo "  -h                          Show this help message"
    echo
    echo "Example:"
    echo "  $0 -m manifest.yaml -o /tmp/artifacts"
    echo "  $0 -m manifest.yaml -p linux/arm64,linux/amd64,darwin/arm64"
    echo "  $0 -m manifest.yaml -n 1 -o ./artifacts"
    echo "  $0 -m manifest.yaml -n 1 -o ./artifacts -v 0.121.0 -s 0.122.0 -g 1.24.1"
    exit 1
}

# Parse command line arguments
while getopts "m:p:i:o:n:v:g:s:h" opt; do
    case $opt in
    m) MANIFEST_PATH="$OPTARG" ;;
    o) OUTPUT_DIR="$OPTARG" ;;
    p) PLATFORM="$OPTARG" ;;
    n) PARALLELISM="$OPTARG" ;;
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
echo "Artifacts will be saved to: $OUTPUT_DIR"
[ -n "$PLATFORM" ] && echo "Platform(s): $PLATFORM"
[ -n "$PARALLELISM" ] && echo "Parallelism: $PARALLELISM"
echo

# Always build the latest version of the image
echo "Building Docker image..."
DOCKER_BUILD_CMD="docker build -t $DOCKER_IMAGE"
[ -n "$PLATFORM" ] && DOCKER_BUILD_CMD="$DOCKER_BUILD_CMD --platform $PLATFORM"
DOCKER_BUILD_CMD="$DOCKER_BUILD_CMD ."
if ! (cd builder && eval "$DOCKER_BUILD_CMD"); then
    echo "Error: Failed to build Docker image."
    exit 1
fi

# Run the builder with mounted volumes
docker run --rm \
    -v "$MANIFEST_PATH:/manifest.yaml:ro" \
    -v "$OUTPUT_DIR:/artifacts" \
    "$DOCKER_IMAGE" \
    ${PLATFORM:+"--platforms $PLATFORM"} \
    ${PARALLELISM:+"--parallelism $PARALLELISM"} \
    ${OCB_VERSION:+"--ocb-version $OCB_VERSION"} \
    ${GO_VERSION:+"--go-version $GO_VERSION"} \
    ${SUPERVISOR_VERSION:+"--supervisor-version $SUPERVISOR_VERSION"} \
    --manifest /manifest.yaml

echo "=== Build complete ==="
echo "Artifacts are available in: $OUTPUT_DIR"
