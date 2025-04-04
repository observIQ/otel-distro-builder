#!/usr/bin/env python3
"""Script to check the Go version used to build an OpenTelemetry Collector Contrib binary."""

import argparse
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
from urllib.request import Request, urlopen


def get_platform_info():
    """Get current platform information."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    # Map machine architectures to OTel's naming
    arch_map = {
        "x86_64": "amd64",
        "arm64": "arm64",
        "aarch64": "arm64",
    }

    return system, arch_map.get(machine, machine)


def download_binary(version, os_name, arch):
    """
    Download the binary for the specified version and platform.

    Args:
        version: Version string (e.g. "0.123.1")
        os_name: Operating system name (e.g. "darwin")
        arch: Architecture (e.g. "arm64")

    Returns:
        Path to downloaded file
    """
    # Strip 'v' prefix if present
    version = version.lstrip("v")

    url = f"https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v{version}/otelcol-contrib_{version}_{os_name}_{arch}.tar.gz"

    print(f"Downloading from: {url}")

    headers = {
        "Accept": "application/octet-stream",
        "User-Agent": "Python/check-binary-go-version",
    }

    try:
        req = Request(url, headers=headers)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".tar.gz") as tmp_file:
            with urlopen(req) as response:
                shutil.copyfileobj(response, tmp_file)
            return tmp_file.name
    except Exception as e:
        print(f"Error downloading binary: {e}", file=sys.stderr)
        sys.exit(1)


def extract_binary(archive_path):
    """
    Extract the binary from the downloaded archive.

    Args:
        archive_path: Path to the downloaded .tar.gz file

    Returns:
        Path to the extracted binary
    """
    extract_dir = tempfile.mkdtemp()
    try:
        with tarfile.open(archive_path) as tar:
            tar.extractall(extract_dir)
        binary_path = os.path.join(extract_dir, "otelcol-contrib")
        if not os.path.exists(binary_path):
            print("Binary not found in archive!", file=sys.stderr)
            sys.exit(1)
        return binary_path
    except Exception as e:
        print(f"Error extracting archive: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Clean up the archive
        os.unlink(archive_path)


def check_go_version(binary_path):
    """
    Check the Go version used to build the binary.

    Args:
        binary_path: Path to the binary to check

    Returns:
        Go version string
    """
    try:
        result = subprocess.run(
            ["go", "version", binary_path], capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error checking Go version: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Clean up the extracted files
        shutil.rmtree(os.path.dirname(binary_path))


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check Go version of OpenTelemetry Collector Contrib binary"
    )
    parser.add_argument(
        "--version",
        required=True,
        help="Version to check (e.g. 0.123.1 or v0.123.1)",
    )
    parser.add_argument(
        "--os",
        help="Operating system (defaults to current system)",
    )
    parser.add_argument(
        "--arch",
        help="Architecture (defaults to current architecture)",
    )

    args = parser.parse_args()

    # Use current platform if not specified
    os_name, arch = get_platform_info()
    os_name = args.os or os_name
    arch = args.arch or arch

    # Download, extract, and check version
    archive_path = download_binary(args.version, os_name, arch)
    binary_path = extract_binary(archive_path)
    version_info = check_go_version(binary_path)

    print(f"\nVersion info: {version_info}")


if __name__ == "__main__":
    main()
