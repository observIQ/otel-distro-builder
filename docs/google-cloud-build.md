# Using otel-distro-builder with Google Cloud Build

This guide explains how to use otel-distro-builder with Google Cloud Build to create custom OpenTelemetry Collector distributions in your CI/CD pipeline.

## Prerequisites

1. Google Cloud Platform account
2. Google Cloud SDK installed
3. Docker installed locally
4. Access to Google Container Registry (GCR) or Artifact Registry

## Quick Start

1. Create a manifest file (`manifest.yaml`) that defines your collector configuration:
```yaml
dist:
  module: github.com/open-telemetry/opentelemetry-collector-releases/core
  name: my-otelcol
  description: My Custom OpenTelemetry Collector Build
  output_path: ./artifacts
extensions:
  - # Add your extensions
exporters:
  - # Add your exporters
processors:
  - # Add your processors
receivers:
  - # Add your receivers
connectors:
  - # Add your connectors
providers:
  - # Add your providers
```

2. Create a `cloudbuild.yaml` file in your repository:
```yaml
steps:
  # Build the builder image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', '${_BUILDER_IMAGE}', '.']

  # Push the builder image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', '${_BUILDER_IMAGE}']

  # Run the builder
  - name: '${_BUILDER_IMAGE}'
    args:
      - '--manifest'
      - '${_MANIFEST_PATH}'
      - '--artifacts'
      - '/workspace/artifacts'
      - '--ocb-version'
      - '0.121.0'
      - '--go-version'
      - '1.24.1'
      - '--supervisor-version'
      - '0.122.0'

  # Upload artifacts to GCS
  - name: 'gcr.io/cloud-builders/gsutil'
    args: ['-m', 'cp', '-r', 'artifacts/*', 'gs://${_ARTIFACT_BUCKET}/${_BUILD_ID}/']

substitutions:
  _BUILDER_IMAGE: 'gcr.io/${PROJECT_ID}/otel-builder'
  _MANIFEST_PATH: 'gs://${_ARTIFACT_BUCKET}/${_BUILD_ID}/manifest.yaml'
  _ARTIFACT_BUCKET: 'my-artifact-bucket'
  _BUILD_ID: '${BUILD_ID}'
```

3. Run the build using the provided script:
```bash
./scripts/run_cloud_build.sh \
  -m manifest.yaml \
  -p your-project-id \
  -b your-artifact-bucket
```

## Build Configuration

### Required Parameters

| Parameter | Description |
|-----------|-------------|
| `-m` | Path to manifest file |
| `-p` | Google Cloud project ID |
| `-b` | Artifact bucket name |

### Optional Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `-i` | Build ID | Auto-generated |
| `-v` | OCB version | 0.121.0 |
| `-g` | Go version | 1.24.1 |
| `-s` | Supervisor version | 0.122.0 |

## Artifact Storage

### Google Cloud Storage
- Artifacts are stored in your specified GCS bucket
- Path format: `gs://<bucket>/<build-id>/`
- Includes all build outputs (binaries, packages, etc.)

### Build Artifacts
The following artifacts are generated and stored:
- Binary distributions (tar.gz)
- Package files (DEB, RPM, APK)
- Docker images
- Configuration files
- Service files

## Best Practices

1. **Project Setup**
   - Use a dedicated project for builds
   - Set up appropriate IAM permissions
   - Configure billing and quotas

2. **Storage Management**
   - Implement lifecycle policies for GCS
   - Clean up old artifacts
   - Monitor storage costs

3. **Security**
   - Use service accounts with minimal permissions
   - Enable audit logging
   - Review security settings

4. **Cost Optimization**
   - Use appropriate machine types
   - Implement build caching
   - Clean up unused resources

## Troubleshooting

1. **Build Failures**
   - Check Cloud Build logs
   - Verify manifest syntax
   - Review IAM permissions
   - Check resource quotas

2. **Storage Issues**
   - Verify bucket permissions
   - Check storage quotas
   - Review lifecycle policies

3. **Authentication Problems**
   - Verify service account permissions
   - Check API enablement
   - Review authentication methods

## Example Usage

### Basic Build
```bash
./scripts/run_cloud_build.sh \
  -m manifest.yaml \
  -p my-project \
  -b my-bucket
```

### Custom Build ID
```bash
./scripts/run_cloud_build.sh \
  -m manifest.yaml \
  -p my-project \
  -b my-bucket \
  -i custom-build-123
```

### Specific Versions
```bash
./scripts/run_cloud_build.sh \
  -m manifest.yaml \
  -p my-project \
  -b my-bucket \
  -v 0.121.0 \
  -g 1.24.1 \
  -s 0.122.0
```

## Additional Resources

- [Google Cloud Build Documentation](https://cloud.google.com/build/docs)
- [Google Cloud Storage Documentation](https://cloud.google.com/storage/docs)
- [OpenTelemetry Collector Documentation](https://opentelemetry.io/docs/collector/)
- [GitHub Repository](https://github.com/observiq/otel-distro-builder)
- [Issue Tracker](https://github.com/observiq/otel-distro-builder/issues) 