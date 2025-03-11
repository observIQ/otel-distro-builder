#!/bin/bash
set -e

# Help message
usage() {
    echo "Usage: $0 -m <manifest_path> [-p <project_id>] [-b <artifact_bucket>]"
    echo
    echo "Build an OpenTelemetry Collector using Google Cloud Build"
    echo
    echo "Required arguments:"
    echo "  -m <manifest_path>    Path to manifest.yaml/yml file"
    echo "  -p <project_id>       Google Cloud project ID"
    echo "  -b <artifact_bucket>  Artifact bucket name"
    echo
    echo "Optional arguments:"
    echo "  -h                    Show this help message"
    echo
    echo "Example:"
    echo "  $0 -m manifest.yaml -p my-project -b my-bucket"
    exit 1
}

# Function to check required tools
check_requirements() {
    local missing_tools=()
    
    command -v gcloud >/dev/null 2>&1 || missing_tools+=("gcloud")
    command -v gsutil >/dev/null 2>&1 || missing_tools+=("gsutil")
    command -v docker >/dev/null 2>&1 || missing_tools+=("docker")
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        echo "Error: Missing required tools: ${missing_tools[*]}"
        exit 1
    fi
}

# Parse command line arguments
while getopts "m:p:b:h" opt; do
    case $opt in
        m) MANIFEST_PATH="$OPTARG";;
        p) PROJECT_ID="$OPTARG";;
        b) ARTIFACT_BUCKET="$OPTARG";;
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

if [ -z "$PROJECT_ID" ]; then
    echo "Error: Project ID is required. Use -p <project_id>"
    usage
fi

if [ -z "$ARTIFACT_BUCKET" ]; then
    echo "Error: Artifact bucket is required. Use -b <bucket>"
    usage
fi

# Check requirements
check_requirements

# Verify gcloud project
if ! gcloud projects describe "$PROJECT_ID" >/dev/null 2>&1; then
    echo "Error: Project $PROJECT_ID not found or not accessible"
    exit 1
fi

# Generate a unique build ID if not provided
if [ -z "${BUILD_ID:-}" ]; then
    BUILD_ID=$(date +%Y%m%d-%H%M%S)-$(head -c 6 /dev/urandom | xxd -p)
    echo "Generated Build ID: $BUILD_ID"
fi

# Print build configuration
echo "Build Configuration:"
echo "==================="
echo "Project ID:      $PROJECT_ID"
echo "Manifest:        $MANIFEST_PATH"
echo "Artifact bucket: $ARTIFACT_BUCKET"
echo "Build ID:        $BUILD_ID"
echo "==================="
echo

# Build and push the builder image
echo "Step 1: Building and pushing builder image..."
BUILDER_IMAGE="gcr.io/${PROJECT_ID}/otel-builder"
if ! docker build -t "$BUILDER_IMAGE" --platform linux/amd64 "$(dirname "$0")/.."; then
    echo "Docker build failed"
    exit 1
fi

if ! docker push "$BUILDER_IMAGE"; then
    echo "Docker push failed"
    exit 1
fi
echo "✓ Builder image pushed successfully"
echo

# Upload manifest to GCS
echo "Step 2: Uploading manifest to GCS..."
MANIFEST_GCS_PATH="gs://${ARTIFACT_BUCKET}/${BUILD_ID}/manifest.yaml"
if ! gsutil cp "$MANIFEST_PATH" "$MANIFEST_GCS_PATH"; then
    echo "Failed to upload manifest to GCS"
    exit 1
fi
echo "✓ Manifest uploaded successfully to $MANIFEST_GCS_PATH"
echo

# Run the build using cloudbuild.yaml
echo "Step 3: Triggering Cloud Build..."
if ! CLOUD_BUILD_ID=$(gcloud builds submit \
    --config="$(dirname "$0")/cloudbuild.yaml" \
    --substitutions=_MANIFEST_PATH="$MANIFEST_GCS_PATH",_BUILDER_IMAGE="$BUILDER_IMAGE",_ARTIFACT_BUCKET="$ARTIFACT_BUCKET",_BUILD_ID="$BUILD_ID" \
    --no-source \
    --format='get(id)'); then
    echo "Failed to submit Cloud Build job. Check your cloudbuild.yaml file and GCP permissions."
    exit 1
fi

if [ -z "$CLOUD_BUILD_ID" ]; then
    echo "Cloud Build submission succeeded but no build ID was returned. This is unexpected."
    exit 1
fi

echo "✓ Build submitted successfully"
echo "Cloud Build ID: $CLOUD_BUILD_ID"
echo
echo "Monitor build progress:"
echo "https://console.cloud.google.com/cloud-build/builds;region=global/$CLOUD_BUILD_ID?project=$PROJECT_ID"
echo
echo "Artifacts will be available at:"
echo "gs://$ARTIFACT_BUCKET/$BUILD_ID/"