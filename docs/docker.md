# Using otel-distro-builder with Docker

This guide explains how to use `otel-distro-builder` with Docker to build custom OpenTelemetry Collector distributions.

## Prerequisites

1. Docker

## Quick Start

1. Pull the latest otel-distro-builder image:

```bash
docker pull ghcr.io/observiq/otel-distro-builder:main
```

2. Create a manifest file (`manifest.yaml`) that defines your collector configuration:

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

3. Run the builder:

```bash
docker run --rm \
  -v $(pwd):/workspace \
  -v $(pwd)/build:/build \
  ghcr.io/observiq/otel-distro-builder:main \
  --manifest /workspace/manifest.yaml \
  --artifacts /workspace/artifacts
```

## Available Options

The Docker container accepts the following command-line options:

| Option                 | Description                             | Default      |
| ---------------------- | --------------------------------------- | ------------ |
| `--manifest`           | Path to manifest file                   | Required     |
| `--artifacts`          | Output directory for artifacts          | `/artifacts` |
| `--platforms`          | Comma-separated GOOS/GOARCH (e.g. linux/amd64,linux/arm64) | (from manifest) |
| `--goos`               | Target operating system                 | `linux`      |
| `--goarch`             | Target architecture                     | `amd64`      |
| `--ocb-version`        | OpenTelemetry Collector Builder version | `0.122.0`    |
| `--go-version`         | Go version to use                       | `1.24.1`     |
| `--supervisor-version` | Supervisor version                      | `0.122.0`    |
| `--parallelism`        | Number of parallel Goreleaser build tasks (lower to reduce memory) | `4` |

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
  ghcr.io/observiq/otel-distro-builder:main \
  --manifest /workspace/manifest.yaml
```

### Custom Platform Build

```bash
# ARM64
docker run --rm \
  -v "$(pwd)/manifest.yaml:/manifest.yaml:ro" \
  -v "$(pwd)/artifacts:/artifacts" \
  ghcr.io/observiq/otel-distro-builder:main \
  --manifest /manifest.yaml \
  --artifacts /artifacts \
  --goos darwin,linux,windows \
  --goarch arm64

#AMD64
docker run --rm \
  -v "$(pwd)/manifest.yaml:/manifest.yaml:ro" \
  -v "$(pwd)/artifacts:/artifacts" \
  ghcr.io/observiq/otel-distro-builder:main \
  --manifest /manifest.yaml \
  --artifacts /artifacts \
  --goos windows,linux,windows \
  --goarch amd64
```

### Specific Version Build

```bash
docker run --rm \
  -v $(pwd):/workspace \
  -v $(pwd)/build:/build \
  ghcr.io/observiq/otel-distro-builder:main \
  --manifest /workspace/manifest.yaml \
  --ocb-version 0.121.0 \
  --go-version 1.24.1 \
  --supervisor-version 0.122.0
```

### Controlling Build Parallelism

Use `--parallelism` to control how many Goreleaser build targets run at once. Lower values reduce peak memory use; higher values can speed up builds when you have enough RAM.

```bash
# Reduce memory use (e.g. for constrained environments or to avoid OOM)
docker run --rm \
  -v "$(pwd)/manifest.yaml:/manifest.yaml:ro" \
  -v "$(pwd)/artifacts:/artifacts" \
  ghcr.io/observiq/otel-distro-builder:main \
  --manifest /manifest.yaml \
  --artifacts /artifacts \
  --parallelism 1

# Use more parallelism when you have sufficient memory (default is 4)
docker run --rm \
  -v "$(pwd)/manifest.yaml:/manifest.yaml:ro" \
  -v "$(pwd)/artifacts:/artifacts" \
  ghcr.io/observiq/otel-distro-builder:main \
  --manifest /manifest.yaml \
  --artifacts /artifacts \
  --parallelism 8
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

4. **Goreleaser build killed (signal: killed / OOM)**

   If the release step fails with errors like *`/usr/local/go-versions/go1.x/pkg/tool/linux_arm64/compile: signal: killed`* when building large dependencies (e.g. elasticsearch, datadog, aws-sdk), the Go compiler process was likely killed by the system OOM killer due to memory limits.

   The builder accepts `--parallelism N` (default 4). Use a lower value (e.g. `--parallelism 1`) to reduce peak memory and avoid OOM. If you still hit OOM:

   - **Docker:** Increase memory for the Docker engine (e.g. Docker Desktop → Settings → Resources → Memory). Try at least 4–6 GB for collector builds with many components.
   - **Local / CI:** Ensure the environment has enough RAM; cross-compiling multiple targets with large dependencies can use several GB.

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
- [GitHub Repository](https://github.com/observiq/otel-distro-builder)
- [Issue Tracker](https://github.com/observiq/otel-distro-builder/issues)
