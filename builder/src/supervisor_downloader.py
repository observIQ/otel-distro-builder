"""Utility for downloading OpenTelemetry OpAMP Supervisor releases."""

import os

import requests
from logger import BuildLogger, get_logger

logger: BuildLogger = get_logger(__name__)


def download_file(url, output_file):
    """Download a file from a given URL and save it to the specified path."""
    logger.info(f"Downloading {url}...", indent=2)

    try:
        response = requests.get(url, stream=True, timeout=30)
        if response.status_code == 200:
            with open(output_file, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            logger.success(f"Successfully downloaded {url}")
        else:
            logger.error(f"Failed to download {url}: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        raise


def set_permissions(file_path, os_name):
    """Set appropriate permissions for the downloaded file."""
    if os_name != "windows":
        os.chmod(file_path, 0o777)
        logger.info(f"Set executable permissions for: {file_path}", indent=1)


def download_supervisor(output_dir, version):
    """Download the OpAMP Supervisor release artifacts."""
    base_url = f"https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/cmd%2Fopampsupervisor%2Fv{version}"

    # Define supported platform combinations
    platforms = [
        ("darwin", "arm64"),
        ("darwin", "amd64"),
        ("linux", "arm64"),
        ("linux", "amd64"),
        ("linux", "ppc64le"),
        ("windows", "amd64"),
    ]

    logger.section("Supervisor Download")
    logger.info("Download Details:", indent=1)
    logger.info(f"Version: {version}", indent=2)
    logger.info(f"Output: {output_dir}", indent=2)

    try:
        for os_name, arch in platforms:
            # Generate artifact name, output file, and download URL
            artifact_name = f"opampsupervisor_{version}_{os_name}_{arch}"
            output_file = os.path.join(output_dir, f"supervisor_{os_name}_{arch}")
            if os_name == "windows":
                artifact_name += ".exe"
                output_file += ".exe"
            download_url = f"{base_url}/{artifact_name}"

            download_file(download_url, output_file)
            set_permissions(output_file, os_name)

        logger.success(
            f"Successfully downloaded supervisor artifacts for version: {version}"
        )
        return output_dir

    except Exception as e:
        logger.error(f"Failed to download supervisor artifacts: {str(e)}")
        raise
