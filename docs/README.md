# OpenTelemetry Distribution Builder Documentation

This directory contains comprehensive documentation for using `otel-distro-builder` to create custom OpenTelemetry Collector distributions.

## Available Guides

### [Using the Local Build Script](local-build-script.md)

Learn how to use the `run_local_build.sh` script for local builds. This guide covers:

- Running builds with the script
- Available command-line options
- Using Make commands
- Managing artifacts
- Troubleshooting common issues

### [Using the Local Multi-Arch Build Script](local-multiarch-build-script.md)

Learn how to use the `run_local_multiarch_build.sh` script to build collector binaries for multiple architectures in one run. This guide covers:

- When to use multi-arch vs single-platform builds
- How the script chooses the Docker image platform (host-native)
- Available options (`-m`, `-o`, `-p`, `-n`, `-v`, `-g`, `-s`)
- Using Make targets (`multiarch-build-local`, `multiarch-build`)
- Troubleshooting (SIGSEGV, OOM, platform list)

### [Using `otel-distro-builder` with Docker](docker.md)

Learn how to build custom OpenTelemetry Collector distributions using Docker. This guide covers:

- Setting up your environment
- Creating manifest files
- Running builds with Docker
- Managing artifacts
- Troubleshooting common issues

### [Using `otel-distro-builder` with GitHub Actions](github-actions.md)

Learn how to integrate `otel-distro-builder` into your CI/CD pipeline using GitHub Actions. This guide covers:

- Setting up GitHub Actions workflows
- Configuring the `otel-distro-builder` action
- Managing releases and artifacts
- Multi-platform builds
- Best practices and troubleshooting

### [Using `otel-distro-builder` with Google Cloud Build](google-cloud-build.md)

Learn how to use `otel-distro-builder` with Google Cloud Build for enterprise-scale builds. This guide covers:

- Setting up Google Cloud Build
- Configuring build pipelines
- Managing artifacts in Google Cloud Storage
- Security and permissions
- Cost optimization and best practices

## Quick Links

- [Main Repository README](../README.md)
- [OpenTelemetry Collector Documentation](https://opentelemetry.io/docs/collector/)
- [GitHub Repository](https://github.com/observiq/otel-distro-builder)
- [Issue Tracker](https://github.com/observiq/otel-distro-builder/issues)

## Contributing to Documentation

If you find any issues or have suggestions for improving the documentation, please:

1. Open an issue in the [GitHub repository](https://github.com/observiq/otel-distro-builder/issues)
2. Submit a pull request with your proposed changes
3. Follow the existing documentation style and format

## Documentation Structure

```text
docs/
├── README.md                    # This landing page
├── local-build-script.md        # Local build script guide
├── local-multiarch-build-script.md  # Local multi-arch build script guide
├── docker.md                   # Docker usage guide
├── github-actions.md           # GitHub Actions usage guide
└── google-cloud-build.md       # Google Cloud Build usage guide
```
