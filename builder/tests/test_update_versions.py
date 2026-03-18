"""Tests for the update_versions_yaml script."""

import os
import sys
import textwrap

import pytest
import yaml

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "scripts")
)

from update_versions_yaml import (
    MIN_SUPERVISOR_VERSION,
    best_match,
    compute_core_version,
    extract_component_versions,
    load_existing,
    serialize_versions_yaml,
    version_tuple,
)


# ---------------------------------------------------------------------------
# version_tuple
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestVersionTuple:
    def test_basic(self):
        assert version_tuple("0.144.0") == (0, 144, 0)

    def test_patch(self):
        assert version_tuple("0.130.1") == (0, 130, 1)

    def test_ordering(self):
        assert version_tuple("0.144.0") > version_tuple("0.143.0")
        assert version_tuple("0.130.1") > version_tuple("0.130.0")
        assert version_tuple("1.50.0") > version_tuple("0.144.0")


# ---------------------------------------------------------------------------
# compute_core_version
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestComputeCoreVersion:
    def test_standard_versions(self):
        assert compute_core_version("0.144.0") == "1.50.0"
        assert compute_core_version("0.143.0") == "1.49.0"
        assert compute_core_version("0.120.0") == "1.26.0"
        assert compute_core_version("0.134.0") == "1.40.0"

    def test_patch_versions(self):
        assert compute_core_version("0.130.1") == "1.36.1"
        assert compute_core_version("0.123.1") == "1.29.1"
        assert compute_core_version("0.122.1") == "1.28.1"

    def test_boundary(self):
        assert compute_core_version("0.94.0") == "1.0.0"

    def test_too_old_raises(self):
        with pytest.raises(ValueError, match="minor.*< 94"):
            compute_core_version("0.93.0")

    def test_validates_against_existing_yaml(self):
        """Cross-check the formula against known entries in versions.yaml."""
        versions_path = os.path.join(
            os.path.dirname(__file__), "..", "versions.yaml"
        )
        existing = load_existing(versions_path)
        for contrib_ver, entry in existing.items():
            expected_core = entry["core"]
            computed_core = compute_core_version(contrib_ver)
            assert computed_core == expected_core, (
                f"Core mismatch for {contrib_ver}: "
                f"computed={computed_core}, expected={expected_core}"
            )


# ---------------------------------------------------------------------------
# best_match
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestBestMatch:
    def test_exact_match(self):
        available = {"0.144.0", "0.143.0", "0.142.0"}
        assert best_match("0.144.0", available) == "0.144.0"

    def test_patch_falls_back_to_base(self):
        available = {"0.130.0", "0.129.0"}
        assert best_match("0.130.1", available) == "0.130.0"

    def test_no_match_returns_none(self):
        available = {"0.143.0", "0.142.0"}
        assert best_match("0.144.0", available) is None

    def test_patch_no_base_returns_none(self):
        available = {"0.129.0"}
        assert best_match("0.130.1", available) is None

    def test_empty_set(self):
        assert best_match("0.144.0", set()) is None


# ---------------------------------------------------------------------------
# extract_component_versions
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestExtractComponentVersions:
    def test_extracts_all_components(self):
        releases = [
            {
                "tag_name": "v0.144.0",
                "assets": [
                    {
                        "name": "otelcol-contrib_0.144.0_linux_amd64.tar.gz"
                    },
                    {"name": "ocb_0.144.0_linux_amd64"},
                ],
            },
            {
                "tag_name": "cmd/opampsupervisor/v0.144.0",
                "assets": [
                    {
                        "name": "opampsupervisor_0.144.0_linux_amd64.tar.gz"
                    },
                ],
            },
        ]
        contrib, ocb, supervisor = extract_component_versions(releases)
        assert "0.144.0" in contrib
        assert "0.144.0" in ocb
        assert "0.144.0" in supervisor

    def test_supervisor_only_from_tagged_releases(self):
        releases = [
            {
                "tag_name": "v0.144.0",
                "assets": [
                    {
                        "name": "opampsupervisor_0.144.0_linux_amd64.tar.gz"
                    },
                ],
            },
        ]
        _, _, supervisor = extract_component_versions(releases)
        assert "0.144.0" not in supervisor

    def test_multiple_versions(self):
        releases = [
            {
                "tag_name": "v0.144.0",
                "assets": [
                    {
                        "name": "otelcol-contrib_0.144.0_linux_amd64.tar.gz"
                    },
                    {"name": "ocb_0.144.0_linux_amd64"},
                ],
            },
            {
                "tag_name": "v0.143.0",
                "assets": [
                    {
                        "name": "otelcol-contrib_0.143.0_linux_amd64.tar.gz"
                    },
                    {"name": "ocb_0.143.0_linux_amd64"},
                ],
            },
        ]
        contrib, ocb, _ = extract_component_versions(releases)
        assert contrib == {"0.144.0", "0.143.0"}
        assert ocb == {"0.144.0", "0.143.0"}

    def test_empty_releases(self):
        contrib, ocb, supervisor = extract_component_versions([])
        assert contrib == set()
        assert ocb == set()
        assert supervisor == set()


# ---------------------------------------------------------------------------
# serialize_versions_yaml
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSerializeVersionsYaml:
    def test_roundtrip_preserves_data(self):
        versions = {
            "0.144.0": {
                "core": "1.50.0",
                "supervisor": "0.144.0",
                "builder": "0.144.0",
                "go": "1.24.0",
            },
            "0.143.0": {
                "core": "1.49.0",
                "supervisor": "0.143.0",
                "builder": "0.143.0",
                "go": "1.24.0",
            },
        }
        content = serialize_versions_yaml(versions)
        parsed = yaml.safe_load(content)
        assert "versions" in parsed
        assert "0.144.0" in parsed["versions"]
        assert "0.143.0" in parsed["versions"]
        assert parsed["versions"]["0.144.0"]["core"] == "1.50.0"
        assert parsed["versions"]["0.143.0"]["go"] == "1.24.0"

    def test_newest_first(self):
        versions = {
            "0.120.0": {
                "core": "1.26.0",
                "supervisor": "0.122.0",
                "builder": "0.120.0",
                "go": "1.23.0",
            },
            "0.144.0": {
                "core": "1.50.0",
                "supervisor": "0.144.0",
                "builder": "0.144.0",
                "go": "1.24.0",
            },
        }
        content = serialize_versions_yaml(versions)
        lines = content.split("\n")
        version_lines = [l for l in lines if l.strip().startswith('"')]
        assert '"0.144.0"' in version_lines[0]
        assert '"0.120.0"' in version_lines[1]

    def test_patch_comment_on_supervisor(self):
        versions = {
            "0.130.1": {
                "core": "1.36.1",
                "supervisor": "0.130.0",
                "builder": "0.130.0",
                "go": "1.23.0",
            },
        }
        content = serialize_versions_yaml(versions)
        assert "# Patch release, uses base version" in content

    def test_min_supervisor_comment(self):
        versions = {
            "0.121.0": {
                "core": "1.27.0",
                "supervisor": "0.122.0",
                "builder": "0.121.0",
                "go": "1.23.0",
            },
        }
        content = serialize_versions_yaml(versions)
        assert (
            f"# Uses {MIN_SUPERVISOR_VERSION} since supervisor started"
            f" at {MIN_SUPERVISOR_VERSION}" in content
        )

    def test_quoted_keys_and_values(self):
        versions = {
            "0.144.0": {
                "core": "1.50.0",
                "supervisor": "0.144.0",
                "builder": "0.144.0",
                "go": "1.24.0",
            },
        }
        content = serialize_versions_yaml(versions)
        assert '"0.144.0":' in content
        assert 'core: "1.50.0"' in content
        assert 'supervisor: "0.144.0"' in content
        assert 'builder: "0.144.0"' in content
        assert 'go: "1.24.0"' in content

    def test_header_contains_formula_docs(self):
        versions = {
            "0.144.0": {
                "core": "1.50.0",
                "supervisor": "0.144.0",
                "builder": "0.144.0",
                "go": "1.24.0",
            },
        }
        content = serialize_versions_yaml(versions)
        assert "Formula: core = 1.(contrib_minor - 94).patch" in content


# ---------------------------------------------------------------------------
# load_existing
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLoadExisting:
    def test_nonexistent_file(self):
        assert load_existing("/nonexistent/path/versions.yaml") == {}

    def test_valid_file(self, tmp_path):
        f = tmp_path / "versions.yaml"
        f.write_text(
            textwrap.dedent("""\
            versions:
              "0.144.0":
                core: "1.50.0"
                supervisor: "0.144.0"
                builder: "0.144.0"
                go: "1.24.0"
        """)
        )
        result = load_existing(str(f))
        assert "0.144.0" in result
        assert result["0.144.0"]["core"] == "1.50.0"

    def test_empty_file(self, tmp_path):
        f = tmp_path / "versions.yaml"
        f.write_text("")
        assert load_existing(str(f)) == {}


# ---------------------------------------------------------------------------
# Integration: load + serialize roundtrip on the real versions.yaml
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestRealVersionsYaml:
    """Verify the script can load and re-serialize the actual versions.yaml."""

    @pytest.fixture
    def real_versions_path(self):
        return os.path.join(
            os.path.dirname(__file__), "..", "versions.yaml"
        )

    def test_loads_real_file(self, real_versions_path):
        result = load_existing(real_versions_path)
        assert len(result) > 0
        first_key = list(result.keys())[0]
        for field in ("core", "supervisor", "builder", "go"):
            assert field in result[first_key], (
                f"Missing '{field}' in entry {first_key}"
            )

    def test_first_entry_is_newest(self, real_versions_path):
        """The first key must be the highest version (DEFAULT_VERSION relies on this)."""
        result = load_existing(real_versions_path)
        keys = list(result.keys())
        assert keys == sorted(
            keys, key=version_tuple, reverse=True
        ), "versions.yaml entries are not sorted newest-first"

    def test_serialize_roundtrip_parseable(self, real_versions_path):
        """Serialize the real data and verify it round-trips through yaml.safe_load."""
        existing = load_existing(real_versions_path)
        content = serialize_versions_yaml(existing)
        parsed = yaml.safe_load(content)
        assert "versions" in parsed
        for ver, entry in existing.items():
            assert ver in parsed["versions"]
            assert parsed["versions"][ver]["core"] == entry["core"]
            assert parsed["versions"][ver]["go"] == entry["go"]
