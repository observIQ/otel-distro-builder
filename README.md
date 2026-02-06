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

## 🔄 Generate Manifest from Existing Config

Already have a running OpenTelemetry Collector with a `config.yaml`? Generate a minimal manifest containing only the components you need:

```bash
# Generate manifest only (prints to stdout)
docker run -v $(pwd):/workspace ghcr.io/observiq/otel-distro-builder:latest \
  --from-config /workspace/config.yaml \
  --generate-only

# Generate manifest and save to file
docker run -v $(pwd):/workspace ghcr.io/observiq/otel-distro-builder:latest \
  --from-config /workspace/config.yaml \
  --output-manifest /workspace/manifest.yaml \
  --generate-only

# Generate manifest and build in one step
docker run -v $(pwd):/workspace ghcr.io/observiq/otel-distro-builder:latest \
  --from-config /workspace/config.yaml \
  --artifacts /workspace/dist \
  --platforms linux/amd64,linux/arm64
```

### Config-to-Manifest Options

| Option | Description | Default |
|--------|-------------|---------|
| `--from-config` | Path to collector config.yaml | Required |
| `--output-manifest` | Path to write generated manifest | None |
| `--generate-only` | Only generate manifest, don't build | `false` |
| `--otel-version` | Target OpenTelemetry version | Latest from `versions.yaml` |
| `--dist-name` | Distribution name | `otelcol-custom` |
| `--dist-module` | Go module path | `github.com/custom/otelcol-distribution` |
| `--dist-version` | Distribution version | `1.0.0` |
| `--no-bindplane` | Exclude Bindplane components | `false` (included) |

> **Note:** By default, generated manifests include all Bindplane components. Use `--no-bindplane` to exclude them.

> See [Config to Manifest documentation](./docs/config-to-manifest.md) for detailed usage and examples.

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
  --platforms linux/amd64,linux/arm64,darwin/amd64,darwin/arm64 \
  --ocb-version 0.123.0 \
  --supervisor-version 0.123.0 \
  --go-version 1.24.0 \
  --parallelism 4
```

**Using `--platforms`** (comma-separated GOOS/GOARCH):

```bash
# Single platform (e.g. Apple Silicon)
docker run --rm -v "$(pwd)/manifest.yaml:/manifest.yaml:ro" -v "$(pwd)/artifacts:/artifacts" \
  ghcr.io/observiq/otel-distro-builder:latest --manifest /manifest.yaml --artifacts /artifacts \
  --platforms darwin/arm64

# Linux only (amd64 + arm64)
docker run --rm -v "$(pwd)/manifest.yaml:/manifest.yaml:ro" -v "$(pwd)/artifacts:/artifacts" \
  ghcr.io/observiq/otel-distro-builder:latest --manifest /manifest.yaml --artifacts /artifacts \
  --platforms linux/amd64,linux/arm64

# Linux + Darwin (all common arches)
docker run --rm -v "$(pwd)/manifest.yaml:/manifest.yaml:ro" -v "$(pwd)/artifacts:/artifacts" \
  ghcr.io/observiq/otel-distro-builder:latest --manifest /manifest.yaml --artifacts /artifacts \
  --platforms linux/amd64,linux/arm64,darwin/amd64,darwin/arm64
```

Optional builder arguments: `--platforms` (GOOS/GOARCH list), `--goos`, `--goarch`, `--ocb-version`, `--supervisor-version`, `--go-version`, `--parallelism` (number of parallel Goreleaser build tasks; default 4; lower to reduce memory use).

> Read more details in the [Docker documentation](./docs/docker.md).

#### Parallelism Benchmarks

When building for multiple architectures or large manifests, the number of parallel Goreleaser build tasks (`--parallelism`) directly affects memory usage and build time. Here are real-world benchmarks for different parallelism settings (measured on a MacBook Pro M4 Pro with 48GB RAM, Docker Engine set to 14 CPUs + 24GB RAM):

| Build Targets                                                            | Parallelism | Duration    |
| ------------------------------------------------------------------------ | ----------- | ----------- |
| Single architecture (`darwin/arm64`)                                     | 1           | 05m 56s     |
| Single architecture (`darwin/arm64`)                                     | 4           | 04m 44s     |
| Single architecture (`darwin/arm64`)                                     | 14          | 05m 26s     |
| Single architecture (`linux/arm64`)                                      | 1           | 05m 23s     |
| Single architecture (`linux/arm64`)                                      | 4           | 05m 45s     |
| Single architecture (`linux/arm64`)                                      | 14          | 04m 38s     |
| Single architecture (`linux/amd64`)                                      | 14          | 05m 06s     |
| Multi-architecture (`darwin/arm64,darwin/amd64`)                         | 1           | 07m 12s     |
| Multi-architecture (`darwin/arm64,darwin/amd64`)                         | 4           | 08m 04s     |
| Multi-architecture (`darwin/arm64,darwin/amd64`)                         | 14          | 06m 56s     |
| Multi-architecture (`linux/arm64,linux/amd64`)                           | 1           | 10m 09s     |
| Multi-architecture (`darwin/arm64,linux/arm64`)                          | 1           | 08m 27s     |
| Multi-architecture (`darwin/arm64,linux/arm64`)                          | 4           | 07m 19s     |
| Multi-architecture (`darwin/arm64,linux/arm64`)                          | 14          | 07m 32s     |
| Multi-architecture (`darwin/arm64,linux/amd64`)                          | 1           | 14m 02s     |
| Multi-architecture (`darwin/arm64,linux/amd64`)                          | 4           | 12m 14s     |
| Multi-architecture (`darwin/arm64,linux/amd64`)                          | 14          | 11m 13s     |
| Multi-architecture (`darwin/arm64,darwin/amd64,linux/arm64,linux/amd64`) | 1           | 14m 06s     |
| Multi-architecture (`darwin/arm64,darwin/amd64,linux/arm64,linux/amd64`) | 14          | 11m 21s     |
| Multi-architecture (`darwin/arm64,darwin/amd64,linux/arm64,linux/amd64`) | 16          | 10m 55s     |
| Single architecture (`darwin/arm64`)                                     | 48          | 03m 43s     |
| Single architecture (`linux/amd64`)                                      | 48          | 04m 36s     |

- Lower `--parallelism` reduces peak memory use and may be required for constrained environments or very large builds, at the expense of longer build times.
- Higher `--parallelism` can speed up builds if you have sufficient memory, but may cause OOM failures on systems with limited RAM. In particular for multi-architecture builds for multiple platforms.
- For collector builds with many components, ensure Docker/host RAM is at least 4–6 GB (more for larger/parallel builds).

> See [Docker documentation](./docs/docker.md) for more details and troubleshooting tips.

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

Build a custom OpenTelemetry Collector distribution using a local Docker container (single or custom platform):

```bash
# Basic build (host platform)
./scripts/run_local_build.sh -m manifest.yaml

# Custom output directory and versions
./scripts/run_local_build.sh -m manifest.yaml -o ./dist -v 0.121.0 -s 0.122.0 -g 1.24.0

# Build Docker image for a specific platform (e.g. Apple Silicon / arm64)
./scripts/run_local_build.sh -m manifest.yaml -p linux/arm64

# Multiple platforms for Docker image (comma-delimited)
./scripts/run_local_build.sh -m manifest.yaml -p linux/arm64,linux/amd64
```

Options: `-m` (required), `-o` (output dir), `-p` (platforms), `-v` (OCB version), `-g` (Go version), `-s` (Supervisor version). When running the container directly, you can also pass `--parallelism N` to the builder (default 4; lower for less memory use).

Via Make: `make build`, `make build-local`, `make build output_dir=./artifacts ocb_version=0.121.0`, `make build platforms=linux/arm64,linux/amd64`.

**Multi-arch builds** use the same script with `-p` (omit `-p` for single-arch default linux/arm64):

```bash
# Multi-arch: linux + darwin, amd64 + arm64
./scripts/run_local_build.sh -m manifest.yaml -p linux/amd64,linux/arm64,darwin/amd64,darwin/arm64

# Or a subset of platforms
./scripts/run_local_build.sh -m manifest.yaml -p linux/amd64,linux/arm64 -o ./dist -v 0.121.0 -s 0.122.0 -g 1.24.0
```

Via Make: `make multiarch-build` (default platforms), `make multiarch-build-local`, or `make build platforms=linux/amd64,linux/arm64`.

Artifacts are written to the specified output directory (default: `./artifacts`).

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
