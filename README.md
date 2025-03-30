# 🚀 OpenTelemetry Distribution Builder

<div align="center">

[![GitHub Release](https://img.shields.io/github/v/release/observIQ/otel-distro-builder)](https://github.com/observIQ/otel-distro-builder/releases)
[![Apache 2.0 License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

Build custom OpenTelemetry Collector Distributions from manifest files with a local build utility, Docker, Google Cloud Build, or a GitHub Action.

[Quick Start](#-quick-start) • [Documentation](#-documentation) • [Examples](#-examples)

</div>

## 🤔 Why OpenTelemetry Distribution Builder?

The OpenTelemetry Distribution Builder lets you create and maintain custom, vendor-neutral OpenTelemetry Collector distributions—without all the usual complexity.

Built on top of the [OpenTelemetry Collector Builder (OCB)](https://github.com/open-telemetry/opentelemetry-collector/tree/main/cmd/builder), it uses a `manifest.yaml` to define the components you need, then automates packaging for multiple platforms and manages version releases via GitHub.

Avoid vendor lock-in or the overhead of bundling the entire OpenTelemetry Contrib Collector, and maintain a distribution that’s perfectly tailored to your needs.

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
     module: github.com/open-telemetry/opentelemetry-collector-releases/core
     name: my-otelcol
     description: My Custom OpenTelemetry Collector Distro
     output_path: ./artifacts
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
   name: Build OpenTelemetry Distribution
   on:
     push:
       tags: ["v*"]
     workflow_dispatch:

   jobs:
     build:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - uses: observiq/otel-distro-builder@v1
           with:
             manifest: "./manifest.yaml"
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

| Input              | Description                 | Default           |
| ------------------ | --------------------------- | ----------------- |
| `manifest`         | Path to manifest file       | `./manifest.yaml` |
| `create_release`   | Create GitHub release       | `true`            |
| `upload_artifacts` | Upload to Actions artifacts | `true`            |
| `platforms`        | Target platforms            | `linux/amd64`     |

#### Outputs

| Output           | Description          |
| ---------------- | -------------------- |
| `name`           | Distribution name    |
| `version`        | Distribution version |
| `artifacts_path` | Path to artifacts    |

### Docker Usage

```bash
# Pull the latest version
docker pull ghcr.io/observiq/otel-distro-builder:main

# Pull specific version
docker pull ghcr.io/observiq/otel-distro-builder:v1.0.5

# Run a build
docker run --rm -v $(pwd):/workspace -v $(pwd)/build:/build ghcr.io/observiq/otel-distro-builder:main \
  --manifest /workspace/manifest.yaml \
  # Optional
  --artifacts /workspace/artifacts \
  --goos linux \
  --goarch amd64 \
  --ocb-version 0.121.0 \
  --go-version 1.22.1
```

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

# Create new release
make release          # Auto-increment patch version
make release v=2.0.0 # Specific version
```

### Build Scripts

#### `run_cloud_build.sh`

Triggers a build using Google Cloud Build:

```bash
./scripts/run_cloud_build.sh -m manifest.yaml -p project_id -b artifact_bucket [-i build_id]
```

Options:

- `-m`: Path to manifest file (required)
- `-p`: Google Cloud project ID
- `-b`: Artifact bucket name
- `-i`: Build ID for artifact storage (default: auto-generated)

#### `run_local_build.sh`

This script is used to build a custom OpenTelemetry Collector distribution using a local Docker container:

```bash
./scripts/run_local_build.sh -m manifest.yaml [-o output_dir] [-v ocb_version] [-g go_version]

# Optionally, run it with
make build-local # to get the latest version of the otelcol and ocb
# Or
make build -v 0.121.0 -s 0.122.0 -g 1.24.1 # to pass custom params as needed
```

Options:

- `-m`: Path to manifest file (required)
- `-o`: Directory to store build artifacts (default: ./artifacts)
- `-v`: OpenTelemetry Collector Builder version (default: 0.121.0)
- `-g`: Go version to use for building (default: 1.24.1)
- `-i`: Build ID for artifact storage (default: auto-generated)

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

1. **Builder Image Preparation**: Build and push to Google Container Registry
2. **Manifest Processing**: Upload and validate manifest configuration
3. **Build Execution**:
   - Download OpenTelemetry Collector Builder (OCB)
   - Generate Go source files
   - Build platform-specific packages
   - Create SBOMs and checksums
4. **Artifact Management**: Upload to Google Cloud Storage

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
