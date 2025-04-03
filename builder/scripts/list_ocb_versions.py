#!/usr/bin/env python3
"""Script to list available OCB versions from GitHub releases."""

import json
import re
import sys
from urllib.request import Request, urlopen


def get_releases():
    """Get all releases from the opentelemetry-collector-releases repository."""
    url = "https://api.github.com/repos/open-telemetry/opentelemetry-collector-releases/releases"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Python/list-ocb-versions",
    }

    try:
        req = Request(url, headers=headers)
        with urlopen(req) as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"Error fetching releases: {e}", file=sys.stderr)
        sys.exit(1)


def extract_ocb_versions(releases):
    """Extract OCB versions and their available platforms from release assets."""
    versions = {}
    pattern = re.compile(r"ocb_(\d+\.\d+\.\d+)_([^_]+)_([^_\.]+)")

    for release in releases:
        for asset in release.get("assets", []):
            name = asset["name"]
            match = pattern.search(name)
            if match:
                version, os_name, arch = match.groups()
                if version not in versions:
                    versions[version] = {}
                if os_name not in versions[version]:
                    versions[version][os_name] = set()
                versions[version][os_name].add(arch)

    return versions


def main():
    """Main entry point."""
    print("Fetching OCB releases...")
    releases = get_releases()
    versions = extract_ocb_versions(releases)

    if not versions:
        print("No OCB versions found!", file=sys.stderr)
        sys.exit(1)

    print("\nAvailable OCB versions and platforms:")
    for version in sorted(
        versions.keys(), key=lambda v: [int(x) for x in v.split(".")]
    ):
        print(f"\n{version}:")
        for os_name in sorted(versions[version].keys()):
            archs = sorted(versions[version][os_name])
            print(f"  {os_name}: {', '.join(archs)}")

    print(f"\nTotal versions: {len(versions)}")
    latest = sorted(versions.keys(), key=lambda v: [int(x) for x in v.split(".")])[-1]
    print(f"Latest version: {latest}")


if __name__ == "__main__":
    main()
