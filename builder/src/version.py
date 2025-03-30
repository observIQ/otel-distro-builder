"""Version parsing utilities for OpenTelemetry Collector Builder."""

import re

import yaml
from packaging import version

CONTRIB_PREFIX = "github.com/open-telemetry/opentelemetry-collector-contrib/"


def get_otel_contrib_version_from_manifest(manifest_content: str) -> str:
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
