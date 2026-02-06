#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

# Default values
OUTPUT_DIR="$(pwd)/artifacts"
DOCKER_IMAGE="otel-distro-builder"

usage() {
    echo "Usage: $0 -m <manifest_path> [-o <output_dir>] [-p <platforms>] [-n <parallelism>] [version options]"
    echo
    echo "Build an OpenTelemetry Collector distribution using local Docker."
    echo "The image is built for the host architecture; use -p to set target platforms."
    echo
    echo "Required arguments:"
    echo "  -m <manifest_path>          Path to manifest.yaml/yml file"
    echo
    echo "Optional arguments:"
    echo "  -o <output_dir>             Directory for build artifacts (default: ./artifacts)"
    echo "  -p <platforms>             Comma-delimited GOOS/GOARCH (e.g. linux/arm64,linux/amd64,darwin/arm64)"
    echo "  -n <parallelism>           Parallel Goreleaser tasks (default: 4; use 1 to reduce memory)"
    echo "  -v <ocb_version>            OCB version (passed to builder)"
    echo "  -g <go_version>             Go version (passed to builder)"
    echo "  -s <supervisor_version>     Supervisor version (passed to builder)"
    echo "  -h                          Show this help message"
    echo
    echo "Examples:"
    echo "  $0 -m manifest.yaml -o /tmp/artifacts"
    echo "  $0 -m manifest.yaml -p linux/arm64,linux/amd64,darwin/arm64"
    echo "  $0 -m manifest.yaml -n 1 -o ./artifacts -v 0.121.0 -s 0.122.0 -g 1.24.0"
    exit 1
}

# Parse command line arguments
while getopts "m:o:p:n:v:g:s:h" opt; do
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

DOCKER_PLATFORM=$(get_docker_platform)

echo "=== Running local build ==="
echo "Manifest: $MANIFEST_PATH"
echo "Artifacts will be saved to: $OUTPUT_DIR"
echo "Docker platform: $DOCKER_PLATFORM"
[ -n "$PLATFORM" ] && echo "Target platform(s): $PLATFORM"
[ -n "$PARALLELISM" ] && echo "Parallelism: $PARALLELISM"
echo

echo "Building Docker image..."
if ! (cd builder && docker build --platform "$DOCKER_PLATFORM" -t "$DOCKER_IMAGE" .); then
    echo "Error: Failed to build Docker image."
    exit 1
fi

# Optional builder arguments
EXTRA_ARGS=()
[ -n "$PLATFORM" ] && EXTRA_ARGS+=(--platforms "$PLATFORM")
[ -n "$PARALLELISM" ] && EXTRA_ARGS+=(--parallelism "$PARALLELISM")
[ -n "$OCB_VERSION" ] && EXTRA_ARGS+=(--ocb-version "$OCB_VERSION")
[ -n "$GO_VERSION" ] && EXTRA_ARGS+=(--go-version "$GO_VERSION")
[ -n "$SUPERVISOR_VERSION" ] && EXTRA_ARGS+=(--supervisor-version "$SUPERVISOR_VERSION")

echo "Running builder..."
docker run --rm \
    --platform "$DOCKER_PLATFORM" \
    -v "$MANIFEST_PATH:/manifest.yaml:ro" \
    -v "$OUTPUT_DIR:/artifacts" \
    "$DOCKER_IMAGE" \
    --manifest /manifest.yaml \
    --artifacts /artifacts \
    "${EXTRA_ARGS[@]}"

echo "=== Build complete ==="
echo "Artifacts are available in: $OUTPUT_DIR"
