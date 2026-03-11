# Test configuration samples

Sample configs used by tests and scripts.

## `otelcol/`

OpenTelemetry Collector (otelcol) configs for config-to-manifest and parser tests:

- **simple.yaml** – OTLP + batch + debug pipelines
- **minimal.yaml** – Nop components only
- **complex.yaml** – Extensions, multiple receivers/processors/exporters, connectors
- **named_instances.yaml** – Named instances (e.g. `otlp/traces`, `batch/fast`)

## `supervisor/`

OpAMP Supervisor configs (for reference and future tests):

- **minimal.yaml** – Minimal supervisor config (no remote server)
- **sample.yaml** – Sample with OpAMP server and capabilities

> **Note:** The packaged template at `builder/templates/supervisor_config.yaml` includes a commented Bindplane sample (endpoint, headers, TLS) for production use.
