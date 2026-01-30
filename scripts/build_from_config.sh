#!/bin/bash
set -e

# Default values
OUTPUT_DIR="$(pwd)/artifacts"
OTEL_VERSION=""
DIST_NAME="otelcol-custom"
DIST_MODULE="github.com/custom/otelcol-distribution"
DIST_VERSION="1.0.0"
PLATFORM=""
PARALLELISM=""
NO_BINDPLANE=false

# Help message
usage() {
    echo "Usage: $0 -c <config_path> [options]"
    echo
    echo "Generate a manifest from a collector config.yaml and build the distribution"
    echo
    echo "Required arguments:"
    echo "  -c <config_path>            Path to collector config.yaml file"
    echo
    echo "Manifest options:"
    echo "  -v <otel_version>           Target OpenTelemetry version (default: latest from versions.yaml)"
    echo "  -n <dist_name>              Distribution name (default: otelcol-custom)"
    echo "  -m <dist_module>            Go module path (default: github.com/custom/otelcol-distribution)"
    echo "  -V <dist_version>           Distribution version (default: 1.0.0)"
    echo "  -B                          Exclude Bindplane/observIQ components (included by default)"
    echo
    echo "Build options:"
    echo "  -o <output_dir>             Directory to store build artifacts (default: ./artifacts)"
    echo "  -p <platform>               Target platform(s), comma-delimited (e.g. linux/amd64,linux/arm64)"
    echo "  -P <parallelism>            Number of parallel Goreleaser build tasks (default: 4)"
    echo
    echo "Other options:"
    echo "  -k                          Keep generated manifest file after build"
    echo "  -h                          Show this help message"
    echo
    echo "Examples:"
    echo "  # Build from config with defaults"
    echo "  $0 -c config.yaml"
    echo
    echo "  # Build with specific OTel version and output directory"
    echo "  $0 -c config.yaml -v 0.144.0 -o ./dist"
    echo
    echo "  # Build for multiple platforms"
    echo "  $0 -c config.yaml -p linux/amd64,linux/arm64"
    echo
    echo "  # Build with custom distribution name"
    echo "  $0 -c config.yaml -n my-collector -v 0.144.0"
    echo
    echo "  # Keep the generated manifest"
    echo "  $0 -c config.yaml -k"
    exit 1
}

KEEP_MANIFEST=false

# Parse command line arguments
while getopts "c:o:v:n:m:V:p:P:Bkh" opt; do
    case $opt in
    c) CONFIG_PATH="$OPTARG" ;;
    o) OUTPUT_DIR="$OPTARG" ;;
    v) OTEL_VERSION="$OPTARG" ;;
    n) DIST_NAME="$OPTARG" ;;
    m) DIST_MODULE="$OPTARG" ;;
    V) DIST_VERSION="$OPTARG" ;;
    p) PLATFORM="$OPTARG" ;;
    P) PARALLELISM="$OPTARG" ;;
    B) NO_BINDPLANE=true ;;
    k) KEEP_MANIFEST=true ;;
    h) usage ;;
    ?) usage ;;
    esac
done

# Validate required arguments
if [ -z "$CONFIG_PATH" ]; then
    echo "Error: Config path is required. Use -c <path>"
    usage
fi

if [ ! -f "$CONFIG_PATH" ]; then
    echo "Error: Config file not found: $CONFIG_PATH"
    exit 1
fi

# Get absolute paths
CONFIG_PATH=$(cd "$(dirname "$CONFIG_PATH")" && pwd)/$(basename "$CONFIG_PATH")
# For OUTPUT_DIR, create it first if needed then get realpath
mkdir -p "$OUTPUT_DIR"
OUTPUT_DIR=$(cd "$OUTPUT_DIR" && pwd)

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create temp manifest path or use persistent path
if [ "$KEEP_MANIFEST" = true ]; then
    MANIFEST_PATH="${OUTPUT_DIR}/manifest.yaml"
    mkdir -p "$OUTPUT_DIR"
else
    # Create temp file (works on both Linux and macOS)
    TEMP_DIR=$(mktemp -d)
    MANIFEST_PATH="${TEMP_DIR}/manifest.yaml"
    trap 'rm -rf "$TEMP_DIR"' EXIT
fi

echo "=== Build from Config ==="
echo "Config: $CONFIG_PATH"
echo "Output: $OUTPUT_DIR"
[ -n "$OTEL_VERSION" ] && echo "OTel Version: $OTEL_VERSION"
echo "Distribution: $DIST_NAME"
[ -n "$PLATFORM" ] && echo "Platform(s): $PLATFORM"
echo

# Step 1: Generate manifest
echo "=== Step 1: Generating Manifest ==="
GENERATE_ARGS="-c $CONFIG_PATH -o $MANIFEST_PATH"
GENERATE_ARGS="$GENERATE_ARGS -n $DIST_NAME"
GENERATE_ARGS="$GENERATE_ARGS -m $DIST_MODULE"
GENERATE_ARGS="$GENERATE_ARGS -V $DIST_VERSION"
[ -n "$OTEL_VERSION" ] && GENERATE_ARGS="$GENERATE_ARGS -v $OTEL_VERSION"
[ "$NO_BINDPLANE" = true ] && GENERATE_ARGS="$GENERATE_ARGS -B"

# shellcheck disable=SC2086
"$SCRIPT_DIR/generate_manifest.sh" $GENERATE_ARGS

if [ ! -f "$MANIFEST_PATH" ]; then
    echo "Error: Failed to generate manifest"
    exit 1
fi

echo
echo "=== Step 2: Building Distribution ==="

# Build Docker args
BUILD_ARGS="-m $MANIFEST_PATH -o $OUTPUT_DIR"
[ -n "$PLATFORM" ] && BUILD_ARGS="$BUILD_ARGS -p $PLATFORM"
[ -n "$PARALLELISM" ] && BUILD_ARGS="$BUILD_ARGS -n $PARALLELISM"
[ -n "$OTEL_VERSION" ] && BUILD_ARGS="$BUILD_ARGS -v $OTEL_VERSION"

# shellcheck disable=SC2086
"$SCRIPT_DIR/run_local_build.sh" $BUILD_ARGS

echo
echo "=== Build Complete ==="
echo "Artifacts: $OUTPUT_DIR"
[ "$KEEP_MANIFEST" = true ] && echo "Manifest: $MANIFEST_PATH"
