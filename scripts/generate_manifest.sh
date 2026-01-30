#!/bin/bash
set -e

# Default values
OUTPUT_MANIFEST=""
OTEL_VERSION=""
DIST_NAME="otelcol-custom"
DIST_MODULE="github.com/custom/otelcol-distribution"
DIST_VERSION="1.0.0"
USE_DOCKER=false
DOCKER_IMAGE="otel-distro-builder"
NO_BINDPLANE=false

# Help message
usage() {
    echo "Usage: $0 -c <config_path> [-o <output_manifest>] [options]"
    echo
    echo "Generate an OCB manifest from an existing OpenTelemetry Collector config.yaml"
    echo
    echo "Required arguments:"
    echo "  -c <config_path>            Path to collector config.yaml file"
    echo
    echo "Optional arguments:"
    echo "  -o <output_manifest>        Path to write generated manifest (default: stdout)"
    echo "  -v <otel_version>           Target OpenTelemetry version (default: latest from versions.yaml)"
    echo "  -n <dist_name>              Distribution name (default: otelcol-custom)"
    echo "  -m <dist_module>            Go module path (default: github.com/custom/otelcol-distribution)"
    echo "  -V <dist_version>           Distribution version (default: 1.0.0)"
    echo "  -B                          Exclude Bindplane/observIQ components (included by default)"
    echo "  -d                          Use Docker instead of local Python"
    echo "  -h                          Show this help message"
    echo
    echo "Examples:"
    echo "  # Generate manifest and print to stdout"
    echo "  $0 -c config.yaml"
    echo
    echo "  # Generate manifest and save to file"
    echo "  $0 -c config.yaml -o manifest.yaml"
    echo
    echo "  # Generate manifest with specific OTel version"
    echo "  $0 -c config.yaml -o manifest.yaml -v 0.144.0"
    echo
    echo "  # Generate manifest with custom distribution name"
    echo "  $0 -c config.yaml -o manifest.yaml -n my-collector -m github.com/myorg/collector"
    echo
    echo "  # Generate manifest without Bindplane components"
    echo "  $0 -c config.yaml -o manifest.yaml -B"
    echo
    echo "  # Use Docker instead of local Python"
    echo "  $0 -c config.yaml -o manifest.yaml -d"
    exit 1
}

# Parse command line arguments
while getopts "c:o:v:n:m:V:Bdh" opt; do
    case $opt in
    c) CONFIG_PATH="$OPTARG" ;;
    o) OUTPUT_MANIFEST="$OPTARG" ;;
    v) OTEL_VERSION="$OPTARG" ;;
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
[ -n "$OUTPUT_MANIFEST" ] && echo "Output: $OUTPUT_MANIFEST"
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
    [ "$NO_BINDPLANE" = true ] && DOCKER_ARGS="$DOCKER_ARGS --no-bindplane"
    
    if [ -n "$OUTPUT_MANIFEST" ]; then
        OUTPUT_DIR=$(dirname "$OUTPUT_MANIFEST")
        OUTPUT_FILENAME=$(basename "$OUTPUT_MANIFEST")
        mkdir -p "$OUTPUT_DIR"
        OUTPUT_MANIFEST=$(cd "$OUTPUT_DIR" && pwd)/$OUTPUT_FILENAME
        DOCKER_ARGS="$DOCKER_ARGS --output-manifest /output/$OUTPUT_FILENAME"
        
        # Build Docker image if needed
        echo "Building Docker image..."
        DOCKER_PLATFORM="linux/$(uname -m | sed 's/x86_64/amd64/' | sed 's/aarch64/arm64/')"
        (cd "$PROJECT_ROOT/builder" && docker build -t "$DOCKER_IMAGE" --platform "$DOCKER_PLATFORM" . > /dev/null)
        
        # Run with output volume
        # shellcheck disable=SC2086
        docker run --rm \
            --platform "$DOCKER_PLATFORM" \
            -v "$CONFIG_PATH:/config.yaml:ro" \
            -v "$OUTPUT_DIR:/output" \
            "$DOCKER_IMAGE" \
            $DOCKER_ARGS
        
        echo "=== Manifest generated ==="
        echo "Output: $OUTPUT_MANIFEST"
    else
        # Build Docker image if needed
        echo "Building Docker image..."
        DOCKER_PLATFORM="linux/$(uname -m | sed 's/x86_64/amd64/' | sed 's/aarch64/arm64/')"
        (cd "$PROJECT_ROOT/builder" && docker build -t "$DOCKER_IMAGE" --platform "$DOCKER_PLATFORM" . > /dev/null)
        
        # Run without output volume (prints to stdout)
        # shellcheck disable=SC2086
        docker run --rm \
            --platform "$DOCKER_PLATFORM" \
            -v "$CONFIG_PATH:/config.yaml:ro" \
            "$DOCKER_IMAGE" \
            $DOCKER_ARGS
    fi
else
    # Use local Python
    PYTHON_ARGS="--from-config $CONFIG_PATH --generate-only"
    PYTHON_ARGS="$PYTHON_ARGS --dist-name $DIST_NAME"
    PYTHON_ARGS="$PYTHON_ARGS --dist-module $DIST_MODULE"
    PYTHON_ARGS="$PYTHON_ARGS --dist-version $DIST_VERSION"
    [ -n "$OTEL_VERSION" ] && PYTHON_ARGS="$PYTHON_ARGS --otel-version $OTEL_VERSION"
    [ -n "$OUTPUT_MANIFEST" ] && PYTHON_ARGS="$PYTHON_ARGS --output-manifest $OUTPUT_MANIFEST"
    [ "$NO_BINDPLANE" = true ] && PYTHON_ARGS="$PYTHON_ARGS --no-bindplane"
    
    # Run the Python module
    cd "$PROJECT_ROOT"
    # shellcheck disable=SC2086
    python -m builder.src.main $PYTHON_ARGS
    
    if [ -n "$OUTPUT_MANIFEST" ]; then
        echo "=== Manifest generated ==="
        echo "Output: $OUTPUT_MANIFEST"
    fi
fi
