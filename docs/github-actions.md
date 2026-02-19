# Using otel-distro-builder with GitHub Actions

This guide explains how to use `otel-distro-builder` with GitHub Actions to build custom OpenTelemetry Collector distributions in your CI/CD pipeline.

## Prerequisites

1. GitHub repository
2. GitHub Actions enabled
3. Appropriate repository permissions

## Quick Start

1. Create a manifest file (`manifest.yaml`) that defines your collector configuration:

```yaml
dist:
  module: github.com/open-telemetry/opentelemetry-collector-releases/core
  name: my-otelcol
  description: My Custom OpenTelemetry Collector Build
  output_path: ./artifacts
extensions:
  -  # Add your extensions
exporters:
  -  # Add your exporters
processors:
  -  # Add your processors
receivers:
  -  # Add your receivers
connectors:
  -  # Add your connectors
providers:
  -  # Add your providers
```

2. Create a GitHub Actions workflow file (`.github/workflows/build.yml`):

```yaml
name: Build OpenTelemetry Collector Distribution

on:
  push:
    tags: ["v*"]
  workflow_dispatch:

permissions:
  contents: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build and Package
        uses: observiq/otel-distro-builder@v1
        with:
          manifest: "./manifest.yaml"
          artifact_dir: "${{ github.workspace }}/artifacts"
          os: "linux"
          arch: "amd64,arm64"

      - name: Create Release
        uses: softprops/action-gh-release@v2
        with:
          files: ${{ github.workspace }}/artifacts/*
```

## Available Inputs

The GitHub Action accepts the following inputs:

| Input                | Description                                    | Default                       | Required |
| -------------------- | ---------------------------------------------- | ----------------------------- | -------- |
| `manifest`           | Path to manifest file                          | `./manifest.yaml`             | Yes      |
| `artifact_dir`       | Directory to store build artifacts             | `/github/workspace/artifacts` | Yes      |
| `os`                 | Target operating systems (comma-separated)     | `linux`                       | No       |
| `arch`               | Target architectures (comma-separated)         | `amd64`                       | No       |
| `ocb_version`        | OpenTelemetry Collector Builder version        | —                             | No       |
| `supervisor_version` | Supervisor version                             | —                             | No       |
| `go_version`         | Go version for building                        | —                             | No       |

## Outputs

The action does not expose formal step outputs. All generated artifacts are written to the directory specified by `artifact_dir`. Use a separate step (e.g. `softprops/action-gh-release`) to upload them to a GitHub Release or elsewhere.

## Example Workflows

### Basic Build with Release

```yaml
name: Build and Release

on:
  push:
    tags: ["v*"]
  workflow_dispatch:

permissions:
  contents: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Build and Package Collector
        uses: observiq/otel-distro-builder@v1
        with:
          manifest: "./manifest.yaml"
          artifact_dir: "${{ github.workspace }}/artifacts"

      - name: Create Release
        uses: softprops/action-gh-release@v2
        with:
          files: ${{ github.workspace }}/artifacts/*
```

### Multi-Platform Build

```yaml
name: Multi-Platform Build

on:
  push:
    tags: ["v*"]
  workflow_dispatch:

permissions:
  contents: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build and Package Collector
        uses: observiq/otel-distro-builder@v1
        with:
          manifest: "./manifest.yaml"
          artifact_dir: "${{ github.workspace }}/artifacts"
          os: "linux,darwin"
          arch: "amd64,arm64"

      - name: Create Release
        uses: softprops/action-gh-release@v2
        with:
          files: ${{ github.workspace }}/artifacts/*
```

### Custom Output Directory

```yaml
name: Custom Output Build

on:
  push:
    tags: ["v*"]
  workflow_dispatch:

permissions:
  contents: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build and Package Collector
        uses: observiq/otel-distro-builder@v1
        with:
          manifest: "./manifest.yaml"
          artifact_dir: "${{ github.workspace }}/dist"

      - name: Create Release
        uses: softprops/action-gh-release@v2
        with:
          files: ${{ github.workspace }}/dist/*
```

## Artifacts and Releases

### Generated Artifacts

The builder will generate the following artifacts:

- Binary distributions (tar.gz)
- Package files (DEB, RPM, APK)
- Docker images
- Configuration files
- Service files

### GitHub Release

The action does not create releases itself. Add a separate step using `softprops/action-gh-release` (or similar) to upload the contents of `artifact_dir` to a GitHub Release:

```yaml
- name: Create Release
  uses: softprops/action-gh-release@v2
  with:
    files: ${{ github.workspace }}/artifacts/*
```

### Actions Artifacts

To upload artifacts to GitHub Actions for download from the Actions UI, add an `actions/upload-artifact` step after the build:

```yaml
- uses: actions/upload-artifact@v4
  with:
    name: collector-artifacts
    path: ${{ github.workspace }}/artifacts/*
```

## Best Practices

1. **Version Management**

   - Use semantic versioning for tags
   - Tag format: `vX.Y.Z` (e.g., `v1.0.0`)
   - Include version in manifest file

2. **Platform Selection**

   - Specify only needed platforms
   - Consider your target environments
   - Balance build time vs. coverage

3. **Artifact Management**

   - Use meaningful output directories
   - Clean up old artifacts
   - Consider artifact retention policies

4. **Security**
   - Review manifest security implications
   - Use specific versions in manifest
   - Consider signing artifacts

## Troubleshooting

1. **Build Failures**

   - Check manifest file syntax
   - Verify component compatibility
   - Check action logs

2. **Release Issues**

   - Ensure proper tag format
   - Check GitHub permissions
   - Verify release settings

3. **Artifact Problems**
   - Check file permissions
   - Verify disk space
   - Review artifact size limits

## Additional Resources

- [OpenTelemetry Collector Documentation](https://opentelemetry.io/docs/collector/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Repository](https://github.com/observiq/otel-distro-builder)
- [Issue Tracker](https://github.com/observiq/otel-distro-builder/issues)
