# Using otel-distro-builder with Docker

This guide explains how to use `otel-distro-builder` with Docker to build custom OpenTelemetry Collector distributions.

## Quick Start

1. Pull the latest otel-builder image:
```bash
docker pull ghcr.io/observiq/otel-builder:main
```

2. Create a manifest file (`manifest.yaml`) that defines your collector configuration:
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

3. Run the builder:
```bash
docker run --rm \
  -v $(pwd):/workspace \
  -v $(pwd)/build:/build \
  ghcr.io/observiq/otel-builder:main \
  --manifest /workspace/manifest.yaml \
  --artifacts /workspace/artifacts  
```

## Available Options

The Docker container accepts the following command-line options:

| Option | Description | Default |
|--------|-------------|---------|
| `--manifest` | Path to manifest file | Required |
| `--artifacts` | Output directory for artifacts | `/artifacts` |
| `--goos` | Target operating system | `linux` |
| `--goarch` | Target architecture | `amd64` |
| `--ocb-version` | OpenTelemetry Collector Builder version | `0.121.0` |
| `--go-version` | Go version to use | `1.24.1` |
| `--supervisor-version` | Supervisor version | `0.122.0` |

## Using Local Build Script

The repository includes a convenient script for local builds:

```bash
./scripts/run_local_build.sh -m manifest.yaml \
  [-o output_dir] \
  [-v ocb_version] \
  [-g go_version] \
  [-s supervisor_version]
```

Example:
```bash
./scripts/run_local_build.sh \
  -m manifest.yaml \
  -o ./artifacts \
  -v 0.121.0 \
  -g 1.24.1 \
  -s 0.122.0
```

## Volume Mounts

When running the container, you need to mount two volumes:

1. **Workspace Volume**: Contains your manifest file, source files, and the output artifacts directory
   ```bash
   -v $(pwd):/workspace
   ```

2. **Build Volume**: Where the build is stored
   ```bash
   -v $(pwd)/build:/build
   ```

## Output Artifacts

The builder will generate the following artifacts in your specified output directory:

- Binary distributions (tar.gz)
- Package files (DEB, RPM, APK)
- Docker images
- Configuration files
- Service files

## Example Usage

### Basic Build
```bash
docker run --rm \
  -v $(pwd):/workspace \
  -v $(pwd)/build:/build \
  ghcr.io/observiq/otel-builder:main \
  --manifest /workspace/manifest.yaml
```

### Custom Platform Build
```bash
docker run --rm \
  -v $(pwd):/workspace \
  -v $(pwd)/build:/build \
  ghcr.io/observiq/otel-builder:main \
  --manifest /workspace/manifest.yaml \
  --goos linux \
  --goarch arm64
```

### Specific Version Build
```bash
docker run --rm \
  -v $(pwd):/workspace \
  -v $(pwd)/build:/build \
  ghcr.io/observiq/otel-builder:main \
  --manifest /workspace/manifest.yaml \
  --ocb-version 0.121.0 \
  --go-version 1.24.1 \
  --supervisor-version 0.122.0
```

## Troubleshooting

1. **Permission Issues**
   - Ensure the output directory has the correct permissions
   - The container runs as a non-root user (UID 10001)

2. **Volume Mount Issues**
   - Verify the paths are correct and accessible
   - Check if SELinux or AppArmor are blocking access

3. **Build Failures**
   - Check the manifest file syntax
   - Verify all required components are specified
   - Check the logs for specific error messages

## Best Practices

1. **Version Pinning**
   - Always specify exact versions for OCB, Go, and Supervisor
   - This ensures reproducible builds

2. **Artifact Management**
   - Use a dedicated artifacts directory
   - Clean up old artifacts before new builds

3. **Security**
   - Review your manifest file for security implications
   - Use specific versions instead of latest tags
   - Consider using Docker's security scanning features

## Additional Resources

- [OpenTelemetry Collector Documentation](https://opentelemetry.io/docs/collector/)
- [GitHub Repository](https://github.com/observiq/otel-builder)
- [Issue Tracker](https://github.com/observiq/otel-builder/issues)
