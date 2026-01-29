#!/bin/bash
set -e

# Default values for multi-arch build
OUTPUT_DIR="$(pwd)/artifacts"
DOCKER_IMAGE="otel-distro-builder"
# Default platforms: collector targets (GOOS/GOARCH). Image is built for first platform only.
DEFAULT_PLATFORMS="linux/amd64,darwin/amd64,linux/arm64,darwin/arm64"

# Help message
usage() {
    echo "Usage: $0 -m <manifest_path> [-o <output_dir>] [-p <platforms>] [-n <parallelism>]"
    echo
    echo "Build an OpenTelemetry Collector Distribution for multiple architectures."
    echo "The Docker image is built for the first platform; the collector binaries"
    echo "are built for all specified platforms (linux/amd64, linux/arm64, darwin/arm64, etc.)."
    echo
    echo "Required arguments:"
    echo "  -m <manifest_path>          Path to manifest.yaml/yml file"
    echo
    echo "Optional arguments:"
    echo "  -o <output_dir>             Directory to store build artifacts (default: ./artifacts)"
    echo "  -p <platforms>             Comma-delimited GOOS/GOARCH for collector binaries"
    echo "                              (default: linux/amd64,linux/arm64,darwin/arm64)"
    echo "  -n <parallelism>            Number of parallel Goreleaser build tasks (default: builder default 14; use 1 to reduce memory)"
    echo "  -v <ocb_version>            OCB version (passed to builder)"
    echo "  -g <go_version>             Go version (passed to builder)"
    echo "  -s <supervisor_version>     Supervisor version (passed to builder)"
    echo "  -h                          Show this help message"
    echo
    echo "Examples:"
    echo "  $0 -m manifest.yaml"
    echo "  $0 -m manifest.yaml -p linux/amd64,linux/arm64,darwin/arm64"
    echo "  $0 -m manifest.yaml -n 1 -o ./artifacts"
    echo "  $0 -m manifest.yaml -n 8 -o ./artifacts -v 0.121.0 -s 0.122.0 -g 1.24.1"
    exit 1
}

# Parse command line arguments
while getopts "m:p:i:o:n:v:g:s:h" opt; do
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

# Use host-native platform for Docker image to avoid QEMU emulation (which can cause OCB SIGSEGV on arm64)
# On Apple Silicon / arm64 hosts, building linux/amd64 would run under emulation and OCB may crash.
HOST_ARCH=$(uname -m)
case "$HOST_ARCH" in
    arm64|aarch64) IMAGE_PLATFORM="linux/arm64" ;;
    x86_64|amd64) IMAGE_PLATFORM="linux/amd64" ;;
    *)             IMAGE_PLATFORM="linux/arm64" ;;  # default to arm64 for other (e.g. arm)
esac

echo "=== Running local multi-arch build ==="
echo "Manifest: $MANIFEST_PATH"
echo "Artifacts will be saved to: $OUTPUT_DIR"
echo "Collector target platform(s): $PLATFORMS"
echo "Docker image platform: $IMAGE_PLATFORM"
[ -n "$PARALLELISM" ] && echo "Parallelism: $PARALLELISM"
echo

# Build Docker image for one linux platform (so we can run it locally)
echo "Building Docker image for platform: $IMAGE_PLATFORM..."
if ! (cd builder && docker build --platform "$IMAGE_PLATFORM" -t "$DOCKER_IMAGE" .); then
    echo "Error: Failed to build Docker image."
    exit 1
fi

# Run the builder: pass --platforms so it builds collector binaries for all requested platforms
echo "Running builder (collector targets: $PLATFORMS)..."
docker run --rm \
    --platform "$IMAGE_PLATFORM" \
    -v "$MANIFEST_PATH:/manifest.yaml:ro" \
    -v "$OUTPUT_DIR:/artifacts" \
    "$DOCKER_IMAGE" \
    --manifest /manifest.yaml \
    --artifacts /artifacts \
    --platforms "$PLATFORMS" \
    ${PARALLELISM:+"--parallelism $PARALLELISM"} \
    ${OCB_VERSION:+"--ocb-version $OCB_VERSION"} \
    ${GO_VERSION:+"--go-version $GO_VERSION"} \
    ${SUPERVISOR_VERSION:+"--supervisor-version $SUPERVISOR_VERSION"}

echo "=== Multi-arch build complete ==="
echo "Artifacts are available in: $OUTPUT_DIR"
