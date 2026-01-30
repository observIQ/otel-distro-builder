"""Tests for the config parser module."""

import os
import pytest

from builder.src.config_parser import (
    ConfigParser,
    ParsedComponents,
    parse_config_file,
    parse_and_resolve,
    resolve_components,
)
from builder.src.component_registry import get_registry


# Get the path to test configs
TEST_CONFIGS_DIR = os.path.join(os.path.dirname(__file__), "configs")


@pytest.mark.unit
class TestConfigParser:
    """Tests for ConfigParser class."""

    def test_parse_simple_config(self):
        """Test parsing a simple config with basic components."""
        config_content = """
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317

processors:
  batch:
    timeout: 1s

exporters:
  debug:
    verbosity: detailed

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [debug]
"""
        parser = ConfigParser(config_content)
        result = parser.parse()

        assert "otlp" in result.receivers
        assert "batch" in result.processors
        assert "debug" in result.exporters

    def test_parse_named_instances(self):
        """Test parsing config with named instances (e.g., otlp/traces)."""
        config_content = """
receivers:
  otlp/traces:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
  otlp/metrics:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4318

processors:
  batch/fast:
    timeout: 100ms
  batch/slow:
    timeout: 5s

exporters:
  otlp/backend1:
    endpoint: backend1:4317
  otlp/backend2:
    endpoint: backend2:4317

service:
  pipelines:
    traces:
      receivers: [otlp/traces]
      processors: [batch/fast]
      exporters: [otlp/backend1]
"""
        parser = ConfigParser(config_content)
        result = parser.parse()

        # Should extract base names only
        assert "otlp" in result.receivers
        assert len([r for r in result.receivers if r == "otlp"]) == 1  # No duplicates
        assert "batch" in result.processors
        assert "otlp" in result.exporters

    def test_parse_extensions(self):
        """Test parsing config with extensions."""
        config_content = """
extensions:
  health_check:
    endpoint: 0.0.0.0:13133
  pprof:
    endpoint: 0.0.0.0:1777
  zpages:
    endpoint: 0.0.0.0:55679

receivers:
  otlp:

exporters:
  debug:

service:
  extensions: [health_check, pprof, zpages]
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [debug]
"""
        parser = ConfigParser(config_content)
        result = parser.parse()

        assert "health_check" in result.extensions
        assert "pprof" in result.extensions
        assert "zpages" in result.extensions

    def test_parse_connectors(self):
        """Test parsing config with connectors."""
        config_content = """
receivers:
  otlp:

processors:
  batch:

exporters:
  debug:

connectors:
  spanmetrics:
    histogram:
      explicit:
        buckets: [1ms, 10ms, 100ms]
  forward:

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [spanmetrics, debug]
    metrics:
      receivers: [spanmetrics]
      exporters: [debug]
"""
        parser = ConfigParser(config_content)
        result = parser.parse()

        assert "spanmetrics" in result.connectors
        assert "forward" in result.connectors

    def test_parse_empty_config(self):
        """Test parsing an empty config."""
        config_content = ""
        parser = ConfigParser(config_content)
        result = parser.parse()

        assert result.is_empty()

    def test_parse_config_with_empty_sections(self):
        """Test parsing config with empty sections."""
        config_content = """
receivers:
  otlp:

processors: {}

exporters:
  debug:

service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [debug]
"""
        parser = ConfigParser(config_content)
        result = parser.parse()

        assert "otlp" in result.receivers
        assert len(result.processors) == 0
        assert "debug" in result.exporters


@pytest.mark.unit
class TestParseConfigFile:
    """Tests for parse_config_file function."""

    def test_parse_simple_file(self):
        """Test parsing the simple test config file."""
        config_path = os.path.join(TEST_CONFIGS_DIR, "simple.yaml")
        result = parse_config_file(config_path)

        assert "otlp" in result.receivers
        assert "batch" in result.processors
        assert "debug" in result.exporters

    def test_parse_complex_file(self):
        """Test parsing the complex test config file."""
        config_path = os.path.join(TEST_CONFIGS_DIR, "complex.yaml")
        result = parse_config_file(config_path)

        # Check receivers
        assert "otlp" in result.receivers
        assert "prometheus" in result.receivers
        assert "filelog" in result.receivers
        assert "hostmetrics" in result.receivers

        # Check processors
        assert "batch" in result.processors
        assert "attributes" in result.processors
        assert "resourcedetection" in result.processors

        # Check exporters
        assert "debug" in result.exporters
        assert "otlp" in result.exporters
        assert "prometheusremotewrite" in result.exporters

        # Check extensions
        assert "health_check" in result.extensions
        assert "pprof" in result.extensions
        assert "zpages" in result.extensions

        # Check connectors
        assert "spanmetrics" in result.connectors

    def test_parse_named_instances_file(self):
        """Test parsing the named instances test config file."""
        config_path = os.path.join(TEST_CONFIGS_DIR, "named_instances.yaml")
        result = parse_config_file(config_path)

        # Should only have unique base names
        assert result.receivers.count("otlp") == 1
        assert result.receivers.count("prometheus") == 1
        assert result.processors.count("batch") == 1
        assert result.exporters.count("otlp") == 1

    def test_parse_minimal_file(self):
        """Test parsing the minimal test config file."""
        config_path = os.path.join(TEST_CONFIGS_DIR, "minimal.yaml")
        result = parse_config_file(config_path)

        assert "nop" in result.receivers
        assert "nop" in result.exporters

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            parse_config_file("/nonexistent/path/config.yaml")


@pytest.mark.unit
class TestResolveComponents:
    """Tests for resolve_components function."""

    def test_resolve_simple_components(self):
        """Test resolving simple components to Go modules."""
        parsed = ParsedComponents(
            receivers=["otlp"],
            processors=["batch"],
            exporters=["debug"],
        )

        resolved = resolve_components(parsed, version="0.121.0")

        # Check receivers
        assert len(resolved.receivers) == 1
        assert "otlpreceiver" in resolved.receivers[0].gomod

        # Check processors
        assert len(resolved.processors) == 1
        assert "batchprocessor" in resolved.processors[0].gomod

        # Check exporters
        assert len(resolved.exporters) == 1
        assert "debugexporter" in resolved.exporters[0].gomod

    def test_resolve_contrib_components(self):
        """Test resolving contrib components."""
        parsed = ParsedComponents(
            receivers=["prometheus", "filelog"],
            processors=["attributes", "transform"],
            exporters=["elasticsearch", "kafka"],
        )

        resolved = resolve_components(parsed, version="0.121.0")

        # All should be resolved
        assert not resolved.has_unresolved()

        # Check that contrib paths are used
        for receiver in resolved.receivers:
            assert "opentelemetry-collector-contrib" in receiver.gomod

    def test_resolve_unknown_components(self):
        """Test handling of unknown components."""
        parsed = ParsedComponents(
            receivers=["otlp", "unknown_receiver"],
            processors=["batch"],
            exporters=["debug", "nonexistent_exporter"],
        )

        resolved = resolve_components(parsed, version="0.121.0")

        # Should have unresolved components
        assert resolved.has_unresolved()
        assert "unknown_receiver" in resolved.unresolved["receivers"]
        assert "nonexistent_exporter" in resolved.unresolved["exporters"]

        # Known components should still be resolved
        assert len(resolved.receivers) == 1
        assert len(resolved.exporters) == 1

    def test_resolve_with_custom_mappings(self):
        """Test resolving with custom component mappings."""
        parsed = ParsedComponents(
            receivers=["custom_receiver"],
            exporters=["debug"],
        )

        custom_mappings = {
            "receivers": {
                "custom_receiver": "github.com/my/custom/receiver __VERSION__"
            }
        }

        resolved = resolve_components(
            parsed, version="0.121.0", custom_mappings=custom_mappings
        )

        # Custom receiver should be resolved
        assert len(resolved.receivers) == 1
        assert "github.com/my/custom/receiver" in resolved.receivers[0].gomod
        assert resolved.receivers[0].source == "custom"

    def test_version_in_gomod(self):
        """Test that version is correctly applied to gomod paths."""
        parsed = ParsedComponents(
            receivers=["otlp"],
        )

        resolved = resolve_components(parsed, version="0.122.0")

        assert "0.122.0" in resolved.receivers[0].gomod


@pytest.mark.unit
class TestParseAndResolve:
    """Tests for parse_and_resolve function."""

    def test_parse_and_resolve_simple(self):
        """Test parsing and resolving a simple config file."""
        config_path = os.path.join(TEST_CONFIGS_DIR, "simple.yaml")
        resolved = parse_and_resolve(config_path, version="0.121.0")

        assert len(resolved.receivers) > 0
        assert len(resolved.processors) > 0
        assert len(resolved.exporters) > 0
        assert not resolved.has_unresolved()

    def test_parse_and_resolve_complex(self):
        """Test parsing and resolving a complex config file."""
        config_path = os.path.join(TEST_CONFIGS_DIR, "complex.yaml")
        resolved = parse_and_resolve(config_path, version="0.121.0")

        # Should resolve all known components
        assert len(resolved.receivers) >= 4  # otlp, prometheus, filelog, hostmetrics
        assert len(resolved.processors) >= 3  # batch, attributes, resourcedetection
        assert len(resolved.exporters) >= 2  # debug, otlp, prometheusremotewrite
        assert len(resolved.extensions) >= 3  # health_check, pprof, zpages
        assert len(resolved.connectors) >= 1  # spanmetrics


@pytest.mark.unit
class TestComponentRegistry:
    """Tests for the component registry."""

    def test_registry_loads(self):
        """Test that the registry loads successfully."""
        registry = get_registry()
        assert registry is not None

    def test_lookup_core_component(self):
        """Test looking up a core component."""
        registry = get_registry()
        info = registry.lookup("receivers", "otlp", "0.121.0")

        assert info is not None
        assert info.name == "otlp"
        assert info.source == "core"
        assert "otlpreceiver" in info.gomod

    def test_lookup_contrib_component(self):
        """Test looking up a contrib component."""
        registry = get_registry()
        info = registry.lookup("receivers", "prometheus", "0.121.0")

        assert info is not None
        assert info.name == "prometheus"
        assert info.source == "contrib"
        assert "prometheusreceiver" in info.gomod

    def test_lookup_nonexistent(self):
        """Test looking up a nonexistent component."""
        registry = get_registry()
        info = registry.lookup("receivers", "nonexistent", "0.121.0")

        assert info is None

    def test_find_similar(self):
        """Test finding similar component names."""
        registry = get_registry()
        similar = registry.find_similar("receivers", "prometheu")

        # Should suggest "prometheus"
        assert "prometheus" in similar

    def test_lookup_handles_named_instance(self):
        """Test that lookup handles named instances correctly."""
        registry = get_registry()

        # Should extract base name from "otlp/traces"
        info = registry.lookup("receivers", "otlp/traces", "0.121.0")

        assert info is not None
        assert info.name == "otlp"
