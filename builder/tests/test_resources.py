"""Tests for the resources module (path resolution for dev and frozen contexts)."""

import os
from unittest.mock import patch

import pytest
from src.resources import (_get_bindplane_components_yaml_path_impl,
                           _get_components_yaml_path_impl,
                           _get_templates_dir_impl,
                           _get_versions_yaml_path_impl,
                           get_bindplane_components_yaml_path,
                           get_components_yaml_path, get_templates_dir,
                           get_versions_yaml_path)

# Path to builder/src (where resources.py lives)
SRC_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.fixture(autouse=True)
def _clear_lru_caches():
    """Clear lru_cache on every public getter so tests don't pollute each other."""
    get_versions_yaml_path.cache_clear()
    get_templates_dir.cache_clear()
    get_components_yaml_path.cache_clear()
    get_bindplane_components_yaml_path.cache_clear()
    yield
    get_versions_yaml_path.cache_clear()
    get_templates_dir.cache_clear()
    get_components_yaml_path.cache_clear()
    get_bindplane_components_yaml_path.cache_clear()


# ── Development / installed context (no _MEIPASS) ──────────────────────────


@pytest.mark.unit
class TestDevContext:
    """Path resolution when running from source (no PyInstaller)."""

    def test_versions_yaml_path(self):
        result = _get_versions_yaml_path_impl()
        expected = os.path.normpath(os.path.join(SRC_DIR, "..", "versions.yaml"))
        assert result == expected
        assert os.path.isfile(result), f"versions.yaml not found at {result}"

    def test_templates_dir(self):
        result = _get_templates_dir_impl()
        expected = os.path.normpath(os.path.join(SRC_DIR, "..", "templates"))
        assert result == expected
        assert os.path.isdir(result), f"templates dir not found at {result}"

    def test_components_yaml_path(self):
        result = _get_components_yaml_path_impl()
        expected = os.path.normpath(os.path.join(SRC_DIR, "components.yaml"))
        assert result == expected
        assert os.path.isfile(result), f"components.yaml not found at {result}"

    def test_bindplane_components_yaml_path(self):
        result = _get_bindplane_components_yaml_path_impl()
        expected = os.path.normpath(os.path.join(SRC_DIR, "bindplane_components.yaml"))
        assert result == expected
        assert os.path.isfile(
            result
        ), f"bindplane_components.yaml not found at {result}"


# ── Frozen (PyInstaller) context ────────────────────────────────────────────


@pytest.mark.unit
class TestFrozenContext:
    """Path resolution when running as a PyInstaller one-file binary."""

    def test_versions_yaml_frozen(self, tmp_path):
        frozen_file = tmp_path / "builder" / "versions.yaml"
        frozen_file.parent.mkdir(parents=True)
        frozen_file.write_text("versions: {}")

        with patch("src.resources._frozen_base", return_value=str(tmp_path)):
            result = _get_versions_yaml_path_impl()
        assert result == str(frozen_file)

    def test_templates_dir_frozen(self, tmp_path):
        frozen_dir = tmp_path / "builder" / "templates"
        frozen_dir.mkdir(parents=True)

        with patch("src.resources._frozen_base", return_value=str(tmp_path)):
            result = _get_templates_dir_impl()
        assert result == str(frozen_dir)

    def test_components_yaml_frozen(self, tmp_path):
        frozen_file = tmp_path / "builder" / "src" / "components.yaml"
        frozen_file.parent.mkdir(parents=True)
        frozen_file.write_text("components: {}")

        with patch("src.resources._frozen_base", return_value=str(tmp_path)):
            result = _get_components_yaml_path_impl()
        assert result == str(frozen_file)

    def test_bindplane_components_yaml_frozen(self, tmp_path):
        frozen_file = tmp_path / "builder" / "src" / "bindplane_components.yaml"
        frozen_file.parent.mkdir(parents=True)
        frozen_file.write_text("components: {}")

        with patch("src.resources._frozen_base", return_value=str(tmp_path)):
            result = _get_bindplane_components_yaml_path_impl()
        assert result == str(frozen_file)


# ── Frozen fallback (MEIPASS set but files missing) ─────────────────────────


@pytest.mark.unit
class TestFrozenFallback:
    """When _MEIPASS is set but the expected files don't exist, fall back to dev paths."""

    def test_versions_yaml_falls_back(self, tmp_path):
        # tmp_path exists but has no builder/ subtree
        with patch("src.resources._frozen_base", return_value=str(tmp_path)):
            result = _get_versions_yaml_path_impl()
        # Should fall back to the __file__-relative dev path
        expected = os.path.normpath(os.path.join(SRC_DIR, "..", "versions.yaml"))
        assert result == expected

    def test_templates_dir_falls_back(self, tmp_path):
        with patch("src.resources._frozen_base", return_value=str(tmp_path)):
            result = _get_templates_dir_impl()
        expected = os.path.normpath(os.path.join(SRC_DIR, "..", "templates"))
        assert result == expected

    def test_components_yaml_falls_back(self, tmp_path):
        with patch("src.resources._frozen_base", return_value=str(tmp_path)):
            result = _get_components_yaml_path_impl()
        expected = os.path.normpath(os.path.join(SRC_DIR, "components.yaml"))
        assert result == expected

    def test_bindplane_components_yaml_falls_back(self, tmp_path):
        with patch("src.resources._frozen_base", return_value=str(tmp_path)):
            result = _get_bindplane_components_yaml_path_impl()
        expected = os.path.normpath(os.path.join(SRC_DIR, "bindplane_components.yaml"))
        assert result == expected


# ── lru_cache wrappers ──────────────────────────────────────────────────────


@pytest.mark.unit
class TestCachedGetters:
    """Public cached getters delegate to impl and cache the result."""

    def test_get_versions_yaml_path_caches(self):
        first = get_versions_yaml_path()
        second = get_versions_yaml_path()
        assert first == second
        assert get_versions_yaml_path.cache_info().hits == 1

    def test_get_templates_dir_caches(self):
        first = get_templates_dir()
        second = get_templates_dir()
        assert first == second
        assert get_templates_dir.cache_info().hits == 1

    def test_get_components_yaml_path_caches(self):
        first = get_components_yaml_path()
        second = get_components_yaml_path()
        assert first == second
        assert get_components_yaml_path.cache_info().hits == 1

    def test_get_bindplane_components_yaml_path_caches(self):
        first = get_bindplane_components_yaml_path()
        second = get_bindplane_components_yaml_path()
        assert first == second
        assert get_bindplane_components_yaml_path.cache_info().hits == 1

    def test_cache_clear_recomputes(self, tmp_path):
        """After cache_clear, the getter calls the impl again."""
        # First call — dev path
        dev_result = get_versions_yaml_path()

        # Clear and call with frozen context
        get_versions_yaml_path.cache_clear()
        frozen_file = tmp_path / "builder" / "versions.yaml"
        frozen_file.parent.mkdir(parents=True)
        frozen_file.write_text("versions: {}")

        with patch("src.resources._frozen_base", return_value=str(tmp_path)):
            frozen_result = get_versions_yaml_path()

        assert frozen_result == str(frozen_file)
        assert frozen_result != dev_result
