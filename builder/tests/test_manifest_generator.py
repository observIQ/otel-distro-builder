"""Tests for the manifest generator module."""

import os
import tempfile

import pytest
import yaml

from builder.src.config_parser import ParsedComponents, resolve_components
from builder.src.manifest_generator import (
    ManifestConfig,
    ManifestGenerator,
    generate_manifest,
    generate_manifest_from_config,
)


# Get the path to test configs
TEST_CONFIGS_DIR = os.path.join(os.path.dirname(__file__), "configs")


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
        resolved = resolve_components(parsed, version="0.121.0")

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
        resolved = resolve_components(parsed, version="0.121.0")

        config = ManifestConfig(
            module="github.com/myorg/mycollector",
            name="mycollector",
            description="My custom collector",
            version="2.0.0",
            otel_version="0.121.0",
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
        resolved = resolve_components(parsed, version="0.121.0")

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
        resolved = resolve_components(parsed, version="0.121.0")

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
        resolved = resolve_components(parsed, version="0.121.0")

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
        resolved = resolve_components(parsed, version="0.121.0")

        generator = ManifestGenerator(resolved)
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
        resolved = resolve_components(parsed, version="0.121.0")

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
        resolved = resolve_components(parsed, version="0.121.0")

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
        resolved = resolve_components(parsed, version="0.121.0")

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
        resolved = resolve_components(parsed, version="0.121.0")

        result = generate_manifest(
            resolved=resolved,
            name="test-collector",
            module="github.com/test/collector",
            otel_version="0.121.0",
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
        config_path = os.path.join(TEST_CONFIGS_DIR, "simple.yaml")

        result = generate_manifest_from_config(
            config_path=config_path,
            name="simple-collector",
            otel_version="0.121.0",
        )

        manifest = yaml.safe_load(result.content)

        assert manifest["dist"]["name"] == "simple-collector"
        assert "receivers" in manifest
        assert "processors" in manifest
        assert "exporters" in manifest

    def test_generate_from_complex_config(self):
        """Test generating manifest from complex config file."""
        config_path = os.path.join(TEST_CONFIGS_DIR, "complex.yaml")

        result = generate_manifest_from_config(
            config_path=config_path,
            name="complex-collector",
            otel_version="0.121.0",
        )

        manifest = yaml.safe_load(result.content)

        assert manifest["dist"]["name"] == "complex-collector"
        assert len(manifest["receivers"]) >= 4
        assert len(manifest["extensions"]) >= 3
        assert len(manifest["connectors"]) >= 1

    def test_generate_writes_to_file(self):
        """Test that manifest is written to file when output_path specified."""
        config_path = os.path.join(TEST_CONFIGS_DIR, "simple.yaml")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "manifest.yaml")

            result = generate_manifest_from_config(
                config_path=config_path,
                output_path=output_path,
                name="test-collector",
                otel_version="0.121.0",
            )

            # Check file was written
            assert os.path.exists(output_path)

            # Read and verify content
            with open(output_path, "r") as f:
                file_content = f.read()

            assert file_content == result.content

    def test_generate_header_comment(self):
        """Test that generated manifest has header comment."""
        config_path = os.path.join(TEST_CONFIGS_DIR, "simple.yaml")

        result = generate_manifest_from_config(
            config_path=config_path,
            otel_version="0.121.0",
        )

        # Should have header comments
        assert result.content.startswith("#")
        assert "Generated from collector config.yaml" in result.content
        assert "0.121.0" in result.content


@pytest.mark.unit
class TestBindplaneComponents:
    """Tests for Bindplane component inclusion."""

    def test_bindplane_components_included_by_default(self):
        """Test that Bindplane components are included by default."""
        parsed = ParsedComponents(
            receivers=["otlp"],
            exporters=["debug"],
        )
        resolved = resolve_components(parsed, version="0.121.0")

        # Default config includes Bindplane
        generator = ManifestGenerator(resolved)
        result = generator.generate()

        manifest = yaml.safe_load(result.content)

        # Should have more receivers than just otlp (Bindplane adds 10)
        assert len(manifest["receivers"]) > 1

        # Check for a Bindplane-specific gomod
        gomods = [r["gomod"] for r in manifest["receivers"]]
        assert any("observiq" in g for g in gomods)

    def test_bindplane_components_excluded_with_flag(self):
        """Test that Bindplane components can be excluded."""
        parsed = ParsedComponents(
            receivers=["otlp"],
            exporters=["debug"],
        )
        resolved = resolve_components(parsed, version="0.121.0")

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
        resolved = resolve_components(parsed, version="0.121.0")

        generator = ManifestGenerator(resolved)
        result = generator.generate()

        manifest = yaml.safe_load(result.content)

        # Should have Bindplane replaces
        replaces_str = " ".join(manifest.get("replaces", []))
        assert "observiq" in replaces_str


@pytest.mark.unit
class TestManifestValidity:
    """Tests to ensure generated manifests are valid for OCB."""

    def test_manifest_has_required_sections(self):
        """Test that manifest has all required sections for OCB."""
        config_path = os.path.join(TEST_CONFIGS_DIR, "simple.yaml")

        result = generate_manifest_from_config(
            config_path=config_path,
            otel_version="0.121.0",
        )

        manifest = yaml.safe_load(result.content)

        # Required sections
        assert "dist" in manifest
        assert "module" in manifest["dist"]
        assert "name" in manifest["dist"]

        # At least one component type should be present
        component_types = ["receivers", "processors", "exporters", "extensions", "connectors"]
        has_components = any(t in manifest for t in component_types)
        assert has_components

    def test_gomod_format_is_correct(self):
        """Test that gomod entries have correct format."""
        config_path = os.path.join(TEST_CONFIGS_DIR, "simple.yaml")

        result = generate_manifest_from_config(
            config_path=config_path,
            otel_version="0.121.0",
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
        config_path = os.path.join(TEST_CONFIGS_DIR, "simple.yaml")

        result = generate_manifest_from_config(
            config_path=config_path,
            otel_version="0.121.0",
        )

        manifest = yaml.safe_load(result.content)

        assert "conf_resolver" in manifest
        assert "default_uri_scheme" in manifest["conf_resolver"]
