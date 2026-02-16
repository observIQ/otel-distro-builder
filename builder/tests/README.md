# OTel Builder Tests

This directory contains unit and integration tests for the OpenTelemetry Collector builder (config parsing, manifest generation, platforms, version resolution, and optional full builds).

## Structure

- **Unit tests** (e.g. `test_*.py`): Config parser, manifest generator, platforms, version logic
- **Manifests** (`manifests/`): Test manifest files (e.g. `contrib-0.117.0.yaml`, `contrib-0.116.0.yaml`)
- **Configs** (`configs/`): Sample collector configs for config-to-manifest tests (see `configs/README.md`)

## Running Tests

From the repository root:

```bash
make test          # All tests
make unit-test     # Unit tests only (pytest -m "unit")
make build-test    # Build integration tests (pytest -m "build")
make script-test   # Shell script smoke tests
```

To run pytest directly, set `PYTHONPATH` so the builder package is importable:

```bash
PYTHONPATH=builder/src builder/.venv/bin/pytest builder/tests -v

# Single file or test
PYTHONPATH=builder/src builder/.venv/bin/pytest builder/tests/test_platforms.py -v
PYTHONPATH=builder/src builder/.venv/bin/pytest builder/tests/test_version.py -v -k "test_determine_build_versions"
```

Or activate the venv and set `PYTHONPATH`:

```bash
make setup
source builder/.venv/bin/activate
PYTHONPATH=builder/src pytest builder/tests -v
```

## Adding New Test Cases

- **Manifest-based tests**: Add manifest files to `manifests/`; the build test framework can use them.
- **Unit tests**: Add tests in `builder/tests/` and use markers: `@pytest.mark.unit`, `@pytest.mark.build`, or `@pytest.mark.release` as appropriate.
- **Config-to-manifest tests**: Add sample configs under `configs/otelcol/` (see `configs/README.md`).

## Test Verification

The test framework verifies:

- Build process completion
- Presence of required files:
  - Package files (.deb, .rpm, .apk, .tar.gz)
  - SBOM files
  - Checksums
  - Binary directories

## Debugging

The test framework provides detailed output including:

- Build process output
- Artifact directory contents
- Directory permissions
- Error messages
