"""Unit tests for the Go SDK downloader module."""

import os
from unittest.mock import patch

import pytest
from src.go_downloader import (_get_cache_dir, _get_go_arch, _get_go_os,
                               build_go_url, get_cache_path)

# ── URL construction ────────────────────────────────────────────────────────


@pytest.mark.unit
def test_build_go_url_linux_amd64():
    """Test URL construction for linux/amd64."""
    url = build_go_url("1.24.0", "linux", "amd64")
    assert url == "https://go.dev/dl/go1.24.0.linux-amd64.tar.gz"


@pytest.mark.unit
def test_build_go_url_darwin_arm64():
    """Test URL construction for darwin/arm64."""
    url = build_go_url("1.24.0", "darwin", "arm64")
    assert url == "https://go.dev/dl/go1.24.0.darwin-arm64.tar.gz"


@pytest.mark.unit
def test_build_go_url_windows_amd64():
    """Test URL construction for windows/amd64 uses .zip extension."""
    url = build_go_url("1.23.0", "windows", "amd64")
    assert url == "https://go.dev/dl/go1.23.0.windows-amd64.zip"


@pytest.mark.unit
def test_build_go_url_linux_arm64():
    """Test URL construction for linux/arm64."""
    url = build_go_url("1.22.5", "linux", "arm64")
    assert url == "https://go.dev/dl/go1.22.5.linux-arm64.tar.gz"


# ── Platform helpers ────────────────────────────────────────────────────────


@pytest.mark.unit
def test_get_go_os_linux():
    """Test Go OS detection for Linux."""
    with patch("src.go_downloader.platform.system", return_value="Linux"):
        assert _get_go_os() == "linux"


@pytest.mark.unit
def test_get_go_os_darwin():
    """Test Go OS detection for macOS."""
    with patch("src.go_downloader.platform.system", return_value="Darwin"):
        assert _get_go_os() == "darwin"


@pytest.mark.unit
def test_get_go_os_windows():
    """Test Go OS detection for Windows."""
    with patch("src.go_downloader.platform.system", return_value="Windows"):
        assert _get_go_os() == "windows"


@pytest.mark.unit
def test_get_go_os_unsupported():
    """Test Go OS detection for unsupported OS raises ValueError."""
    with patch("src.go_downloader.platform.system", return_value="SunOS"):
        with pytest.raises(ValueError, match="Unsupported OS"):
            _get_go_os()


@pytest.mark.unit
def test_get_go_arch_delegates_to_get_architecture():
    """Test that _get_go_arch delegates to ocb_downloader.get_architecture."""
    with patch("src.go_downloader.get_architecture", return_value="arm64"):
        assert _get_go_arch() == "arm64"


# ── Cache path logic ───────────────────────────────────────────────────────


@pytest.mark.unit
def test_get_cache_path_contains_version():
    """Test that cache path includes the version directory."""
    path = get_cache_path("1.24.0")
    assert path.endswith(os.path.join("otel-distro-builder", "go", "1.24.0"))


@pytest.mark.unit
def test_get_cache_path_different_versions():
    """Test that different versions produce different cache paths."""
    path1 = get_cache_path("1.23.0")
    path2 = get_cache_path("1.24.0")
    assert path1 != path2
    assert "1.23.0" in path1
    assert "1.24.0" in path2


@pytest.mark.unit
def test_cache_dir_respects_xdg_on_linux():
    """Test that XDG_CACHE_HOME is respected on Linux."""
    with (
        patch("src.go_downloader.sys.platform", "linux"),
        patch.dict(os.environ, {"XDG_CACHE_HOME": "/custom/cache"}),
    ):
        result = _get_cache_dir()
        assert result == os.path.join("/custom/cache", "otel-distro-builder", "go")


@pytest.mark.unit
def test_cache_dir_fallback_on_linux():
    """Test that ~/.cache is used as fallback on Linux without XDG_CACHE_HOME."""
    with (
        patch("src.go_downloader.sys.platform", "linux"),
        patch.dict(os.environ, {}, clear=True),
        patch("src.go_downloader.os.path.expanduser", return_value="/home/user"),
    ):
        result = _get_cache_dir()
        # expanduser("~/.cache") returns the mocked value + "/.cache"
        # but since we mock expanduser it returns "/home/user"
        assert "otel-distro-builder" in result


@pytest.mark.unit
def test_cache_dir_macos():
    """Test that ~/Library/Caches is used on macOS."""
    with (
        patch("src.go_downloader.sys.platform", "darwin"),
        patch("src.go_downloader.os.path.expanduser", return_value="/Users/testuser"),
    ):
        result = _get_cache_dir()
        assert result == os.path.join(
            "/Users/testuser", "Library", "Caches", "otel-distro-builder", "go"
        )
