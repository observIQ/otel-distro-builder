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
  -v "$(pwd)/manifest.yaml:/manifest.yaml:ro" \
  -v "$(pwd)/artifacts:/artifacts" \
  ghcr.io/observiq/otel-distro-builder:main \
  --manifest /manifest.yaml \
  --artifacts /artifacts
```

## Available Options

The Docker container accepts the following command-line options:

| Option                 | Description                             | Default      |
| ---------------------- | --------------------------------------- | ------------ |
| `--manifest`           | Path to manifest file                   | Required     |
| `--artifacts`          | Output directory for artifacts          | `<cwd>/artifacts` |
| `--platforms`          | Comma-separated GOOS/GOARCH (e.g. linux/amd64,linux/arm64) | (from manifest) |
| `--goos`               | Target operating system                 | `linux`      |
| `--goarch`             | Target architecture                     | `amd64`      |
| `--ocb-version`        | OpenTelemetry Collector Builder version | `0.122.0`    |
| `--go-version`         | Go version to use                       | `1.24.0`     |
| `--supervisor-version` | Supervisor version                      | `0.122.0`    |
| `--parallelism`        | Number of parallel Goreleaser build tasks (lower to reduce memory) | `4` |

## Volume Mounts

When running the container, mount the manifest file and an artifacts directory:

1. **Manifest** (read-only): Mount your manifest file into the container.

   ```bash
   -v "$(pwd)/manifest.yaml:/manifest.yaml:ro"
   ```

2. **Artifacts**: Mount a host directory at `/artifacts` so build outputs are written back to the host.

   ```bash
   -v "$(pwd)/artifacts:/artifacts"
   ```

> **Important:** Always pass `--artifacts /artifacts` to ensure the builder writes to the mounted volume. Without it, artifacts are written to the container's working directory (`/app/artifacts`) and will be lost when the container exits.

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
  -v "$(pwd)/manifest.yaml:/manifest.yaml:ro" \
  -v "$(pwd)/artifacts:/artifacts" \
  ghcr.io/observiq/otel-distro-builder:main \
  --manifest /manifest.yaml \
  --artifacts /artifacts
```

### Custom Platform Build

Use `--platforms` with a comma-separated list of `GOOS/GOARCH` (e.g. `linux/amd64`, `darwin/arm64`). This is the recommended way to specify target platforms.

```bash
# Single platform: Apple Silicon (darwin/arm64)
docker run --rm \
  -v "$(pwd)/manifest.yaml:/manifest.yaml:ro" \
  -v "$(pwd)/artifacts:/artifacts" \
  ghcr.io/observiq/otel-distro-builder:main \
  --manifest /manifest.yaml \
  --artifacts /artifacts \
  --platforms darwin/arm64

# Linux only: amd64 and arm64
docker run --rm \
  -v "$(pwd)/manifest.yaml:/manifest.yaml:ro" \
  -v "$(pwd)/artifacts:/artifacts" \
  ghcr.io/observiq/otel-distro-builder:main \
  --manifest /manifest.yaml \
  --artifacts /artifacts \
  --platforms linux/amd64,linux/arm64

# Linux + Darwin (common server and Mac targets)
docker run --rm \
  -v "$(pwd)/manifest.yaml:/manifest.yaml:ro" \
  -v "$(pwd)/artifacts:/artifacts" \
  ghcr.io/observiq/otel-distro-builder:main \
  --manifest /manifest.yaml \
  --artifacts /artifacts \
  --platforms linux/amd64,linux/arm64,darwin/amd64,darwin/arm64

# Include Windows (amd64)
docker run --rm \
  -v "$(pwd)/manifest.yaml:/manifest.yaml:ro" \
  -v "$(pwd)/artifacts:/artifacts" \
  ghcr.io/observiq/otel-distro-builder:main \
  --manifest /manifest.yaml \
  --artifacts /artifacts \
  --platforms linux/amd64,linux/arm64,darwin/arm64,windows/amd64
```

Alternatively, use `--goos` and `--goarch` to specify target OS and architecture lists (builder builds the Cartesian product):

```bash
# ARM64 only (darwin, linux, windows)
docker run --rm \
  -v "$(pwd)/manifest.yaml:/manifest.yaml:ro" \
  -v "$(pwd)/artifacts:/artifacts" \
  ghcr.io/observiq/otel-distro-builder:main \
  --manifest /manifest.yaml \
  --artifacts /artifacts \
  --goos darwin,linux,windows \
  --goarch arm64

# AMD64 only
docker run --rm \
  -v "$(pwd)/manifest.yaml:/manifest.yaml:ro" \
  -v "$(pwd)/artifacts:/artifacts" \
  ghcr.io/observiq/otel-distro-builder:main \
  --manifest /manifest.yaml \
  --artifacts /artifacts \
  --goos darwin,linux,windows \
  --goarch amd64
```

### Specific Version Build

```bash
docker run --rm \
  -v "$(pwd)/manifest.yaml:/manifest.yaml:ro" \
  -v "$(pwd)/artifacts:/artifacts" \
  ghcr.io/observiq/otel-distro-builder:main \
  --manifest /manifest.yaml \
  --artifacts /artifacts \
  --ocb-version 0.121.0 \
  --go-version 1.24.0 \
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
