"""Tests for the manifest generator module."""

import os
import tempfile

import pytest
import yaml

from builder.src.config_parser import ParsedComponents, resolve_components
from builder.src.manifest_generator import (ManifestConfig, ManifestGenerator,
                                            generate_manifest,
                                            generate_manifest_from_config)
from builder.src.resources import get_bindplane_components_yaml_path

# Get the path to test configs (collector configs live under otelcol/)
TEST_CONFIGS_DIR = os.path.join(os.path.dirname(__file__), "configs")


def _get_bindplane_version() -> str:
    """Read the current Bindplane version from bindplane_components.yaml."""
    with open(get_bindplane_components_yaml_path(), "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["version"]
TEST_OTELCOL_CONFIGS_DIR = os.path.join(TEST_CONFIGS_DIR, "otelcol")


@pytest.mark.unit
class TestManifestGenerator:
    """Tests for ManifestGenerator class."""

    def test_generate_simple_manifest(self):
        """Test generating a manifest with simple components."""
        parsed = ParsedComponents(
            receivers=["otlp"],
            processors=["batch"],
            exporters=["debug"],
        )
        resolved = resolve_components(parsed, version="0.147.0")

        config = ManifestConfig(include_bindplane=False)
        generator = ManifestGenerator(resolved, config)
        result = generator.generate()

        # Parse the generated YAML
        manifest = yaml.safe_load(result.content)

        # Check dist section
        assert "dist" in manifest
        assert manifest["dist"]["name"] == "otelcol-custom"

        # Check components
        assert "receivers" in manifest
        assert "processors" in manifest
        assert "exporters" in manifest

        # Verify gomod entries exist
        assert len(manifest["receivers"]) == 1
        assert "gomod" in manifest["receivers"][0]

    def test_generate_with_custom_config(self):
        """Test generating a manifest with custom configuration."""
        parsed = ParsedComponents(
            receivers=["otlp"],
            exporters=["debug"],
        )
        resolved = resolve_components(parsed, version="0.147.0")

        config = ManifestConfig(
            module="github.com/myorg/mycollector",
            name="mycollector",
            description="My custom collector",
            version="2.0.0",
            otel_version="0.147.0",
        )

        generator = ManifestGenerator(resolved, config)
        result = generator.generate()

        manifest = yaml.safe_load(result.content)

        assert manifest["dist"]["module"] == "github.com/myorg/mycollector"
        assert manifest["dist"]["name"] == "mycollector"
        assert manifest["dist"]["description"] == "My custom collector"
        assert manifest["dist"]["version"] == "2.0.0"

    def test_generate_includes_providers(self):
        """Test that generated manifest includes providers."""
        parsed = ParsedComponents(
            receivers=["otlp"],
            exporters=["debug"],
        )
        resolved = resolve_components(parsed, version="0.147.0")

        generator = ManifestGenerator(resolved)
        result = generator.generate()

        manifest = yaml.safe_load(result.content)

        assert "providers" in manifest
        assert len(manifest["providers"]) >= 5  # env, file, http, https, yaml

    def test_generate_includes_replaces(self):
        """Test that generated manifest includes replaces."""
        parsed = ParsedComponents(
            receivers=["otlp"],
            exporters=["debug"],
        )
        resolved = resolve_components(parsed, version="0.147.0")

        generator = ManifestGenerator(resolved)
        result = generator.generate()

        manifest = yaml.safe_load(result.content)

        assert "replaces" in manifest
        assert len(manifest["replaces"]) >= 1

    def test_generate_with_extensions(self):
        """Test generating a manifest with extensions."""
        parsed = ParsedComponents(
            receivers=["otlp"],
            exporters=["debug"],
            extensions=["health_check", "pprof", "zpages"],
        )
        resolved = resolve_components(parsed, version="0.147.0")

        config = ManifestConfig(include_bindplane=False)
        generator = ManifestGenerator(resolved, config)
        result = generator.generate()

        manifest = yaml.safe_load(result.content)

        assert "extensions" in manifest
        assert len(manifest["extensions"]) == 3

    def test_generate_with_connectors(self):
        """Test generating a manifest with connectors."""
        parsed = ParsedComponents(
            receivers=["otlp"],
            exporters=["debug"],
            connectors=["spanmetrics", "forward"],
        )
        resolved = resolve_components(parsed, version="0.147.0")

        config = ManifestConfig(include_bindplane=False)
        generator = ManifestGenerator(resolved, config)
        result = generator.generate()

        manifest = yaml.safe_load(result.content)

        assert "connectors" in manifest
        assert len(manifest["connectors"]) == 2

    def test_generate_warnings_for_unresolved(self):
        """Test that warnings are generated for unresolved components."""
        parsed = ParsedComponents(
            receivers=["otlp", "unknown_receiver"],
            exporters=["debug"],
        )
        resolved = resolve_components(parsed, version="0.147.0")

        generator = ManifestGenerator(resolved)
        result = generator.generate()

        assert len(result.warnings) > 0
        assert any("unknown_receiver" in w for w in result.warnings)

    def test_generate_without_providers(self):
        """Test generating a manifest without providers."""
        parsed = ParsedComponents(
            receivers=["otlp"],
            exporters=["debug"],
        )
        resolved = resolve_components(parsed, version="0.147.0")

        config = ManifestConfig(include_providers=False)

        generator = ManifestGenerator(resolved, config)
        result = generator.generate()

        manifest = yaml.safe_load(result.content)

        assert "providers" not in manifest

    def test_generate_without_replaces(self):
        """Test generating a manifest without replaces."""
        parsed = ParsedComponents(
            receivers=["otlp"],
            exporters=["debug"],
        )
        resolved = resolve_components(parsed, version="0.147.0")

        config = ManifestConfig(include_replaces=False)

        generator = ManifestGenerator(resolved, config)
        result = generator.generate()

        manifest = yaml.safe_load(result.content)

        assert "replaces" not in manifest


@pytest.mark.unit
class TestGenerateManifest:
    """Tests for generate_manifest function."""

    def test_generate_manifest_basic(self):
        """Test basic manifest generation."""
        parsed = ParsedComponents(
            receivers=["otlp", "prometheus"],
            processors=["batch", "attributes"],
            exporters=["debug", "otlp"],
        )
        resolved = resolve_components(parsed, version="0.147.0")

        result = generate_manifest(
            resolved=resolved,
            name="test-collector",
            module="github.com/test/collector",
            otel_version="0.147.0",
            include_bindplane=False,
        )

        manifest = yaml.safe_load(result.content)

        assert manifest["dist"]["name"] == "test-collector"
        assert len(manifest["receivers"]) == 2
        assert len(manifest["processors"]) == 2
        assert len(manifest["exporters"]) == 2


@pytest.mark.unit
class TestGenerateManifestFromConfig:
    """Tests for generate_manifest_from_config function."""

    def test_generate_from_simple_config(self):
        """Test generating manifest from simple config file."""
        config_path = os.path.join(TEST_OTELCOL_CONFIGS_DIR, "simple.yaml")

        result = generate_manifest_from_config(
            config_path=config_path,
            name="simple-collector",
            otel_version="0.147.0",
        )

        manifest = yaml.safe_load(result.content)

        assert manifest["dist"]["name"] == "simple-collector"
        assert "receivers" in manifest
        assert "processors" in manifest
        assert "exporters" in manifest

    def test_generate_from_complex_config(self):
        """Test generating manifest from complex config file."""
        config_path = os.path.join(TEST_OTELCOL_CONFIGS_DIR, "complex.yaml")

        result = generate_manifest_from_config(
            config_path=config_path,
            name="complex-collector",
            otel_version="0.147.0",
        )

        manifest = yaml.safe_load(result.content)

        assert manifest["dist"]["name"] == "complex-collector"
        assert len(manifest["receivers"]) >= 4
        assert len(manifest["extensions"]) >= 3
        assert len(manifest["connectors"]) >= 1

    def test_generate_writes_to_file(self):
        """Test that manifest is written to file when output_path specified."""
        config_path = os.path.join(TEST_OTELCOL_CONFIGS_DIR, "simple.yaml")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "manifest.yaml")

            result = generate_manifest_from_config(
                config_path=config_path,
                output_path=output_path,
                name="test-collector",
                otel_version="0.147.0",
            )

            # Check file was written
            assert os.path.exists(output_path)

            # Read and verify content
            with open(output_path, "r") as f:
                file_content = f.read()

            assert file_content == result.content

    def test_generate_header_comment(self):
        """Test that generated manifest has header comment."""
        config_path = os.path.join(TEST_OTELCOL_CONFIGS_DIR, "simple.yaml")

        result = generate_manifest_from_config(
            config_path=config_path,
            otel_version="0.147.0",
        )

        # Should have header comments
        assert result.content.startswith("#")
        assert "Generated from collector config.yaml" in result.content
        assert "0.147.0" in result.content


@pytest.mark.unit
class TestBindplaneComponents:
    """Tests for Bindplane component inclusion."""

    def test_bindplane_components_included_by_default(self):
        """Test that Bindplane components are included by default."""
        parsed = ParsedComponents(
            receivers=["otlp"],
            exporters=["debug"],
        )
        resolved = resolve_components(parsed, version="0.147.0")

        # Default config includes Bindplane
        generator = ManifestGenerator(resolved)
        result = generator.generate()

        manifest = yaml.safe_load(result.content)

        # Should have more receivers than just otlp (Bindplane adds 3)
        assert len(manifest["receivers"]) > 1

        # Check for Bindplane-required gomods (e.g. filelog, hostmetrics)
        gomods = [r["gomod"] for r in manifest["receivers"]]
        assert any("filelogreceiver" in g for g in gomods)

    def test_bindplane_components_excluded_with_flag(self):
        """Test that Bindplane components can be excluded."""
        parsed = ParsedComponents(
            receivers=["otlp"],
            exporters=["debug"],
        )
        resolved = resolve_components(parsed, version="0.147.0")

        config = ManifestConfig(include_bindplane=False)
        generator = ManifestGenerator(resolved, config)
        result = generator.generate()

        manifest = yaml.safe_load(result.content)

        # Should have only the user's receiver
        assert len(manifest["receivers"]) == 1

        # No Bindplane gomods
        gomods = [r["gomod"] for r in manifest["receivers"]]
        assert not any("observiq" in g for g in gomods)

    def test_bindplane_replaces_included(self):
        """Test that Bindplane replaces are included when enabled."""
        parsed = ParsedComponents(
            receivers=["otlp"],
            exporters=["debug"],
        )
        resolved = resolve_components(parsed, version="0.147.0")

        generator = ManifestGenerator(resolved)
        result = generator.generate()

        manifest = yaml.safe_load(result.content)

        # Should have Bindplane replaces
        replaces_str = " ".join(manifest.get("replaces", []))
        assert "observiq" in replaces_str


@pytest.mark.unit
class TestBindplaneVersion:
    """Tests for --bindplane-version override."""

    def test_bindplane_version_override(self):
        """Test that bindplane_version overrides the file's default."""
        parsed = ParsedComponents(
            receivers=["otlp"],
            exporters=["debug"],
        )
        resolved = resolve_components(parsed, version="0.147.0")

        config = ManifestConfig(
            include_bindplane=True,
            bindplane_version="1.90.0",
        )
        generator = ManifestGenerator(resolved, config)
        result = generator.generate()

        manifest = yaml.safe_load(result.content)

        # All Bindplane-owned gomods should use v1.90.0
        all_gomods = []
        for section in ["extensions", "receivers", "processors", "exporters"]:
            for entry in manifest.get(section, []):
                all_gomods.append(entry["gomod"])

        bp_gomods = [g for g in all_gomods if "observiq" in g]
        assert len(bp_gomods) > 0
        for gomod in bp_gomods:
            assert "v1.90.0" in gomod, f"Expected v1.90.0 in {gomod}"

    def test_bindplane_version_default_uses_file(self):
        """Test that without override, the file's version is used."""
        parsed = ParsedComponents(
            receivers=["otlp"],
            exporters=["debug"],
        )
        resolved = resolve_components(parsed, version="0.147.0")

        config = ManifestConfig(include_bindplane=True)
        generator = ManifestGenerator(resolved, config)
        result = generator.generate()

        manifest = yaml.safe_load(result.content)

        # Check that Bindplane gomods use the version from the file
        expected_version = _get_bindplane_version()
        all_gomods = []
        for section in ["extensions", "receivers", "processors", "exporters"]:
            for entry in manifest.get(section, []):
                all_gomods.append(entry["gomod"])

        bp_gomods = [g for g in all_gomods if "observiq" in g]
        assert len(bp_gomods) > 0
        for gomod in bp_gomods:
            assert f"v{expected_version}" in gomod, f"Expected v{expected_version} in {gomod}"


@pytest.mark.unit
class TestRequiredBindplaneCompatibility:
    """Tests for required Bindplane-compatible modules (BYOC minimal set)."""

    # Module paths (without version) that must be present for Bindplane compatibility
    REQUIRED_CONNECTORS = [
        "go.opentelemetry.io/collector/connector/forwardconnector",
        "github.com/open-telemetry/opentelemetry-collector-contrib/connector/routingconnector",
    ]
    REQUIRED_EXPORTERS = [
        "go.opentelemetry.io/collector/exporter/otlpexporter",
        "go.opentelemetry.io/collector/exporter/otlphttpexporter",
        "go.opentelemetry.io/collector/exporter/nopexporter",
    ]
    REQUIRED_EXTENSIONS = [
        "github.com/observiq/bindplane-otel-collector/extension/bindplaneextension",
        "github.com/open-telemetry/opentelemetry-collector-contrib/extension/healthcheckextension",
        "github.com/open-telemetry/opentelemetry-collector-contrib/extension/opampextension",
        "github.com/open-telemetry/opentelemetry-collector-contrib/extension/storage/filestorage",
    ]
    REQUIRED_PROCESSORS = [
        "github.com/observiq/bindplane-otel-collector/processor/snapshotprocessor",
        "github.com/open-telemetry/opentelemetry-collector-contrib/processor/metricstransformprocessor",
        "github.com/open-telemetry/opentelemetry-collector-contrib/processor/transformprocessor",
        "github.com/observiq/bindplane-otel-collector/processor/throughputmeasurementprocessor",
        "github.com/open-telemetry/opentelemetry-collector-contrib/processor/resourcedetectionprocessor",
    ]
    REQUIRED_RECEIVERS = [
        "github.com/open-telemetry/opentelemetry-collector-contrib/receiver/filelogreceiver",
        "github.com/open-telemetry/opentelemetry-collector-contrib/receiver/hostmetricsreceiver",
        "go.opentelemetry.io/collector/receiver/nopreceiver",
    ]

    @staticmethod
    def _gomod_paths(manifest: dict, section: str) -> set:
        """Extract module paths (without version) from a manifest section."""
        return {
            entry["gomod"].split()[0]
            for entry in manifest.get(section, [])
            if "gomod" in entry
        }

    def test_minimal_config_includes_all_required_modules(self):
        """With include_bindplane=True, even a minimal config produces all required modules."""
        parsed = ParsedComponents(
            receivers=["otlp"],
            exporters=["debug"],
        )
        resolved = resolve_components(parsed, version="0.147.0")

        config = ManifestConfig(include_bindplane=True)
        generator = ManifestGenerator(resolved, config)
        result = generator.generate()
        manifest = yaml.safe_load(result.content)

        conn_paths = self._gomod_paths(manifest, "connectors")
        for req in self.REQUIRED_CONNECTORS:
            assert req in conn_paths, f"Missing required connector: {req}"

        exp_paths = self._gomod_paths(manifest, "exporters")
        for req in self.REQUIRED_EXPORTERS:
            assert req in exp_paths, f"Missing required exporter: {req}"

        ext_paths = self._gomod_paths(manifest, "extensions")
        for req in self.REQUIRED_EXTENSIONS:
            assert req in ext_paths, f"Missing required extension: {req}"

        proc_paths = self._gomod_paths(manifest, "processors")
        for req in self.REQUIRED_PROCESSORS:
            assert req in proc_paths, f"Missing required processor: {req}"

        recv_paths = self._gomod_paths(manifest, "receivers")
        for req in self.REQUIRED_RECEIVERS:
            assert req in recv_paths, f"Missing required receiver: {req}"

    def test_required_modules_not_added_when_bindplane_disabled(self):
        """With include_bindplane=False, no required modules are added."""
        parsed = ParsedComponents(
            receivers=["otlp"],
            exporters=["debug"],
        )
        resolved = resolve_components(parsed, version="0.147.0")

        config = ManifestConfig(include_bindplane=False)
        generator = ManifestGenerator(resolved, config)
        result = generator.generate()
        manifest = yaml.safe_load(result.content)

        # Should NOT have connectors section at all (user didn't specify any)
        assert "connectors" not in manifest

        # Should NOT have any observiq modules
        all_gomods = []
        for section in ["extensions", "receivers", "processors", "exporters"]:
            for entry in manifest.get(section, []):
                all_gomods.append(entry["gomod"])
        assert not any("observiq" in g for g in all_gomods)

    def test_no_duplicates_when_user_already_has_required(self):
        """Required modules that are already present via user config should not be duplicated."""
        # User config already includes forward connector and otlp exporter
        parsed = ParsedComponents(
            receivers=["otlp"],
            exporters=["otlp", "debug"],
            connectors=["forward"],
        )
        resolved = resolve_components(parsed, version="0.147.0")

        config = ManifestConfig(include_bindplane=True)
        generator = ManifestGenerator(resolved, config)
        result = generator.generate()
        manifest = yaml.safe_load(result.content)

        # forwardconnector should appear exactly once
        conn_gomods = [e["gomod"] for e in manifest.get("connectors", [])]
        forward_count = sum(1 for g in conn_gomods if "forwardconnector" in g)
        assert forward_count == 1, f"forwardconnector appeared {forward_count} times"

        # otlpexporter should appear exactly once
        exp_gomods = [e["gomod"] for e in manifest.get("exporters", [])]
        otlp_count = sum(
            1 for g in exp_gomods if "otlpexporter" in g and "otlphttp" not in g
        )
        assert otlp_count == 1, f"otlpexporter appeared {otlp_count} times"

    def test_connectors_section_created_when_absent(self):
        """When user config has no connectors, the required connectors still appear."""
        parsed = ParsedComponents(
            receivers=["otlp"],
            exporters=["debug"],
        )
        resolved = resolve_components(parsed, version="0.147.0")

        config = ManifestConfig(include_bindplane=True)
        generator = ManifestGenerator(resolved, config)
        result = generator.generate()
        manifest = yaml.safe_load(result.content)

        assert "connectors" in manifest
        conn_paths = self._gomod_paths(manifest, "connectors")
        for req in self.REQUIRED_CONNECTORS:
            assert req in conn_paths, f"Missing required connector: {req}"


@pytest.mark.unit
class TestManifestValidity:
    """Tests to ensure generated manifests are valid for OCB."""

    def test_manifest_has_required_sections(self):
        """Test that manifest has all required sections for OCB."""
        config_path = os.path.join(TEST_OTELCOL_CONFIGS_DIR, "simple.yaml")

        result = generate_manifest_from_config(
            config_path=config_path,
            otel_version="0.147.0",
        )

        manifest = yaml.safe_load(result.content)

        # Required sections
        assert "dist" in manifest
        assert "module" in manifest["dist"]
        assert "name" in manifest["dist"]

        # At least one component type should be present
        component_types = [
            "receivers",
            "processors",
            "exporters",
            "extensions",
            "connectors",
        ]
        has_components = any(t in manifest for t in component_types)
        assert has_components

    def test_gomod_format_is_correct(self):
        """Test that gomod entries have correct format."""
        config_path = os.path.join(TEST_OTELCOL_CONFIGS_DIR, "simple.yaml")

        result = generate_manifest_from_config(
            config_path=config_path,
            otel_version="0.147.0",
        )

        manifest = yaml.safe_load(result.content)

        for receiver in manifest.get("receivers", []):
            gomod = receiver["gomod"]
            # Should have module path and version
            parts = gomod.split()
            assert len(parts) >= 2, f"Invalid gomod format: {gomod}"
            assert parts[1].startswith("v"), f"Version should start with v: {gomod}"

    def test_conf_resolver_present(self):
        """Test that conf_resolver section is present."""
        config_path = os.path.join(TEST_OTELCOL_CONFIGS_DIR, "simple.yaml")

        result = generate_manifest_from_config(
            config_path=config_path,
            otel_version="0.147.0",
        )

        manifest = yaml.safe_load(result.content)

        assert "conf_resolver" in manifest
        assert "default_uri_scheme" in manifest["conf_resolver"]
