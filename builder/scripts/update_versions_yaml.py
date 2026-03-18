#!/usr/bin/env python3
"""Update builder/versions.yaml with latest upstream OpenTelemetry versions.

Fetches the latest releases from the opentelemetry-collector-releases repo,
computes version mappings (core, supervisor, builder, go), and updates
builder/versions.yaml with any new versions found.

Usage:
    # Dry run (prints what would be updated):
    python update_versions_yaml.py

    # Apply changes:
    python update_versions_yaml.py --write

    # Check if updates are available (CI):
    python update_versions_yaml.py --check
"""

import argparse
import os
import re
import sys
import time

import requests
import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VERSIONS_YAML_PATH = os.path.join(SCRIPT_DIR, "..", "versions.yaml")

GITHUB_API_BASE = "https://api.github.com"
RAW_GITHUB_BASE = "https://raw.githubusercontent.com"
RELEASES_REPO = "open-telemetry/opentelemetry-collector-releases"
CONTRIB_REPO = "open-telemetry/opentelemetry-collector-contrib"

MIN_SUPERVISOR_VERSION = "0.122.0"
MIN_CONTRIB_VERSION = "0.120.0"

YAML_HEADER = """\
versions:
  # Format:
  # contrib_version:
  #   core: <version>       # Core collector module version (go.opentelemetry.io/collector/...)
  #   supervisor: <version>
  #   builder: <version>
  #   go: <version>
  #
  # Core vs Contrib versioning:
  # Since the 1.0 release, core modules (go.opentelemetry.io/collector/...) use v1.x
  # while contrib modules (github.com/open-telemetry/opentelemetry-collector-contrib/...) use v0.x.
  # Formula: core = 1.(contrib_minor - 94).patch
"""


def version_tuple(v):
    """Parse 'x.y.z' into a comparable tuple."""
    return tuple(int(x) for x in v.split("."))


def _build_session(token=None):
    """Create a requests.Session with auth and retry headers."""
    session = requests.Session()
    session.headers.update(
        {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "otel-distro-builder/update-versions",
        }
    )
    if token:
        session.headers["Authorization"] = f"token {token}"
    return session


def github_get(url, token=None, retries=3, backoff=2):
    """GET a JSON response from the GitHub API. Returns (parsed_json, headers).

    Retries on transient errors (5xx, timeouts) with exponential backoff.
    """
    session = _build_session(token)
    last_exc = None
    for attempt in range(retries):
        try:
            resp = session.get(url, timeout=30)
            resp.raise_for_status()
            return resp.json(), dict(resp.headers)
        except requests.exceptions.HTTPError as exc:
            last_exc = exc
            if resp.status_code < 500:
                raise
            wait = backoff**attempt
            print(
                f"    Retrying ({attempt + 1}/{retries}) after HTTP {resp.status_code}, "
                f"waiting {wait}s...",
                file=sys.stderr,
            )
            time.sleep(wait)
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
        ) as exc:
            last_exc = exc
            wait = backoff**attempt
            print(
                f"    Retrying ({attempt + 1}/{retries}) after {exc}, "
                f"waiting {wait}s...",
                file=sys.stderr,
            )
            time.sleep(wait)
    raise last_exc  # type: ignore[misc]


def fetch_all_releases(token=None):
    """Fetch all releases from the opentelemetry-collector-releases repo (paginated).

    Uses per_page=30 (default) because this repo has very large release payloads
    (many assets per release) and per_page=100 frequently causes 504 timeouts.
    """
    all_releases = []
    page = 1
    while True:
        url = (
            f"{GITHUB_API_BASE}/repos/{RELEASES_REPO}/releases?per_page=30&page={page}"
        )
        releases, headers = github_get(url, token)
        if not releases:
            break
        all_releases.extend(releases)
        if 'rel="next"' not in headers.get("Link", ""):
            break
        page += 1
    return all_releases


def extract_component_versions(releases):
    """Return (contrib_set, ocb_set, supervisor_set) of version strings."""
    contrib = set()
    ocb = set()
    supervisor = set()

    contrib_re = re.compile(r"otelcol-contrib_(\d+\.\d+\.\d+)_")
    ocb_re = re.compile(r"ocb_(\d+\.\d+\.\d+)_")
    sup_re = re.compile(r"opampsupervisor_(\d+\.\d+\.\d+)_")
    sup_tag_re = re.compile(r"cmd/opampsupervisor/v\d+\.\d+\.\d+")

    for release in releases:
        is_sup = bool(sup_tag_re.match(release.get("tag_name", "")))
        for asset in release.get("assets", []):
            name = asset["name"]
            m = contrib_re.search(name)
            if m:
                contrib.add(m.group(1))
            m = ocb_re.search(name)
            if m:
                ocb.add(m.group(1))
            if is_sup:
                m = sup_re.search(name)
                if m:
                    supervisor.add(m.group(1))

    return contrib, ocb, supervisor


def compute_core_version(contrib_version):
    """Apply the formula: core = 1.(contrib_minor - 94).patch."""
    parts = [int(x) for x in contrib_version.split(".")]
    core_minor = parts[1] - 94
    if core_minor < 0:
        raise ValueError(f"Contrib version {contrib_version}: minor ({parts[1]}) < 94")
    return f"1.{core_minor}.{parts[2]}"


def _fetch_gomod_text(version_tag, token=None):
    """Fetch go.mod content for a given contrib version tag. Returns text or None on 404."""
    url = f"{RAW_GITHUB_BASE}/{CONTRIB_REPO}/v{version_tag}/go.mod"
    session = _build_session(token)
    last_exc = None
    for attempt in range(3):
        try:
            resp = session.get(url, timeout=30)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.text
        except requests.exceptions.HTTPError as exc:
            last_exc = exc
            if resp.status_code < 500:
                raise
            wait = 2**attempt
            print(
                f"    Retrying go.mod fetch ({attempt + 1}/3) for v{version_tag}, "
                f"waiting {wait}s...",
                file=sys.stderr,
            )
            time.sleep(wait)
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
        ) as exc:
            last_exc = exc
            wait = 2**attempt
            print(
                f"    Retrying go.mod fetch ({attempt + 1}/3) for v{version_tag}, "
                f"waiting {wait}s...",
                file=sys.stderr,
            )
            time.sleep(wait)
    raise last_exc  # type: ignore[misc]


def fetch_go_version(contrib_version, token=None):
    """Fetch the Go version from contrib's go.mod at the given release tag.

    For patch releases (e.g. 0.146.1) where the contrib repo may not have a
    matching tag, falls back to the base version (0.146.0).
    """
    text = _fetch_gomod_text(contrib_version, token)
    if text is None:
        parts = contrib_version.split(".")
        if int(parts[2]) > 0:
            base = f"{parts[0]}.{parts[1]}.0"
            print(
                f"    go.mod not found for v{contrib_version}, "
                f"falling back to v{base}",
                file=sys.stderr,
            )
            text = _fetch_gomod_text(base, token)
    if text is None:
        raise ValueError(
            f"Could not fetch go.mod for v{contrib_version} (or base version)"
        )
    m = re.search(r"^go\s+(\d+\.\d+(?:\.\d+)?)\s*$", text, re.MULTILINE)
    if not m:
        raise ValueError(f"No go directive in go.mod for v{contrib_version}")
    ver = m.group(1)
    if len(ver.split(".")) == 2:
        ver += ".0"
    return ver


def best_match(target, available):
    """Find the best matching version: exact first, then base version for patches."""
    if target in available:
        return target
    parts = target.split(".")
    if int(parts[2]) > 0:
        base = f"{parts[0]}.{parts[1]}.0"
        if base in available:
            return base
    return None


def load_existing(path):
    """Load existing version mappings from versions.yaml."""
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not data or "versions" not in data:
        return {}
    return dict(data["versions"])


def serialize_versions_yaml(versions):
    """Render the complete versions.yaml content with stable formatting."""
    sorted_keys = sorted(versions.keys(), key=version_tuple, reverse=True)
    lines = [YAML_HEADER]

    for ver in sorted_keys:
        e = versions[ver]
        lines.append(f'  "{ver}":')
        lines.append(f'    core: "{e["core"]}"')

        sup = e["supervisor"]
        sup_line = f'    supervisor: "{sup}"'
        if sup != ver:
            if int(ver.split(".")[2]) > 0:
                sup_line += "  # Patch release, uses base version"
            elif version_tuple(ver) < version_tuple(MIN_SUPERVISOR_VERSION):
                sup_line += (
                    f"  # Uses {MIN_SUPERVISOR_VERSION} since supervisor"
                    f" started at {MIN_SUPERVISOR_VERSION}"
                )
        lines.append(sup_line)

        lines.append(f'    builder: "{e["builder"]}"')
        lines.append(f'    go: "{e["go"]}"')

    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Apply changes to versions.yaml",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if updates are available (for CI)",
    )
    parser.add_argument(
        "--max-entries",
        type=int,
        default=40,
        help="Maximum number of version entries to keep (default: 40)",
    )
    parser.add_argument(
        "--versions-file",
        default=VERSIONS_YAML_PATH,
        help="Path to versions.yaml",
    )
    args = parser.parse_args()

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")

    print("Fetching releases from GitHub...", file=sys.stderr)
    releases = fetch_all_releases(token)

    print("Extracting component versions...", file=sys.stderr)
    contrib_versions, ocb_versions, supervisor_versions = extract_component_versions(
        releases
    )
    print(
        f"Found {len(contrib_versions)} contrib, {len(ocb_versions)} OCB, "
        f"{len(supervisor_versions)} supervisor versions",
        file=sys.stderr,
    )

    existing = load_existing(args.versions_file)

    min_tuple = version_tuple(MIN_CONTRIB_VERSION)
    eligible = {v for v in contrib_versions if version_tuple(v) >= min_tuple}
    new_versions = eligible - set(existing.keys())

    if not new_versions:
        print("No new versions to add.", file=sys.stderr)
        if args.check:
            sys.exit(0)
        return

    sorted_new = sorted(new_versions, key=version_tuple, reverse=True)
    print(f"New versions to add: {sorted_new}", file=sys.stderr)

    if args.check:
        sys.exit(1)

    merged = dict(existing)

    for ver in sorted_new:
        print(f"  Processing {ver}...", file=sys.stderr)

        try:
            core = compute_core_version(ver)
        except ValueError as exc:
            print(f"    Skipping {ver}: {exc}", file=sys.stderr)
            continue

        try:
            go_ver = fetch_go_version(ver, token)
        except (requests.exceptions.RequestException, ValueError) as exc:
            print(
                f"    ERROR fetching go.mod for v{ver}: {exc}",
                file=sys.stderr,
            )
            sys.exit(1)

        builder_ver = best_match(ver, ocb_versions)
        if builder_ver is None:
            builder_ver = ver
            print(
                f"    WARNING: No OCB asset for {ver}, assuming {ver}",
                file=sys.stderr,
            )

        sup_ver = best_match(ver, supervisor_versions)
        if sup_ver is None:
            if version_tuple(ver) < version_tuple(MIN_SUPERVISOR_VERSION):
                sup_ver = MIN_SUPERVISOR_VERSION
            else:
                sup_ver = ver
                print(
                    f"    WARNING: No supervisor asset for {ver}, assuming {ver}",
                    file=sys.stderr,
                )

        merged[ver] = {
            "core": core,
            "supervisor": sup_ver,
            "builder": builder_ver,
            "go": go_ver,
        }

    all_sorted = sorted(merged.keys(), key=version_tuple, reverse=True)
    if len(all_sorted) > args.max_entries:
        for old in all_sorted[args.max_entries :]:
            del merged[old]

    if args.write:
        content = serialize_versions_yaml(merged)
        with open(args.versions_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated {args.versions_file}", file=sys.stderr)

    latest = sorted(merged.keys(), key=version_tuple, reverse=True)[0]
    print(latest)


if __name__ == "__main__":
    main()
