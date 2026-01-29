# 🚀 OpenTelemetry Distribution Builder

<div align="center">

[![GitHub Release](https://img.shields.io/github/v/release/observIQ/otel-distro-builder)](https://github.com/observIQ/otel-distro-builder/releases)
[![Apache 2.0 License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

Build custom OpenTelemetry Collector Distributions from manifest files with a local build utility, Docker, Google Cloud Build, or a GitHub Action.

[Quick Start](#-quick-start) • [Documentation](#-documentation) • [Examples](#-examples)

</div>

## 🤔 Why OpenTelemetry Distribution Builder?

Built on top of the [OpenTelemetry Collector Builder (OCB)](https://github.com/open-telemetry/opentelemetry-collector/tree/main/cmd/builder), it uses a `manifest.yaml` to define the components you need, then automates packaging for multiple platforms and manages version releases via GitHub.

While OCB (OpenTelemetry Collector Builder) focuses on building single collector binaries, the OpenTelemetry Distribution Builder provides a complete distribution management solution:

- 🔨 Builds multi-platform binaries using OCB under the hood
- 📦 Generates installation packages following OTel community best practices
- 🚀 Automates versioned releases through GitHub Actions
- 🔄 Simplifies updates through manifest-based configuration

It handles all the complex aspects of managing your own distribution that have historically made building custom collectors challenging. With the OpenTelemetry Distribution Builder, you can focus on defining your components while the tooling takes care of the rest.

## ✨ Features

- 🎯 **Custom Component Selection**: Build distributions with exactly the components you need
- 🌐 **Multi-Platform Support**: Build for multiple architectures (amd64, arm64)
- 📦 **Multiple Package Formats**: Generate APK, DEB, RPM, and TAR.GZ packages
- 🔄 **GitHub Actions Integration**: Seamless CI/CD integration
- 🚀 **Automated Releases**: Streamlined versioning and release process
- 🔍 **Platform-Specific Builds**: Optimize for your target environment

## 🚀 Quick Start

1. **Create a new repository**
2. **Add your manifest file** (`manifest.yaml`):

   ```yaml
   dist:
     name: my-otelcol
     description: My Custom OpenTelemetry Collector Distro
     # ...
   extensions:
     -  # ...
   exporters:
     -  # ...
   processors:
     -  # ...
   receivers:
     -  # ...
   connectors:
     -  # ...
   providers:
     -  # ...
   ```

3. **Set up GitHub Actions** (`.github/workflows/build.yml`):

```yaml
name: OpenTelemetry Distribution Build

on:
   push:
     tags:
       - "v*"
   workflow_dispatch:

  permissions:
    contents: write # This is required for creating/modifying releases

  jobs:
    build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Build the OpenTelemetry distribution using this custom action
      - uses: observiq/otel-distro-builder@v1
        with:
          manifest: "./manifest.yaml"

      # Create a GitHub Release and attach the build artifacts
      # This makes the artifacts available for download from the Releases page
      - name: Create Release
        uses: softprops/action-gh-release@v2
        with:
          files: ${{ github.workspace }}/artifacts/*
```

4. **Trigger a build**:

   ```bash
   git tag v1.0.0 && git push --tags
   ```

5. **(Optional) Build with Docker**:

   ```bash
   docker pull ghcr.io/observiq/otel-distro-builder:main
   docker run --rm -v $(pwd):/workspace -v $(pwd)/build:/build ghcr.io/observiq/otel-distro-builder:main \
     --manifest /workspace/manifest.yaml
   ```

## 📚 Documentation

To view detailed guides, see the [docs](./docs) directory.

### GitHub Action Configuration

#### Inputs

| Input       | Description           | Default           |
| ----------- | --------------------- | ----------------- |
| `manifest`  | Path to manifest file | `./manifest.yaml` |
| `platforms` | Target platforms      | `linux/amd64`     |

#### Outputs

All generated packages and binaries are available in the `${{ github.workspace }}/artifacts/*` folder.

### Docker Usage

```bash
# Pull the latest version
docker pull ghcr.io/observiq/otel-distro-builder:latest

# Pull specific version
docker pull ghcr.io/observiq/otel-distro-builder:v1.0.5

# Run a build
docker run --rm \
  -v "$(pwd)/manifest.yaml:/manifest.yaml:ro" \
  -v "$(pwd)/artifacts:/artifacts" \
  ghcr.io/observiq/otel-distro-builder:latest \
  --manifest /manifest.yaml \
  --artifacts /artifacts \
  --goos windows,linux,windows \ # select operating system
  --goarch amd64,arm64 \ # select architecture
  # optional, versions will default to values in manifest.yaml
  --ocb-version 0.123.0 \
  --supervisor-version 0.123.0 \
  --go-version 1.24.1
```

> Read more details in the [Docker documentation](./docs/docker.md).

## 🛠️ Development

### Prerequisites

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

```

### Build Scripts

#### `run_cloud_build.sh`

Triggers a build using Google Cloud Build:

```bash
./scripts/run_cloud_build.sh -m manifest.yaml -p project_id -b artifact_bucket
```

Options:

- `-m`: Path to manifest file (required)
- `-p`: Google Cloud project ID
- `-b`: Artifact bucket name

#### `run_local_build.sh`

This script is used to build a custom OpenTelemetry Collector distribution using a local Docker container:

```bash
./scripts/run_local_build.sh -m manifest.yaml [-o output_dir] [-v ocb_version] [-g go_version]

# Optionally, run it with
make build-local # to get the latest version of the otelcol and ocb
# Or
make build output_dir=./artifacts ocb_version=0.121.0 go_version=1.22.1 supervisor_version=0.122.0
```

Options:

- `-m`: Path to manifest file (required)
- `-o`: Directory to store build artifacts (default: ./artifacts)
- `-v`: OpenTelemetry Collector Builder version (default: auto-detected from manifest)
- `-g`: Go version to use for building (default: 1.24.1)

The artifacts will be saved to the specified output directory (default: `./artifacts`).

## 📁 Project Structure

```text
otel-distro-builder/
├── builder/                # Builder application
│   ├── src/               # Core builder code
│   ├── templates/         # Build templates
│   ├── tests/            # Test suite
│   └── Dockerfile        # Builder image definition
├── action/                # GitHub Action
├── scripts/              # Build scripts
└── Makefile              # Development commands
```

## 🔧 Build Process

1. **Builder Image Preparation**: Build and push to registry
2. **Manifest Processing**: Upload and validate manifest configuration
3. **Build Execution**:
   - Download OpenTelemetry Collector Builder (OCB)
   - Generate Go source files
   - Build platform-specific packages
   - Create SBOMs and checksums
4. **Artifact Management**: Upload to GitHub, Google Cloud Storage, or save locally

## 📦 Build Artifacts

The builder produces:

- 📦 Binary packages (APK, DEB, RPM)
- 📚 Source tarball
- 🔧 Raw binary
- 📋 SBOM files
- 🔍 Checksums
- 📝 Build metadata

### Storage Locations

- **Local builds**: `./artifacts` directory
- **Cloud builds**: `gs://<bucket>/<build_id>/`

## 🔢 Versioning

We follow semantic versioning. The builder is available in several forms:

- GitHub Action: Use `@v1` for latest 1.x version, or `@v1.0.5` for specific versions
- Docker Image: Use `main` for latest, or version tags like `v1.0.5`
- Container Registry: `ghcr.io/observiq/otel-distro-builder:main` or `ghcr.io/observiq/otel-distro-builder:v1.0.5`

## 📚 Examples

Check out our example workflows in `.github/workflows/examples/` for common use cases:

- Multi-platform builds
- Container publishing
- Custom package configurations

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">
  Made with ❤️ by the Bindplane team
</div>
