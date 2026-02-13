# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpenTelemetry Distribution Builder (`otel-distro-builder`) is a Python CLI tool that builds custom OpenTelemetry Collector distributions. It wraps the OpenTelemetry Collector Builder (OCB) to produce packaged binaries (APK, DEB, RPM, TAR.GZ) with SBOMs and checksums. No Docker required for CLI execution.

## Common Commands

### Development Setup
```bash
make setup                    # Full dev environment setup (venv + deps)
source builder/.venv/bin/activate  # Activate virtualenv
```

### Quality Checks
```bash
make format         # Format with black + isort
make lint           # Pylint (PYTHONPATH=builder/src)
make type-check     # mypy on builder/src
make shell-check    # shellcheck on scripts/*.sh
make quality        # All of the above
```

### Testing
```bash
make test           # All tests
make unit-test      # Unit tests only (pytest -m "unit")
make build-test     # Build integration tests (pytest -m "build")
make script-test    # Shell script smoke tests

# Run a single test file:
PYTHONPATH=builder/src builder/.venv/bin/pytest builder/tests/test_platforms.py -v

# Run a single test by name:
PYTHONPATH=builder/src builder/.venv/bin/pytest builder/tests/test_version.py -v -k "test_determine_build_versions"
```

Note: `PYTHONPATH=builder/src` is required when running pytest directly.

### Building
```bash
make build                                    # Build from manifest.yaml
make generate-manifest config=config.yaml     # Generate manifest from collector config
make build-from-config config=config.yaml     # Generate manifest + build in one step
make build-cli                                # Build standalone PyInstaller binary
```

## Architecture

### Two Execution Modes

The CLI (`builder/src/main.py`) has two mutually exclusive entry paths:

1. **`--manifest`**: Reads a pre-written OCB manifest YAML and builds directly
2. **`--from-config`**: Takes a collector `config.yaml`, reverse-engineers which components are needed, generates an OCB manifest, then builds (or stops with `--generate-only`)

### Module Dependency Flow

```
main.py  ─────────────────────────────────────────────┐
  ├── build.py (orchestration)                        │
  │     ├── ocb_downloader.py (downloads OCB binary)  │
  │     ├── supervisor_downloader.py                  │
  │     └── version.py (OCB/Go/Supervisor versioning) │
  ├── manifest_generator.py (config → manifest)       │
  │     ├── config_parser.py (extracts components)    │
  │     └── component_registry.py (Go module lookup)  │
  ├── platforms.py (GOOS/GOARCH resolution)           │
  └── resources.py (package data path resolution)     │
       └── handles both dev and PyInstaller contexts  ┘
```

### Key Data Files (in builder/src/)

- **`components.yaml`** (~32KB): Registry mapping component names to Go module paths for all core/contrib OTel components
- **`bindplane_components.yaml`**: Bindplane-specific component mappings
- **`versions.yaml`** (in builder/): Maps OCB versions to compatible Go and Supervisor versions (24+ versions)

### Build Pipeline (build.py)

1. Parse manifest → 2. Resolve platform pairs → 3. Determine OCB/Go versions → 4. Download OCB binary → 5. Generate Go sources via OCB → 6. Build binaries with goreleaser → 7. Generate SBOMs with syft → 8. Create checksums → 9. Collect artifacts

### Template Files (builder/templates/)

Goreleaser config, Dockerfile, systemd/launchd service files, and install/remove hooks used during the packaging phase.

## Code Conventions

- Full type annotations throughout; enforced by mypy
- Max line length: 120 (black formatting)
- Dataclasses for config/result objects (`BuildContext`, `BuildMetrics`, `ManifestConfig`, `ParsedComponents`, etc.)
- Test markers: `@pytest.mark.unit`, `@pytest.mark.build`, `@pytest.mark.release`
- Test fixtures in `builder/tests/configs/` (collector configs) and `builder/tests/manifests/`
- `resources.py` abstracts path resolution to work in both development and PyInstaller-frozen contexts (`sys._MEIPASS`)

## CI Workflows (.github/workflows/)

- **base-tests.yml**: Runs on push/PR — quality checks, unit tests, simple build test
- **build-cli-binaries.yml**: Triggered on version tags — builds PyInstaller binaries for linux/amd64, linux/arm64, darwin/arm64
- **release.yml**: Triggered on version tags — builds wheel/sdist, creates GitHub Release
