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

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build and Package
        uses: observiq/otel-distro-builder@v1
        with:
          manifest: "./manifest.yaml"
          output-dir: "./artifacts"
          create_release: true
          upload_artifacts: true
          platforms: "linux/amd64,linux/arm64"
```

## Available Inputs

The GitHub Action accepts the following inputs:

| Input              | Description                        | Default           | Required |
| ------------------ | ---------------------------------- | ----------------- | -------- |
| `manifest`         | Path to manifest file              | `./manifest.yaml` | Yes      |
| `output-dir`       | Output directory for artifacts     | `./artifacts`     | No       |
| `create_release`   | Create GitHub release              | `true`            | No       |
| `upload_artifacts` | Upload to Actions artifacts        | `true`            | No       |
| `platforms`        | Target platforms (comma-separated) | `linux/amd64`     | No       |

## Outputs

The action provides the following outputs:

| Output           | Description                    |
| ---------------- | ------------------------------ |
| `name`           | Name of the built collector    |
| `version`        | Version of the built collector |
| `artifacts_path` | Path to the built artifacts    |

## Example Workflows

### Basic Build with Release

```yaml
name: Build and Release

on:
  push:
    tags: ["v*"]
  workflow_dispatch:

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
          create_release: true
          upload_artifacts: true
```

### Multi-Platform Build

```yaml
name: Multi-Platform Build

on:
  push:
    tags: ["v*"]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build and Package Collector
        uses: observiq/otel-distro-builder@v1
        with:
          manifest: "./manifest.yaml"
          platforms: "linux/amd64,linux/arm64,linux/arm/v7"
          create_release: true
          upload_artifacts: true
```

### Custom Output Directory

```yaml
name: Custom Output Build

on:
  push:
    tags: ["v*"]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build and Package Collector
        uses: observiq/otel-distro-builder@v1
        with:
          manifest: "./manifest.yaml"
          output-dir: "./dist"
          create_release: true
          upload_artifacts: true
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

When `create_release` is enabled:

- A new GitHub release is created with the tag name
- All artifacts are attached to the release
- Release notes are generated from commit messages

### Actions Artifacts

When `upload_artifacts` is enabled:

- All built artifacts are uploaded to GitHub Actions
- Available for download from the Actions UI
- Can be used by subsequent workflow steps

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
- [GitHub Repository](https://github.com/observiq/otel-distor-builder)
- [Issue Tracker](https://github.com/observiq/otel-distro-builder/issues)
