# Using the Local Multi-Arch Build Script

This guide explains how to build custom OpenTelemetry Collector distributions for **multiple architectures** in a single run using `run_local_build.sh` with the `-p` (platforms) option.

## When to Use Multi-Arch Builds

Use `run_local_build.sh -p <platforms>` when you need collector binaries for several platforms (e.g. linux/amd64, linux/arm64, darwin/arm64) from one command. The script builds one Docker image for your host architecture (to avoid emulation issues) and runs the builder so it produces artifacts for all requested platforms.

For a single platform, run `run_local_build.sh` without `-p` (default: linux/arm64). See [Using the Local Build Script](./local-build-script.md).

## Prerequisites

1. Docker

## Quick Start

1. Create a manifest file (`manifest.yaml`) that defines your collector configuration (same as for the standard local build):

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

2. Run the build script with `-p` to target multiple platforms:

```bash
./scripts/run_local_build.sh -m manifest.yaml -p linux/amd64,darwin/amd64,linux/arm64,darwin/arm64
```

This builds the collector for linux and darwin (amd64 and arm64) and writes artifacts to `./artifacts`. Omit `-p` for a single-arch build (default: linux/arm64).

## How It Works

1. **Docker image**: The script builds a Docker image for your **host** architecture (e.g. linux/arm64 on Apple Silicon, linux/amd64 on Intel). This avoids running under QEMU emulation, which can cause the OpenTelemetry Collector Builder (OCB) to crash.
2. **Collector targets**: The builder runs inside the container with `--platforms` set to your requested list. Goreleaser then builds the collector for each platform (linux/amd64, linux/arm64, darwin/arm64, etc.) in one go.
3. **Artifacts**: All binaries and packages are written to your chosen output directory (default: `./artifacts`).

## Available Options

| Option | Description | Default | Required |
|--------|-------------|---------|----------|
| `-m` | Path to manifest file | None | Yes |
| `-o` | Output directory for artifacts | `./artifacts` | No |
| `-p` | Comma-delimited GOOS/GOARCH for collector binaries (omit for single-arch: linux/arm64) | None (single-arch) | No |
| `-n` | Number of parallel Goreleaser build tasks (use 1 to reduce memory) | Builder default (4) | No |
| `-v` | OpenTelemetry Collector Builder version | From manifest | No |
| `-g` | Go version to use | From manifest/versions.yaml | No |
| `-s` | Supervisor version | From manifest | No |
| `-h` | Show help message | N/A | No |

The `-p` value is passed to the builder as `--platforms` and defines which OS/architecture combinations to build (e.g. `linux/amd64,linux/arm64,darwin/arm64`). The Docker image used to run the builder is always built for your host (linux/arm64 or linux/amd64). For multi-arch, always pass `-p`; `make multiarch-build` uses a default platform list.

## Example Usage

### Default Multi-Arch Platforms (Make)

Use `make multiarch-build` to build for the default multi-arch list (linux/amd64, darwin/amd64, linux/arm64, darwin/arm64). Or pass `-p` explicitly:

```bash
./scripts/run_local_build.sh -m manifest.yaml -p linux/amd64,darwin/amd64,linux/arm64,darwin/arm64
```

### Custom Platforms

Build only for linux/amd64 and linux/arm64:

```bash
./scripts/run_local_build.sh -m manifest.yaml -p linux/amd64,linux/arm64
```

Build for linux and darwin, both amd64 and arm64:

```bash
./scripts/run_local_build.sh -m manifest.yaml -p linux/amd64,linux/arm64,darwin/amd64,darwin/arm64
```

### Custom Output Directory

```bash
./scripts/run_local_build.sh -m manifest.yaml -p linux/amd64,linux/arm64 -o ./dist
```

### Specific Versions

```bash
./scripts/run_local_build.sh -m manifest.yaml -p linux/amd64,linux/arm64 \
  -v 0.121.0 \
  -s 0.122.0 \
  -g 1.24.0
```

### Reduce Memory Use (Parallelism)

If the build runs out of memory, lower parallelism (e.g. `-n 1`):

```bash
./scripts/run_local_build.sh -m manifest.yaml -p linux/amd64,linux/arm64 -n 1
```

### Combined Options

```bash
./scripts/run_local_build.sh -m manifest.yaml \
  -o ./dist \
  -p linux/amd64,linux/arm64,darwin/arm64 \
  -n 4 \
  -v 0.121.0 -s 0.122.0 -g 1.24.0
```

## Using Make Commands

You can run multi-arch builds via Make (both use `run_local_build.sh -p` under the hood):

### Multi-arch with pinned versions

```bash
make multiarch-build-local
```

This runs `run_local_build.sh` with default multi-arch platforms and pinned OCB, Supervisor, and Go versions.

### Multi-arch with optional parameters

```bash
make multiarch-build
```

Override as needed:

```bash
make multiarch-build output_dir=./artifacts platforms=linux/amd64,linux/arm64 ocb_version=0.121.0
```

## Build Process

1. **Host detection**: The script detects your host architecture (arm64 or amd64) and chooses the Docker image platform (linux/arm64 or linux/amd64) so the container runs natively.
2. **Image build**: A Docker image is built for that platform and tagged as `otel-distro-builder`.
3. **Builder run**: The container runs with your manifest, `--platforms` set to your target list, and optional version/parallelism flags.
4. **Artifact generation**: The builder produces binaries and packages for each platform and copies them to your output directory.

## Output Artifacts

The script produces the same kinds of artifacts as the standard build, but for each target platform:

- Binary distributions (tar.gz) per platform
- Package files (DEB, RPM, APK) where applicable
- Configuration and service files
- SBOMs and checksums

All are written to the directory specified with `-o` (default: `./artifacts`).

## Best Practices

1. **Platform list**: Use `-p` only when you need a subset of platforms; otherwise the default is usually sufficient.
2. **Memory**: For large manifests or many platforms, use `-n 1` or increase Docker/host memory to avoid OOM.
3. **Versions**: Pin OCB, Supervisor, and Go with `-v`, `-s`, and `-g` for reproducible builds.
4. **Output**: Use a dedicated directory (e.g. `-o ./dist`) so multi-arch artifacts don’t mix with single-arch builds.

## Troubleshooting

1. **SIGSEGV or OCB crash**
   - The script builds the Docker image for your host arch to avoid QEMU. If you still see crashes, ensure you’re not overriding the image platform; the script chooses it automatically.

2. **Out of memory**
   - Use `-n 1` to limit parallel Goreleaser tasks, and/or increase Docker Desktop memory (e.g. 6–8 GB for many platforms).

3. **Build failures**
   - Check manifest syntax, that Docker is running, and review the builder logs. See [Docker documentation](./docker.md) for more troubleshooting.

4. **Wrong platforms**
   - Confirm `-p` is a comma-separated list of `GOOS/GOARCH` (e.g. `linux/amd64,darwin/arm64`). No spaces.

## Testing the Scripts

To verify the scripts work without running a full Docker build:

1. **Script smoke tests** (no Docker): run `make script-test`. This checks that each script prints help, enforces required arguments, and that `generate_manifest.sh` can produce a manifest from the test config.
2. **Unit tests**: run `make unit-test` to test platform parsing and main CLI logic used by the builder.
3. **Full integration**: with Docker running, use a small manifest and one platform to confirm the pipeline end-to-end, e.g. `./scripts/run_local_build.sh -m manifest.yaml -p linux/amd64 -o ./artifacts-test`.

## Additional Resources

- [Using the Local Build Script](./local-build-script.md) – single-platform local builds
- [Docker documentation](./docker.md) – builder options and troubleshooting
- [OpenTelemetry Collector Documentation](https://opentelemetry.io/docs/collector/)
- [GitHub Repository](https://github.com/observiq/otel-distro-builder)
- [Issue Tracker](https://github.com/observiq/otel-distro-builder/issues)
