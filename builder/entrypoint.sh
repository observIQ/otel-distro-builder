#!/bin/bash
set -e

# Convert GitHub Actions inputs to command line arguments
ARGS=""

# Required arguments
if [ -n "$INPUT_MANIFEST" ]; then
    ARGS="$ARGS --manifest $INPUT_MANIFEST"
elif [ -n "$1" ]; then
    # Allow direct command line arguments to work too
    ARGS="$ARGS $@"
    exec python /app/builder/src/main.py $ARGS
    exit 0
fi

# Optional arguments
if [ -n "$INPUT_ARTIFACT_DIR" ]; then
    ARGS="$ARGS --artifacts $INPUT_ARTIFACT_DIR"
fi

# Handle platforms if specified
if [ -n "$INPUT_PLATFORMS" ]; then
    ARGS="$ARGS --platforms $INPUT_PLATFORMS"
fi

# Handle OS if specified
if [ -n "$INPUT_OS" ]; then
    ARGS="$ARGS --goos $INPUT_OS"
fi

# Handle ARCH if specified
if [ -n "$INPUT_ARCH" ]; then
    ARGS="$ARGS --goarch $INPUT_ARCH"
fi

# Handle OCB and supervisor versions if specified
if [ -n "$INPUT_OCB_VERSION" ]; then
    ARGS="$ARGS --ocb-version $INPUT_OCB_VERSION"
fi

if [ -n "$INPUT_SUPERVISOR_VERSION" ]; then
    ARGS="$ARGS --supervisor-version $INPUT_SUPERVISOR_VERSION"
fi

# Handle Go version if specified
if [ -n "$INPUT_GO_VERSION" ]; then
    ARGS="$ARGS --go-version $INPUT_GO_VERSION"
fi

echo "Executing: python /app/builder/src/main.py $ARGS"

# Execute the Python script with the converted arguments
exec python /app/builder/src/main.py $ARGS 