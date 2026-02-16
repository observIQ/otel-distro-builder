# Generate Manifest from Collector Config

This guide explains how to use the OTel Distro Builder to generate an OCB (OpenTelemetry Collector Builder) manifest from an existing OpenTelemetry Collector configuration file.

## Overview

If you already have a running OpenTelemetry Collector with a `config.yaml` file, you can use this feature to:

1. Detect all components (receivers, processors, exporters, extensions, connectors) used in your config
2. Generate a minimal `manifest.yaml` containing only those components
3. Optionally build a custom collector distribution in the same run

You get a smaller, more efficient collector binary that includes only the components you use. **No Docker required**—the CLI runs on your host; for full builds you need Go installed and the CLI downloads OCB automatically.

## Quick Start (Host CLI)

Generate a manifest only, or generate and build in one step:

```bash
# Generate manifest only (prints to stdout)
otel-distro-builder --from-config config.yaml --generate-only

# Generate manifest and save to a file
otel-distro-builder --from-config config.yaml --output-manifest manifest.yaml --generate-only

# Generate manifest and build the distribution
otel-distro-builder --from-config config.yaml --artifacts ./artifacts --platforms linux/amd64,linux/arm64
```

## Other Ways to Run

### Using Make

Make targets wrap the CLI and are convenient for local development:

```bash
# Generate manifest (writes to manifest.yaml if output= is set)
make generate-manifest config=config.yaml output=manifest.yaml

# Generate and print to stdout
make generate-manifest config=config.yaml

# Generate and build in one step
make build-from-config config=config.yaml
```

### Using the generate_manifest.sh Script

The script invokes the CLI with common options:

```bash
# Generate and print to stdout
./scripts/generate_manifest.sh -c config.yaml

# Generate and write to manifest.yaml
./scripts/generate_manifest.sh -c config.yaml -o manifest.yaml

# Custom OpenTelemetry version and distribution name
./scripts/generate_manifest.sh -c config.yaml -v 0.144.0 -n my-collector -o manifest.yaml

# Exclude Bindplane components
./scripts/generate_manifest.sh -c config.yaml -B -o manifest.yaml
```

Run `./scripts/generate_manifest.sh -h` for all options.

### Using Docker

Use Docker for an isolated environment (mount your workspace and artifacts):

```bash
# Generate manifest and save to file
docker run -v $(pwd):/workspace ghcr.io/observiq/otel-distro-builder:main \
  --from-config /workspace/config.yaml \
  --output-manifest /workspace/manifest.yaml \
  --generate-only

# Generate and build
docker run -v $(pwd):/workspace ghcr.io/observiq/otel-distro-builder:main \
  --from-config /workspace/config.yaml \
  --artifacts /workspace/dist \
  --platforms linux/amd64,linux/arm64
```

## CLI Options

### Config-to-Manifest Options

| Option | Description | Default |
|--------|-------------|---------|
| `--from-config` | Path to your collector config.yaml file | Required |
| `--output-manifest` | Path to write the generated manifest | None (prints to stdout if `--generate-only`) |
| `--generate-only` | Only generate manifest, don't build | `false` |
| `--otel-version` | Target OpenTelemetry version | Latest from `versions.yaml` |
| `--dist-name` | Name of the distribution | `otelcol-custom` |
| `--dist-module` | Go module path for the distribution | `github.com/custom/otelcol-distribution` |
| `--dist-version` | Version of the distribution | `1.0.0` |
| `--no-bindplane` | Exclude Bindplane components from the manifest | `false` (components included) |

### Build Options

These options apply when building (omitting `--generate-only`):

| Option | Description | Default |
|--------|-------------|---------|
| `--artifacts` | Directory to copy final artifacts to | `<cwd>/artifacts` |
| `--platforms` | Comma-separated GOOS/GOARCH (e.g., `linux/amd64,darwin/arm64`) | From manifest |
| `--goos` | Target operating systems (overrides manifest) | Derived from platforms |
| `--goarch` | Target architectures (overrides manifest) | Derived from platforms |
| `--ocb-version` | OpenTelemetry Collector Builder version | Detected from manifest |
| `--supervisor-version` | Supervisor version | Detected from manifest |
| `--go-version` | Go version for build | From manifest/versions.yaml |
| `--parallelism` | Number of parallel Goreleaser build tasks | `4` |

## Example

### Input: config.yaml

```yaml
extensions:
  health_check:
    endpoint: 0.0.0.0:13133

receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318
  
  prometheus:
    config:
      scrape_configs:
        - job_name: 'app'
          static_configs:
            - targets: ['localhost:8080']

processors:
  batch:
    timeout: 1s
  
  attributes:
    actions:
      - key: environment
        value: production
        action: insert

exporters:
  otlp:
    endpoint: backend:4317
  
  debug:
    verbosity: detailed

service:
  extensions: [health_check]
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch, attributes]
      exporters: [otlp, debug]
    metrics:
      receivers: [otlp, prometheus]
      processors: [batch]
      exporters: [otlp]
```

### Generated: manifest.yaml

```yaml
# OpenTelemetry Collector Builder (OCB) Manifest
# Generated from collector config.yaml
# Target version: 0.121.0

dist:
  module: github.com/custom/otelcol-distribution
  name: otelcol-custom
  description: Custom OpenTelemetry Collector distribution
  version: 1.0.0
  output_path: ./_build

conf_resolver:
  default_uri_scheme: env

extensions:
  - gomod: github.com/open-telemetry/opentelemetry-collector-contrib/extension/healthcheckextension v0.121.0

receivers:
  - gomod: go.opentelemetry.io/collector/receiver/otlpreceiver v0.121.0
  - gomod: github.com/open-telemetry/opentelemetry-collector-contrib/receiver/prometheusreceiver v0.121.0

processors:
  - gomod: go.opentelemetry.io/collector/processor/batchprocessor v0.121.0
  - gomod: github.com/open-telemetry/opentelemetry-collector-contrib/processor/attributesprocessor v0.121.0

exporters:
  - gomod: go.opentelemetry.io/collector/exporter/otlpexporter v0.121.0
  - gomod: go.opentelemetry.io/collector/exporter/debugexporter v0.121.0

providers:
  - gomod: go.opentelemetry.io/collector/confmap/provider/envprovider v1.27.0
  - gomod: go.opentelemetry.io/collector/confmap/provider/fileprovider v1.27.0
  - gomod: go.opentelemetry.io/collector/confmap/provider/httpprovider v1.27.0
  - gomod: go.opentelemetry.io/collector/confmap/provider/httpsprovider v1.27.0
  - gomod: go.opentelemetry.io/collector/confmap/provider/yamlprovider v1.27.0

replaces:
  - github.com/googleapis/gnostic v0.5.6 => github.com/googleapis/gnostic v0.5.5
  # ... additional replaces
```

## Bindplane Components

By default, generated manifests include all Bindplane components. This provides access to additional receivers, processors, and exporters developed by Bindplane.

### Included Bindplane Components

- **Extensions**: bindplaneextension
- **Receivers**: awss3rehydration, azureblobrehydration, http, m365, okta, plugin, route, sapnetweaver, splunksearchapi, telemetrygenerator
- **Processors**: datapointcount, logcount, lookup, mask, metricextract, metricstats, removeemptyvalues, resourceattributetransposer, sampling, snapshot, spancount, throughputmeasurement, topology, unroll
- **Exporters**: azureblob, chronicle, chronicleforwarder, googlecloud, googlecloudstorage, googlemanagedprometheus, qradar, snowflake

### Excluding Bindplane Components

To generate a manifest with only standard OpenTelemetry components, use `--no-bindplane`:

```bash
# CLI: generate manifest without Bindplane components
otel-distro-builder --from-config config.yaml --output-manifest manifest.yaml --generate-only --no-bindplane

# Or using the shell script
./scripts/generate_manifest.sh -c config.yaml -o manifest.yaml -B
```

## Supported Components

The builder includes mappings for:

- **Core components**: Built-in receivers, processors, exporters from the OpenTelemetry Collector core
- **Contrib components**: Components from the OpenTelemetry Collector Contrib repository
- **Bindplane components**: Custom components from the Bindplane collector (included by default)

### Component Name Mapping

Components in your config.yaml are mapped to their Go module paths. For example:

| Config Name | Go Module |
|-------------|-----------|
| `otlp` (receiver) | `go.opentelemetry.io/collector/receiver/otlpreceiver` |
| `prometheus` (receiver) | `github.com/open-telemetry/opentelemetry-collector-contrib/receiver/prometheusreceiver` |
| `batch` (processor) | `go.opentelemetry.io/collector/processor/batchprocessor` |
| `debug` (exporter) | `go.opentelemetry.io/collector/exporter/debugexporter` |

### Named Instances

The builder correctly handles named instances. For example, if your config has:

```yaml
receivers:
  otlp/traces:
    protocols:
      grpc:
  otlp/metrics:
    protocols:
      http:
```

Both will be recognized as using the `otlp` receiver, and only one gomod entry will be added.

## Handling Unknown Components

If your config contains components that aren't in the registry, the builder will:

1. Log a warning with the unknown component name
2. Suggest similar component names if a close match exists
3. Continue generating the manifest (unknown components will be listed in warnings)

You can then manually add the missing component's gomod to the generated manifest.

## Customization

### Custom Component Mappings

If you're using custom components not in the registry, you can:

1. Generate the manifest with `--generate-only`
2. Manually add the missing gomod entries to the generated manifest
3. Build using the modified manifest with `--manifest`

### Modifying the Generated Manifest

The generated manifest is a standard OCB manifest. You can edit it to:

- Add additional components
- Change versions
- Add custom `replaces` directives
- Modify the distribution settings

## Troubleshooting

### "Unknown receiver/processor/exporter" Warning

This means the component name in your config doesn't match any known component in the registry. Check:

1. The spelling matches the official component name
2. The component exists in the version you're targeting
3. For custom components, manually add the gomod entry

### Version Mismatch

If you get build errors related to versions, try:

1. Using a different `--otel-version` that matches your config
2. Checking the [OpenTelemetry Collector releases](https://github.com/open-telemetry/opentelemetry-collector/releases) for compatible versions

### Missing Dependencies

Some components have additional dependencies. If the build fails, check:

1. The component's documentation for required dependencies
2. Add any necessary `replaces` directives to the manifest
