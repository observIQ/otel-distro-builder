"""Tests for version parsing functionality."""

import pytest
import yaml
from src.version import (
    MIN_SUPERVISOR_VERSION,
    BuildVersions,
    determine_build_versions,
    get_contrib_version_from_manifest,
)


@pytest.mark.base
def test_determine_build_versions_with_overrides():
    """Test version determination when both versions are provided."""
    manifest = """
dist:
  name: test
extensions:
  - gomod: github.com/open-telemetry/opentelemetry-collector-contrib/extension/basicauthextension v0.122.0
"""
    versions = determine_build_versions(
        manifest,
        ocb_version="0.123.0",
        supervisor_version="0.123.0",
    )
    assert isinstance(versions, BuildVersions)
    assert versions.ocb == "0.123.0"
    assert versions.supervisor == "0.123.0"


@pytest.mark.base
def test_determine_build_versions_from_manifest():
    """Test version determination from manifest when no versions provided."""
    manifest = """
dist:
  name: test
extensions:
  - gomod: github.com/open-telemetry/opentelemetry-collector-contrib/extension/basicauthextension v0.122.0
"""
    versions = determine_build_versions(manifest)
    assert versions.ocb == "0.122.0"
    assert versions.supervisor == "0.122.0"


@pytest.mark.base
def test_determine_build_versions_with_minimum():
    """Test version determination respects minimum supervisor version."""
    manifest = """
dist:
  name: test
extensions:
  - gomod: github.com/open-telemetry/opentelemetry-collector-contrib/extension/basicauthextension v0.121.0
"""
    versions = determine_build_versions(manifest)
    assert versions.ocb == "0.121.0"
    assert versions.supervisor == MIN_SUPERVISOR_VERSION


@pytest.mark.base
def test_parse_simple_manifest():
    """Test parsing version from a simple manifest with consistent versions."""
    manifest = """
dist:
  name: test
extensions:
  - gomod: github.com/open-telemetry/opentelemetry-collector-contrib/extension/basicauthextension v0.122.0
exporters:
  - gomod: github.com/open-telemetry/opentelemetry-collector-contrib/exporter/fileexporter v0.122.0
processors:
  - gomod: go.opentelemetry.io/collector/processor/batchprocessor v0.122.1
  - gomod: github.com/open-telemetry/opentelemetry-collector-contrib/processor/attributesprocessor v0.122.0
"""
    version = get_contrib_version_from_manifest(manifest)
    assert version == "0.122.0"


@pytest.mark.base
def test_parse_mixed_versions():
    """Test parsing version from a manifest with mixed contrib versions."""
    manifest = """
dist:
  name: test
extensions:
  - gomod: github.com/open-telemetry/opentelemetry-collector-contrib/extension/basicauthextension v0.121.0
exporters:
  - gomod: github.com/open-telemetry/opentelemetry-collector-contrib/exporter/fileexporter v0.122.0
processors:
  - gomod: github.com/open-telemetry/opentelemetry-collector-contrib/processor/attributesprocessor v0.122.0
"""
    version = get_contrib_version_from_manifest(manifest)
    assert version == "0.122.0"


@pytest.mark.base
def test_parse_no_contrib_components():
    """Test parsing version from a manifest with no contrib components."""
    manifest = """
dist:
  name: test
processors:
  - gomod: go.opentelemetry.io/collector/processor/batchprocessor v0.122.1
"""
    with pytest.raises(ValueError):
        get_contrib_version_from_manifest(manifest)


@pytest.mark.base
def test_parse_invalid_manifest():
    """Test parsing version from an invalid manifest."""
    manifest = "invalid: yaml: content"
    with pytest.raises(yaml.YAMLError):
        get_contrib_version_from_manifest(manifest)
