#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

# Default values for multi-arch build
OUTPUT_DIR="$(pwd)/artifacts"
DOCKER_IMAGE="otel-distro-builder"
# Default platforms: GOOS/GOARCH targets for collector binaries (image is built for host only)
DEFAULT_PLATFORMS="linux/amd64,darwin/amd64,linux/arm64,darwin/arm64"

usage() {
    echo "Usage: $0 -m <manifest_path> [-o <output_dir>] [-p <platforms>] [-n <parallelism>] [version options]"
    echo
    echo "Build an OpenTelemetry Collector distribution for multiple architectures."
    echo "The Docker image is built for the host architecture; collector binaries are"
    echo "built for all platforms given by -p."
    echo
    echo "Required arguments:"
    echo "  -m <manifest_path>          Path to manifest.yaml/yml file"
    echo
    echo "Optional arguments:"
    echo "  -o <output_dir>             Directory for build artifacts (default: ./artifacts)"
    echo "  -p <platforms>             Comma-delimited GOOS/GOARCH (default: $DEFAULT_PLATFORMS)"
    echo "  -n <parallelism>           Parallel Goreleaser tasks (default: 4; use 1 to reduce memory)"
    echo "  -v <ocb_version>            OCB version (passed to builder)"
    echo "  -g <go_version>             Go version (passed to builder)"
    echo "  -s <supervisor_version>     Supervisor version (passed to builder)"
    echo "  -h                          Show this help message"
    echo
    echo "Examples:"
    echo "  $0 -m manifest.yaml"
    echo "  $0 -m manifest.yaml -p linux/amd64,linux/arm64,darwin/arm64"
    echo "  $0 -m manifest.yaml -n 1 -o ./artifacts"
    echo "  $0 -m manifest.yaml -n 8 -o ./artifacts -v 0.121.0 -s 0.122.0 -g 1.24.0"
    exit 1
}

# Parse command line arguments
while getopts "m:o:p:n:v:g:s:h" opt; do
    case $opt in
    m) MANIFEST_PATH="$OPTARG" ;;
    o) OUTPUT_DIR="$OPTARG" ;;
    p) PLATFORMS="$OPTARG" ;;
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

# Use default platforms if not set
PLATFORMS="${PLATFORMS:-$DEFAULT_PLATFORMS}"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Get absolute paths
MANIFEST_PATH=$(realpath "$MANIFEST_PATH")
OUTPUT_DIR=$(realpath "$OUTPUT_DIR")

# Docker image is built for host architecture to avoid QEMU emulation (OCB can crash under emulation)
IMAGE_PLATFORM=$(get_docker_platform)

echo "=== Running local multi-arch build ==="
echo "Manifest: $MANIFEST_PATH"
echo "Artifacts will be saved to: $OUTPUT_DIR"
echo "Collector target platform(s): $PLATFORMS"
echo "Docker image platform: $IMAGE_PLATFORM"
[ -n "$PARALLELISM" ] && echo "Parallelism: $PARALLELISM"
echo

# Build Docker image for host platform
echo "Building Docker image for platform: $IMAGE_PLATFORM..."
if ! (cd builder && docker build --platform "$IMAGE_PLATFORM" -t "$DOCKER_IMAGE" .); then
    echo "Error: Failed to build Docker image."
    exit 1
fi

# Optional builder arguments (passed as separate args to avoid word-split issues)
EXTRA_ARGS=()
[ -n "$PARALLELISM" ] && EXTRA_ARGS+=(--parallelism "$PARALLELISM")
[ -n "$OCB_VERSION" ] && EXTRA_ARGS+=(--ocb-version "$OCB_VERSION")
[ -n "$GO_VERSION" ] && EXTRA_ARGS+=(--go-version "$GO_VERSION")
[ -n "$SUPERVISOR_VERSION" ] && EXTRA_ARGS+=(--supervisor-version "$SUPERVISOR_VERSION")

echo "Running builder (collector targets: $PLATFORMS)..."
docker run --rm \
    --platform "$IMAGE_PLATFORM" \
    -v "$MANIFEST_PATH:/manifest.yaml:ro" \
    -v "$OUTPUT_DIR:/artifacts" \
    "$DOCKER_IMAGE" \
    --manifest /manifest.yaml \
    --artifacts /artifacts \
    --platforms "$PLATFORMS" \
    "${EXTRA_ARGS[@]}"

echo "=== Multi-arch build complete ==="
echo "Artifacts are available in: $OUTPUT_DIR"
