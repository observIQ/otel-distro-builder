# OpenTelemetry Collector Builder

This directory contains the source code for the OpenTelemetry Builder Node, which builds custom OpenTelemetry Collector distributions based on a manifest file.

## Overview

The builder creates OpenTelemetry Collector distributions with custom components. It supports:

- Multiple package formats (APK, DEB, RPM, TAR.GZ)
- Platform-specific builds
- Custom component selection
- GitHub Actions integration
- Multi-platform builds (amd64, arm64)
- Automated releases and versioning

## Quick Start

1. Create a new repository
2. Add your `manifest.yaml` defining your custom collector
3. Create `.github/workflows/build.yml`:

   ```yaml
   name: Build Collector
   on:
     push:
       tags: ["v*"]
     workflow_dispatch:

   jobs:
     build:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - uses: mkelly/otel-builder@v1
           with:
             manifest: "./manifest.yaml"
   ```

4. Push a tag: `git tag v1.0.0 && git push --tags`

## GitHub Action Usage

### Inputs

| Input              | Description                 | Default           |
| ------------------ | --------------------------- | ----------------- |
| `manifest`         | Path to manifest file       | `./manifest.yaml` |
| `output-dir`       | Output directory            | `./artifacts`     |
| `create_release`   | Create GitHub release       | `true`            |
| `upload_artifacts` | Upload to Actions artifacts | `true`            |
| `platforms`        | Target platforms            | `linux/amd64`     |
| `debug`            | Enable debug logging        | `false`           |

### Outputs

| Output           | Description       |
| ---------------- | ----------------- |
| `name`           | Collector name    |
| `version`        | Collector version |
| `artifacts_path` | Path to artifacts |

### Example: Multi-Platform Build with Container Publishing

```yaml
- uses: mkelly/otel-builder@v1
  with:
    manifest: collector/manifest.yml
    output-dir: ./dist
    platforms: linux/amd64,linux/arm64

- name: Build and push container images
  uses: docker/build-push-action@v5
  with:
    context: ./dist
    platforms: linux/amd64,linux/arm64
    push: true
    tags: |
      ghcr.io/mkelly/collector:latest
      ghcr.io/mkelly/collector:1.0.0
```

See `.github/workflows/examples/` for more example workflows.

## Versioning

We follow semantic versioning. The builder is available in several forms:

- GitHub Action: Use `@v1` for latest 1.x version, or `@v1.2.3` for specific versions
- Docker Image: Use `main` for latest, or version tags like `v1.2.3`
- Container Registry: `ghcr.io/mkelly/otel-builder:main` or `ghcr.io/mkelly/otel-builder:v1.2.3`

## Docker Usage

The builder is available as a container image from GitHub Container Registry:

```bash
# Pull latest version
docker pull ghcr.io/mkelly/otel-builder:main

# Pull specific version
docker pull ghcr.io/mkelly/otel-builder:v1.2.3

# Run a build
docker run --rm -v $(pwd):/workspace ghcr.io/mkelly/otel-builder:main \
  --manifest /workspace/manifest.yml \
  --output /workspace/dist
```

## Directory Structure

```
otel-builder/
├── src/    # Core builder code
│   ├── main.py             # Main entry point
│   ├── build.py            # Build process implementation
│   ├── ocb_downloader.py   # OCB binary management
│   └── logger.py           # Logging utilities
├── tests/                  # Test suite
│   ├── test_build.py       # Build process tests
│   └── conftest.py         # Test configuration
├── cloudbuild.yaml         # Cloud Build configuration
├── Dockerfile              # Builder image definition
├── Makefile               # Development commands
└── run_local_build.sh     # Local build script
```

## Development

### Requirements

- Python 3
- Docker
- Make

### Available Commands

```bash
# Show all commands
make help

# Setup development environment
make setup

# Run tests
make test

# Run linting
make lint

# Create new release
make release          # Auto-increment patch version
make release v=2.0.0 # Specific version
```

### Build Scripts

#### run_cloud_build.sh

Triggers a build using Google Cloud Build:

```bash
./run_cloud_build.sh -m manifest.yaml [-p project_id] [-b artifact_bucket] [-i build_id]
```

Options:

- `-m`: Path to manifest file (required)
- `-p`: Google Cloud project ID
- `-b`: Artifact bucket name
- `-i`: Build ID for artifact storage (default: auto-generated)

#### run_local_build.sh

Runs a build locally using Docker:

```bash
./run_local_build.sh -m manifest.yaml
```

The artifacts will be saved to the `./artifacts` directory.

## Build Process

1. The builder image is built and pushed to Google Container Registry
2. The manifest file is uploaded to the build environment
3. The builder:
   - Downloads OCB (OpenTelemetry Collector Builder)
   - Validates the manifest configuration
   - Generates Go source files from the manifest
   - Builds platform-specific packages
   - Creates SBOMs and checksums
4. Artifacts are uploaded to Google Cloud Storage

## Build Artifacts

The build produces several artifacts:

- Binary packages (APK, DEB, RPM)
- Source tarball
- Raw binary
- SBOM files
- Checksums
- Build metadata

Artifacts are stored in:

- Local builds: `./artifacts` directory
- Cloud builds: `gs://<bucket>/<build_id>/`
