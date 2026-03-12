"""Version parsing utilities for OpenTelemetry Collector Builder."""

import re
from dataclasses import dataclass
from typing import Optional

import yaml
from packaging import version

from .resources import get_versions_yaml_path

CONTRIB_PREFIX = "github.com/open-telemetry/opentelemetry-collector-contrib/"
MIN_SUPERVISOR_VERSION = "0.122.0"

# Fallback if versions.yaml cannot be read
_FALLBACK_VERSION = "0.144.0"


def _get_latest_version() -> str:
    """Get the latest version from versions.yaml as the default.

    Returns:
        The first (latest) version key from versions.yaml, or a hardcoded
        fallback if the file cannot be read.
    """
    try:
        versions_file = get_versions_yaml_path()
        with open(versions_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data and "versions" in data:
            keys = list(data["versions"].keys())
            if keys:
                return str(keys[0])
    except (FileNotFoundError, yaml.YAMLError, KeyError):
        pass
    return _FALLBACK_VERSION


DEFAULT_VERSION = _get_latest_version()


@dataclass
class BuildVersions:
    """Versions to use for building the collector."""

    ocb: str
    supervisor: str
    go: str
    core: str


def load_version_mappings() -> dict:
    """Load version mappings from versions.yaml."""
    versions_file = get_versions_yaml_path()
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
    # If both versions are provided, use them but look up Go/core from version mappings
    if ocb_version and supervisor_version:
        version_mappings = load_version_mappings()
        # Find the Go and core versions for this OCB (builder) version
        final_go: str = "1.24.0"
        final_core: str = DEFAULT_VERSION
        for ver_key, mapping in version_mappings.items():
            if mapping.get("builder") == ocb_version:
                final_go = mapping.get("go", "1.24.0")
                final_core = mapping.get("core", ver_key)
                break
        else:
            # OCB version not in mappings; use default version's values
            default_mapping = version_mappings.get(DEFAULT_VERSION, {})
            final_go = default_mapping.get("go", "1.24.0")
            final_core = default_mapping.get("core", DEFAULT_VERSION)
        return BuildVersions(
            ocb=ocb_version,
            supervisor=supervisor_version,
            go=final_go,
            core=final_core,
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

    final_core = versions.get("core", contrib_version)

    return BuildVersions(
        ocb=final_ocb,
        supervisor=final_supervisor,
        go=final_go,
        core=final_core,
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


def get_core_version(contrib_version: str) -> str:
    """Look up the core collector version for a given contrib version.

    Args:
        contrib_version: The contrib/OTel version (e.g. "0.144.0")

    Returns:
        The corresponding core version (e.g. "1.50.0"), or the contrib version
        itself as a fallback if not found in mappings.
    """
    try:
        mappings = load_version_mappings()
        entry = mappings.get(contrib_version, {})
        return entry.get("core", contrib_version)
    except (FileNotFoundError, yaml.YAMLError, KeyError):
        return contrib_version
