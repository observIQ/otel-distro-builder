"""Utility for downloading and caching Go SDK toolchains on demand."""

import os
import platform
import sys
import tarfile
import tempfile
import zipfile

import requests

from .logger import BuildLogger, get_logger
from .ocb_downloader import get_architecture

logger: BuildLogger = get_logger(__name__)


# ── Platform helpers ────────────────────────────────────────────────────────


def _get_go_os() -> str:
    """Return the Go-style OS name (lowercase) for the current host."""
    raw = platform.system().lower()
    if raw in ("linux", "darwin", "windows", "freebsd"):
        return raw
    raise ValueError(f"Unsupported OS for Go SDK download: {raw}")


def _get_go_arch() -> str:
    """Return the Go-style architecture name for the current host."""
    return get_architecture()


# ── URL construction ────────────────────────────────────────────────────────


def build_go_url(version: str, go_os: str, go_arch: str) -> str:
    """Build the official Go SDK download URL.

    Args:
        version: Go version without 'go' prefix (e.g. "1.24.0").
        go_os: Target OS (e.g. "darwin", "linux", "windows").
        go_arch: Target architecture (e.g. "amd64", "arm64").

    Returns:
        Full download URL for the Go SDK archive.
    """
    ext = "zip" if go_os == "windows" else "tar.gz"
    return f"https://go.dev/dl/go{version}.{go_os}-{go_arch}.{ext}"


# ── Cache directory ─────────────────────────────────────────────────────────


def _get_cache_dir() -> str:
    """Return the shared cache directory for downloaded Go toolchains.

    Respects XDG_CACHE_HOME on Linux, uses ~/Library/Caches on macOS,
    and LOCALAPPDATA on Windows.  Falls back to ~/.cache.
    """
    if sys.platform == "linux":
        base = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
    elif sys.platform == "darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Caches")
    elif sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~/.cache"))
    else:
        base = os.path.expanduser("~/.cache")
    return os.path.join(base, "otel-distro-builder", "go")


def get_cache_path(version: str) -> str:
    """Return the cache directory path for a specific Go version.

    Args:
        version: Go version (e.g. "1.24.0").

    Returns:
        Absolute path to the cached Go SDK root directory.
    """
    return os.path.join(_get_cache_dir(), version)


# ── Download and extract ────────────────────────────────────────────────────


def _extract_tar_gz(archive_path: str, dest_dir: str) -> None:
    """Extract a .tar.gz archive to dest_dir."""
    with tarfile.open(archive_path, "r:gz") as tf:
        tf.extractall(dest_dir)


def _extract_zip(archive_path: str, dest_dir: str) -> None:
    """Extract a .zip archive to dest_dir."""
    with zipfile.ZipFile(archive_path, "r") as zf:
        zf.extractall(dest_dir)


def _download_go_sdk(version: str, go_os: str, go_arch: str, dest_dir: str) -> str:
    """Download and extract the Go SDK to dest_dir.

    Args:
        version: Go version (e.g. "1.24.0").
        go_os: Target OS.
        go_arch: Target architecture.
        dest_dir: Directory to extract into.

    Returns:
        Path to the extracted Go root (the directory containing bin/go).
    """
    url = build_go_url(version, go_os, go_arch)
    is_zip = go_os == "windows"
    suffix = ".zip" if is_zip else ".tar.gz"

    logger.section("Go SDK Download")
    logger.info("Download Details:", indent=1)
    logger.info(f"Version: {version}", indent=2)
    logger.info(f"OS: {go_os}", indent=2)
    logger.info(f"Architecture: {go_arch}", indent=2)
    logger.info(f"URL: {url}", indent=2)

    response = requests.get(url, stream=True, timeout=300)
    content_type = response.headers.get("content-type", "")
    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to download Go SDK from {url}. Status: {response.status_code}"
        )
    if "text/html" in content_type:
        raise RuntimeError(f"Go SDK not found at {url} (got HTML response)")

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        try:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    tmp.write(chunk)
            tmp.close()

            os.makedirs(dest_dir, exist_ok=True)

            if is_zip:
                _extract_zip(tmp.name, dest_dir)
            else:
                _extract_tar_gz(tmp.name, dest_dir)
        finally:
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    # The Go archive extracts to a "go/" subdirectory
    go_root = os.path.join(dest_dir, "go")
    go_binary = os.path.join(go_root, "bin", "go")
    if go_os == "windows":
        go_binary += ".exe"

    if not os.path.isfile(go_binary):
        raise RuntimeError(
            f"Go binary not found at {go_binary} after extracting archive"
        )

    logger.success(f"Go {version} extracted to: {go_root}")
    return go_root


# ── Public API ──────────────────────────────────────────────────────────────


def get_go_toolchain(version: str) -> str:
    """Return the GOROOT for a Go toolchain, downloading if not cached.

    Uses a shared cache directory so the same version is reused across builds.

    Args:
        version: Go version to obtain (e.g. "1.24.0").

    Returns:
        Absolute path to the Go SDK root directory (GOROOT).
    """
    cache_dir = get_cache_path(version)
    go_root = os.path.join(cache_dir, "go")
    go_os = _get_go_os()
    go_binary = os.path.join(go_root, "bin", "go")
    if go_os == "windows":
        go_binary += ".exe"

    if os.path.isfile(go_binary):
        logger.info(f"Using cached Go {version} from: {go_root}")
        return go_root

    logger.info(f"Go {version} not found in cache, downloading...")
    return _download_go_sdk(version, go_os, _get_go_arch(), cache_dir)
