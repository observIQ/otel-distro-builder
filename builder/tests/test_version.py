import unittest

import yaml
from src.version import get_otel_contrib_version_from_manifest


class TestVersionParsing(unittest.TestCase):
    def test_parse_simple_manifest(self):
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
        version = get_otel_contrib_version_from_manifest(manifest)
        self.assertEqual(version, "0.122.0")

    def test_parse_mixed_versions(self):
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
        version = get_otel_contrib_version_from_manifest(manifest)
        self.assertEqual(version, "0.122.0")

    def test_parse_no_contrib_components(self):
        manifest = """
dist:
  name: test
processors:
  - gomod: go.opentelemetry.io/collector/processor/batchprocessor v0.122.1
"""
        with self.assertRaises(ValueError):
            get_otel_contrib_version_from_manifest(manifest)

    def test_parse_invalid_manifest(self):
        manifest = "invalid: yaml: content"
        with self.assertRaises(yaml.YAMLError):
            get_otel_contrib_version_from_manifest(manifest)
