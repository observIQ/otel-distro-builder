"""Version parsing utilities for OpenTelemetry Collector Builder."""

import os
import re
from dataclasses import dataclass
from typing import Optional

import yaml
from packaging import version

CONTRIB_PREFIX = "github.com/open-telemetry/opentelemetry-collector-contrib/"
DEFAULT_VERSION = "0.122.0"
MIN_SUPERVISOR_VERSION = "0.122.0"


@dataclass
class BuildVersions:
    """Versions to use for building the collector."""

    ocb: str
    supervisor: str
    go: str


def load_version_mappings() -> dict:
    """Load version mappings from versions.yaml."""
    versions_file = os.path.join(os.path.dirname(__file__), "..", "versions.yaml")
    with open(versions_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["versions"]


def determine_build_versions(
    manifest_content: str,
    ocb_version: Optional[str] = None,
    supervisor_version: Optional[str] = None,
) -> BuildVersions:
    """Determine OCB and Supervisor versions to use based on manifest content and overrides.

    Args:
        manifest_content: Content of the manifest file
        ocb_version: Optional override for OCB version
        supervisor_version: Optional override for Supervisor version

    Returns:
        BuildVersions containing the determined versions
    """
    # If both versions are provided, use them
    if ocb_version and supervisor_version:
        return BuildVersions(
            ocb=ocb_version, supervisor=supervisor_version, go="1.24.1"
        )

    # Try to detect version from manifest
    try:
        contrib_version = get_contrib_version_from_manifest(manifest_content)
    except (ValueError, yaml.YAMLError):
        contrib_version = DEFAULT_VERSION

    # Load version mappings
    version_mappings = load_version_mappings()

    # Look up versions based on contrib version
    if contrib_version not in version_mappings:
        # Fall back to default version if contrib version not found
        contrib_version = DEFAULT_VERSION

    versions = version_mappings[contrib_version]

    # Override with provided versions if any
    final_ocb = ocb_version or versions["builder"]
    final_supervisor = supervisor_version or versions["supervisor"]
    final_go = versions["go"]

    return BuildVersions(
        ocb=final_ocb,
        supervisor=final_supervisor,
        go=final_go,
    )


def get_contrib_version_from_manifest(manifest_content: str) -> str:
    """Extract OpenTelemetry Contrib version from manifest content.

    Args:
        manifest_content: Content of the manifest file

    Returns:
        str: The version to use (without the 'v' prefix)

    Raises:
        ValueError: If version cannot be determined from manifest
    """
    manifest = yaml.safe_load(manifest_content)

    # Sections that can contain contrib components
    sections = [
        "extensions",
        "exporters",
        "processors",
        "receivers",
        "connectors",
        "providers",
    ]

    versions = set()

    # Examine each section
    for section in sections:
        if section not in manifest:
            continue

        # Look at each component in the section
        for component in manifest[section]:
            if "gomod" not in component:
                continue

            gomod = component["gomod"]

            # Check if it's a contrib component
            if CONTRIB_PREFIX in gomod:
                # Extract version using regex
                match = re.search(r"v(\d+\.\d+\.\d+)$", gomod)
                if match:
                    versions.add(match.group(1))

    if not versions:
        raise ValueError("No contrib components found in manifest")

    # Return the highest version
    return str(max(version.parse(v) for v in versions))
