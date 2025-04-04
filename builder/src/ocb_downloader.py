"""Utility for downloading and managing OpenTelemetry Collector Builder (OCB) binaries."""

import os

import requests

from .logger import BuildLogger, get_logger

logger: BuildLogger = get_logger(__name__)


def get_architecture():
    """Determine the architecture of the current system."""
    arch = os.uname().machine
    if arch == "x86_64":
        return "amd64"
    if arch in ["arm64", "aarch64"]:
        return "arm64"
    if arch == "ppc64le":
        return "ppc64le"
    logger.error(f"Unsupported architecture: {arch}")
    raise ValueError(f"Unsupported architecture: {arch}")


def build_ocb_url(version, os_name, arch):
    """Construct the OCB download URL based on version, OS, and architecture."""
    base_url = "https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download"
    url = f"{base_url}/cmd%2Fbuilder%2Fv{version}/ocb_{version}_{os_name}_{arch}"
    if os_name == "windows":
        url += ".exe"
    return url


def download_file(url, output_file):
    """Download a file from a given URL and save it to the specified path."""
    logger.info(f"Downloading from: {url}", indent=1)
    response = requests.get(url, stream=True, timeout=30)

    # Log response details for debugging
    logger.info(f"Response status: {response.status_code}", indent=2)
    logger.info(
        f"Content type: {response.headers.get('content-type', 'none')}", indent=2
    )
    logger.info(
        f"Content length: {response.headers.get('content-length', 'none')}", indent=2
    )

    # Check if we got an actual binary file (GitHub returns HTML with 200 for missing files)
    content_type = response.headers.get("content-type", "")
    if "text/html" in content_type and "<html" in response.text[:100].lower():
        logger.error("Failed to download file. Got HTML response instead of binary.")
        raise RuntimeError(f"File not found at {url}")

    if response.status_code == 200:
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            with open(output_file, "wb") as file:
                bytes_written = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # Filter out keep-alive chunks
                        file.write(chunk)
                        bytes_written += len(chunk)

            if not os.path.getsize(output_file):
                os.remove(output_file)
                raise RuntimeError("Downloaded file is empty")

            logger.success(f"Downloaded file to: {output_file} ({bytes_written} bytes)")
        except Exception as e:
            if os.path.exists(output_file):
                os.remove(output_file)
            raise RuntimeError(f"Failed to save file: {str(e)}") from e
    else:
        logger.error(f"Failed to download file. Status code: {response.status_code}")
        raise RuntimeError(
            f"Failed to download file from {url}. Status code: {response.status_code}"
        )


def set_permissions(file_path, os_name):
    """Set appropriate permissions for the downloaded file."""
    if os_name != "windows":
        os.chmod(file_path, 0o777)
        logger.info(f"Set executable permissions for: {file_path}", indent=1)


def download_ocb(version, output_dir):
    """Download the OCB binary for the specified version and store it in the output directory."""
    logger.section("OCB Download")

    os_name = os.uname().sysname.lower()
    arch = get_architecture()
    output_file = os.path.join(output_dir, f"ocb_{version}_{os_name}_{arch}")
    if os_name == "windows":
        output_file += ".exe"

    logger.info("Download Details:", indent=1)
    logger.info(f"Version: {version}", indent=2)
    logger.info(f"OS: {os_name}", indent=2)
    logger.info(f"Architecture: {arch}", indent=2)
    logger.info(f"Output: {output_file}", indent=2)

    if os.path.isfile(output_file):
        logger.success(f"OCB binary already exists at: {output_file}")
        return output_file

    url = build_ocb_url(version, os_name, arch)
    download_file(url, output_file)
    set_permissions(output_file, os_name)

    logger.success(f"Successfully prepared OCB {version} for {os_name}/{arch}")
    return output_file
