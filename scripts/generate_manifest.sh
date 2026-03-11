#!/bin/bash
set -e

# Default values
ARTIFACTS_DIR=""
OTEL_VERSION=""
BINDPLANE_VERSION=""
DIST_NAME="otelcol-custom"
DIST_MODULE="github.com/custom/otelcol-distribution"
DIST_VERSION="1.0.0"
USE_DOCKER=false
DOCKER_IMAGE="otel-distro-builder"
NO_BINDPLANE=false

# Help message
usage() {
    echo "Usage: $0 -c <config_path> [-a <artifacts_dir>] [options]"
    echo
    echo "Generate an OCB manifest from an existing OpenTelemetry Collector config.yaml"
    echo "The manifest is always written to <artifacts_dir>/manifest.yaml."
    echo
    echo "Required arguments:"
    echo "  -c <config_path>            Path to collector config.yaml file"
    echo
    echo "Optional arguments:"
    echo "  -a <artifacts_dir>          Artifacts directory (default: ./artifacts)"
    echo "  -v <otel_version>           Target OpenTelemetry version (default: latest from versions.yaml)"
    echo "  -n <dist_name>              Distribution name (default: otelcol-custom)"
    echo "  -m <dist_module>            Go module path (default: github.com/custom/otelcol-distribution)"
    echo "  -V <dist_version>           Distribution version (default: 1.0.0)"
    echo "  -b <bindplane_version>      Target Bindplane version (default: latest from bindplane_components.yaml)"
    echo "  -B                          Exclude Bindplane components (included by default)"
    echo "  -d                          Use Docker instead of local Python"
    echo "  -h                          Show this help message"
    echo
    echo "Examples:"
    echo "  # Generate manifest to default ./artifacts/manifest.yaml"
    echo "  $0 -c config.yaml"
    echo
    echo "  # Generate manifest to a custom artifacts directory"
    echo "  $0 -c config.yaml -a ./out"
    echo
    echo "  # Generate manifest with specific OTel version"
    echo "  $0 -c config.yaml -v 0.144.0"
    echo
    echo "  # Generate manifest with custom distribution name"
    echo "  $0 -c config.yaml -n my-collector -m github.com/myorg/collector"
    echo
    echo "  # Generate manifest without Bindplane components"
    echo "  $0 -c config.yaml -B"
    echo
    echo "  # Use Docker instead of local Python"
    echo "  $0 -c config.yaml -d"
    exit 1
}

# Parse command line arguments
while getopts "c:a:v:b:n:m:V:Bdh" opt; do
    case $opt in
    c) CONFIG_PATH="$OPTARG" ;;
    a) ARTIFACTS_DIR="$OPTARG" ;;
    v) OTEL_VERSION="$OPTARG" ;;
    b) BINDPLANE_VERSION="$OPTARG" ;;
    n) DIST_NAME="$OPTARG" ;;
    m) DIST_MODULE="$OPTARG" ;;
    V) DIST_VERSION="$OPTARG" ;;
    B) NO_BINDPLANE=true ;;
    d) USE_DOCKER=true ;;
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

# Get absolute path for config
CONFIG_PATH=$(realpath "$CONFIG_PATH")

# Get script directory (for finding the builder module)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== Generate Manifest from Config ==="
echo "Config: $CONFIG_PATH"
[ -n "$ARTIFACTS_DIR" ] && echo "Artifacts: $ARTIFACTS_DIR"
[ -n "$OTEL_VERSION" ] && echo "OTel Version: $OTEL_VERSION"
echo "Distribution: $DIST_NAME"
echo

if [ "$USE_DOCKER" = true ]; then
    # Build Docker args
    DOCKER_ARGS="--from-config /config.yaml --generate-only"
    DOCKER_ARGS="$DOCKER_ARGS --dist-name $DIST_NAME"
    DOCKER_ARGS="$DOCKER_ARGS --dist-module $DIST_MODULE"
    DOCKER_ARGS="$DOCKER_ARGS --dist-version $DIST_VERSION"
    [ -n "$OTEL_VERSION" ] && DOCKER_ARGS="$DOCKER_ARGS --otel-version $OTEL_VERSION"
    [ -n "$BINDPLANE_VERSION" ] && DOCKER_ARGS="$DOCKER_ARGS --bindplane-version $BINDPLANE_VERSION"
    [ "$NO_BINDPLANE" = true ] && DOCKER_ARGS="$DOCKER_ARGS --no-bindplane"

    # Resolve artifacts dir for Docker volume mount
    if [ -n "$ARTIFACTS_DIR" ]; then
        mkdir -p "$ARTIFACTS_DIR"
        ARTIFACTS_DIR=$(cd "$ARTIFACTS_DIR" && pwd)
    else
        mkdir -p artifacts
        ARTIFACTS_DIR=$(cd artifacts && pwd)
    fi
    DOCKER_ARGS="$DOCKER_ARGS --artifacts /artifacts"

    # Build Docker image if needed
    echo "Building Docker image..."
    DOCKER_PLATFORM="linux/$(uname -m | sed 's/x86_64/amd64/' | sed 's/aarch64/arm64/')"
    (cd "$PROJECT_ROOT/builder" && docker build -t "$DOCKER_IMAGE" --platform "$DOCKER_PLATFORM" . > /dev/null)

    # Run with artifacts volume
    # shellcheck disable=SC2086
    docker run --rm \
        --platform "$DOCKER_PLATFORM" \
        -v "$CONFIG_PATH:/config.yaml:ro" \
        -v "$ARTIFACTS_DIR:/artifacts" \
        "$DOCKER_IMAGE" \
        $DOCKER_ARGS

    echo "=== Manifest generated ==="
    echo "Output: $ARTIFACTS_DIR/manifest.yaml"
else
    # Use CLI on host (prefer installed otel-distro-builder, else Python module)
    PYTHON_ARGS="--from-config $CONFIG_PATH --generate-only"
    PYTHON_ARGS="$PYTHON_ARGS --dist-name $DIST_NAME"
    PYTHON_ARGS="$PYTHON_ARGS --dist-module $DIST_MODULE"
    PYTHON_ARGS="$PYTHON_ARGS --dist-version $DIST_VERSION"
    [ -n "$OTEL_VERSION" ] && PYTHON_ARGS="$PYTHON_ARGS --otel-version $OTEL_VERSION"
    [ -n "$BINDPLANE_VERSION" ] && PYTHON_ARGS="$PYTHON_ARGS --bindplane-version $BINDPLANE_VERSION"
    [ -n "$OUTPUT_MANIFEST" ] && PYTHON_ARGS="$PYTHON_ARGS --output-manifest $OUTPUT_MANIFEST"
    [ -n "$ARTIFACTS_DIR" ] && PYTHON_ARGS="$PYTHON_ARGS --artifacts $ARTIFACTS_DIR"
    [ "$NO_BINDPLANE" = true ] && PYTHON_ARGS="$PYTHON_ARGS --no-bindplane"

    if command -v otel-distro-builder >/dev/null 2>&1; then
        # shellcheck disable=SC2086
        otel-distro-builder $PYTHON_ARGS
    else
        cd "$PROJECT_ROOT"
        # shellcheck disable=SC2086
        python -m builder.src.main $PYTHON_ARGS
    fi

    echo "=== Manifest generated ==="
    if [ -n "$ARTIFACTS_DIR" ]; then
        echo "Output: $ARTIFACTS_DIR/manifest.yaml"
    else
        echo "Output: ./artifacts/manifest.yaml"
    fi
fi
