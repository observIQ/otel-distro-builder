"""Utility for downloading and managing Goreleaser (OSS) and Syft binaries."""

import os
import platform
import shutil
import tarfile
import tempfile

import requests

from .ocb_downloader import get_architecture
from .logger import BuildLogger, get_logger

logger: BuildLogger = get_logger(__name__)

# Tool versions (Dockerfile uses goreleaser-pro; CLI uses OSS for no-license UX)
GORELEASER_VERSION = "2.13.3"
SYFT_VERSION = "1.21.0"


# ── Platform helpers ────────────────────────────────────────────────────────


def _get_os_name_raw() -> str:
    """Return raw platform name (Darwin, Linux, Windows)."""
    return platform.system()


def _goreleaser_asset_os(raw: str) -> str:
    """Goreleaser assets use uname -s casing: Darwin, Linux, Windows."""
    if raw in ("Darwin", "Linux", "Windows"):
        return raw
    raise ValueError(f"Unsupported OS for goreleaser: {raw}")


def _goreleaser_asset_arch(arch: str) -> str:
    """Goreleaser assets: amd64 -> x86_64, arm64 stays arm64."""
    if arch == "amd64":
        return "x86_64"
    return arch


def _syft_asset_os(raw: str) -> str:
    """Syft assets use lowercase: darwin, linux."""
    return raw.lower()


def _syft_asset_arch(arch: str) -> str:
    """Syft assets use our standard names: amd64, arm64."""
    return arch


# ── Generic tar.gz download + extract ───────────────────────────────────────


def _download_and_extract(url: str, binary_name: str, output_dir: str) -> str:
    """Download a tar.gz, extract `binary_name`, return absolute path."""
    output_path = os.path.join(output_dir, binary_name)

    logger.info(f"Downloading from: {url}", indent=1)
    response = requests.get(url, stream=True, timeout=120)
    content_type = response.headers.get("content-type", "")
    if response.status_code != 200:
        raise RuntimeError(f"Failed to download from {url}. Status: {response.status_code}")
    if "text/html" in content_type:
        raise RuntimeError(f"File not found at {url} (got HTML)")

    os.makedirs(output_dir, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
        try:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    tmp.write(chunk)
            tmp.close()
            with tempfile.TemporaryDirectory() as extract_dir:
                with tarfile.open(tmp.name, "r:gz") as tf:
                    tf.extractall(extract_dir)
                # Walk to find the binary (may be at root or in a subdir)
                for root, _dirs, files in os.walk(extract_dir):
                    for f in files:
                        if f == binary_name:
                            shutil.copy2(os.path.join(root, f), output_path)
                            break
                    else:
                        continue
                    break
                else:
                    raise RuntimeError(f"Binary '{binary_name}' not found in archive from {url}")
        finally:
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    os_raw = _get_os_name_raw()
    if os_raw != "Windows":
        os.chmod(output_path, 0o755)
    return output_path


# ── Goreleaser ──────────────────────────────────────────────────────────────


def _build_goreleaser_url(version: str, os_asset: str, arch_asset: str) -> str:
    """Goreleaser OSS download URL (no version in filename)."""
    base = "https://github.com/goreleaser/goreleaser/releases/download"
    ext = "zip" if os_asset == "Windows" else "tar.gz"
    return f"{base}/v{version}/goreleaser_{os_asset}_{arch_asset}.{ext}"


def get_goreleaser_path(tools_dir: str) -> str:
    """Return path to goreleaser binary, downloading if not present."""
    os_raw = _get_os_name_raw()
    binary_name = "goreleaser.exe" if os_raw == "Windows" else "goreleaser"
    existing = os.path.join(tools_dir, binary_name)
    if os.path.isfile(existing):
        return existing

    arch = get_architecture()
    os_asset = _goreleaser_asset_os(os_raw)
    arch_asset = _goreleaser_asset_arch(arch)
    url = _build_goreleaser_url(GORELEASER_VERSION, os_asset, arch_asset)

    logger.section("Goreleaser Download")
    logger.info("Download Details:", indent=1)
    logger.info(f"Version: {GORELEASER_VERSION}", indent=2)
    logger.info(f"OS: {os_asset}", indent=2)
    logger.info(f"Architecture: {arch} ({arch_asset})", indent=2)
    logger.info(f"URL: {url}", indent=2)

    path = _download_and_extract(url, binary_name, tools_dir)
    logger.success(f"Downloaded goreleaser to: {path}")
    return path


# ── Syft ────────────────────────────────────────────────────────────────────


def _build_syft_url(version: str, os_asset: str, arch_asset: str) -> str:
    """Syft download URL (version IS in the filename)."""
    base = "https://github.com/anchore/syft/releases/download"
    return f"{base}/v{version}/syft_{version}_{os_asset}_{arch_asset}.tar.gz"


def get_syft_path(tools_dir: str) -> str:
    """Return path to syft binary, downloading if not present."""
    os_raw = _get_os_name_raw()
    binary_name = "syft.exe" if os_raw == "Windows" else "syft"
    existing = os.path.join(tools_dir, binary_name)
    if os.path.isfile(existing):
        return existing

    arch = get_architecture()
    os_asset = _syft_asset_os(os_raw)
    arch_asset = _syft_asset_arch(arch)
    url = _build_syft_url(SYFT_VERSION, os_asset, arch_asset)

    logger.section("Syft Download")
    logger.info("Download Details:", indent=1)
    logger.info(f"Version: {SYFT_VERSION}", indent=2)
    logger.info(f"OS: {os_asset}", indent=2)
    logger.info(f"Architecture: {arch_asset}", indent=2)
    logger.info(f"URL: {url}", indent=2)

    path = _download_and_extract(url, binary_name, tools_dir)
    logger.success(f"Downloaded syft to: {path}")
    return path
