#!/usr/bin/env python3
"""Script to list available versions of OCB, Collector-Contrib, and Supervisor from GitHub releases."""

import argparse
import json
import re
import sys
import yaml
from urllib.request import Request, urlopen


def get_releases():
    """Get all releases from the opentelemetry-collector-releases repository."""
    url = "https://api.github.com/repos/open-telemetry/opentelemetry-collector-releases/releases"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Python/list-versions",
    }

    try:
        req = Request(url, headers=headers)
        with urlopen(req) as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"Error fetching releases: {e}", file=sys.stderr)
        sys.exit(1)


def extract_versions(releases, component):
    """
    Extract versions from release assets.

    Args:
        releases: List of release data from GitHub API
        component: Which component to extract versions for ('ocb', 'contrib', or 'supervisor')
    """
    versions = set()

    # Define patterns for each component
    patterns = {
        "ocb": re.compile(r"ocb_(\d+\.\d+\.\d+)_"),
        "contrib": re.compile(r"otelcol-contrib_(\d+\.\d+\.\d+)_"),
        "supervisor": re.compile(r"opampsupervisor_(\d+\.\d+\.\d+)_"),
    }

    # For supervisor, we need to check the release tag as well
    supervisor_tag = re.compile(r"cmd/opampsupervisor/v\d+\.\d+\.\d+")

    pattern = patterns[component]

    for release in releases:
        # For supervisor, only process releases with matching tags
        if component == "supervisor" and not supervisor_tag.match(release["tag_name"]):
            continue

        for asset in release.get("assets", []):
            name = asset["name"]
            match = pattern.search(name)
            if match:
                version = match.group(1)
                versions.add(version)

    return sorted(versions, key=lambda v: [int(x) for x in v.split(".")])


def print_versions(versions, component_name, yaml_data=None):
    """Print available versions for a component and optionally add to yaml_data."""
    if not versions:
        print(f"No {component_name} versions found!", file=sys.stderr)
        return False

    print(f"\n{component_name} versions:")
    print("\n".join(versions))

    if yaml_data is not None:
        # Convert component name to a key-friendly format
        key = component_name.lower().replace(" ", "_")
        yaml_data[key] = {
            "versions": versions,
        }

    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="List available versions of OpenTelemetry components."
    )
    parser.add_argument(
        "--component",
        choices=["all", "ocb", "contrib", "supervisor"],
        default="all",
        help="Which component to list versions for",
    )
    parser.add_argument("--output", help="Output YAML file path", default=None)
    args = parser.parse_args()

    print("Fetching releases...")
    releases = get_releases()

    components = {
        "ocb": "OpenTelemetry Collector Builder",
        "contrib": "OpenTelemetry Collector Contrib",
        "supervisor": "OpenTelemetry Supervisor",
    }

    if args.component == "all":
        components_to_check = components.items()
    else:
        components_to_check = [(args.component, components[args.component])]

    success = True
    yaml_data = {} if args.output else None

    for component_id, component_name in components_to_check:
        versions = extract_versions(releases, component_id)
        if not print_versions(versions, component_name, yaml_data):
            success = False

    if args.output and yaml_data:
        try:
            with open(args.output, "w") as f:
                yaml.safe_dump(yaml_data, f, sort_keys=False)
            print(f"\nYAML output written to: {args.output}")
        except Exception as e:
            print(f"Error writing YAML file: {e}", file=sys.stderr)
            success = False

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
