# OTel Builder Tests

This directory contains integration tests for the OpenTelemetry Collector builder system.

## Structure

- `test_build.py`: Main test framework using pytest
- `manifests/`: Test manifest files
  - `contrib-0.117.0.yaml`: Test manifest for contrib collector v0.117.0
  - `contrib-0.116.0.yaml`: Test manifest for contrib collector v0.116.0

## Running Tests

1. Install development dependencies:

```bash
pip install -r ../requirements-dev.txt
```

2. Run tests:

```bash
pytest test_build.py -v
```

## Adding New Test Cases

1. Add new manifest files to the `manifests/` directory
2. The test framework will automatically discover and test them

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
