# Using the Local Build Script

This guide explains how to use the `run_local_build.sh` script to build custom OpenTelemetry Collector distributions using a local Docker container.

## Prerequisites

1. Docker

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

2. Run the build script:

```bash
./scripts/run_local_build.sh -m manifest.yaml
```

## Available Options

| Option | Description | Default | Required |
|--------|-------------|---------|----------|
| `-m` | Path to manifest file | None | Yes |
| `-o` | Output directory for artifacts | `./artifacts` | No |
| `-v` | OpenTelemetry Collector Builder version | `0.121.0` | No |
| `-g` | Go version to use | `1.24.1` | No |
| `-s` | Supervisor version | `0.122.0` | No |
| `-i` | Build ID for artifact storage | Auto-generated | No |
| `-h` | Show help message | N/A | No |

## Example Usage

### Basic Build

```bash
./scripts/run_local_build.sh -m manifest.yaml
```

### Custom Output Directory

```bash
./scripts/run_local_build.sh \
  -m manifest.yaml \
  -o ./dist
```

### Specific Versions

```bash
./scripts/run_local_build.sh \
  -m manifest.yaml \
  -v 0.121.0 \
  -g 1.24.1 \
  -s 0.122.0
```

### Custom Build ID

```bash
./scripts/run_local_build.sh \
  -m manifest.yaml \
  -i custom-build-123
```

## Using Make Commands

The script can also be run using Make commands for convenience:

### Latest Versions

```bash
make build-local
```

This will use the latest versions of otelcol and ocb.

### Custom Versions

```bash
make build output_dir=./artifacts ocb_version=0.121.0 go_version=1.22.1 supervisor_version=0.122.0
```

This allows you to specify custom versions for:

- OpenTelemetry Collector Builder (OCB)
- Supervisor
- Go

## Build Process

1. **Environment Setup**
   - Builds a Docker container with required dependencies
   - Mounts your workspace and artifacts directory
   - Sets up build environment

2. **Build Execution**
   - Processes the manifest file
   - Downloads specified versions of OCB and Go
   - Builds the collector
   - Generates artifacts

3. **Artifact Management**
   - Saves artifacts to specified output directory
   - Creates build metadata
   - Generates SBOMs and checksums

## Output Artifacts

The script generates the following artifacts in your specified output directory:

- Binary distributions (tar.gz)
- Package files (DEB, RPM, APK)
- Docker images
- Configuration files
- Service files
- SBOMs and checksums

## Best Practices

1. **Version Management**
   - Use specific versions for reproducibility
   - Document version requirements
   - Test with different versions

2. **Artifact Organization**
   - Use meaningful output directories
   - Clean up old artifacts
   - Version your builds

3. **Build Process**
   - Monitor build logs
   - Check artifact integrity
   - Verify build outputs

## Troubleshooting

1. **Build Failures**
   - Check manifest syntax
   - Verify Docker is running
   - Review build logs
   - Check disk space

2. **Version Issues**
   - Verify version compatibility
   - Check available versions
   - Review version constraints

3. **Artifact Problems**
   - Check file permissions
   - Verify output directory
   - Review Docker mounts

## Additional Resources

- [OpenTelemetry Collector Documentation](https://opentelemetry.io/docs/collector/)
- [Docker Documentation](https://docs.docker.com/)
- [GitHub Repository](https://github.com/observiq/otel-distro-builder)
- [Issue Tracker](https://github.com/observiq/otel-distro-builder/issues)
