"""Platform handling utilities for the OTel Distro Builder."""

import platform
from typing import List, Optional, Tuple

# Map Python's platform.system() to Go's GOOS
_GOOS_MAP = {
    "linux": "linux",
    "darwin": "darwin",
    "windows": "windows",
    "freebsd": "freebsd",
}

# Map Python's platform.machine() to Go's GOARCH
_GOARCH_MAP = {
    "x86_64": "amd64",
    "amd64": "amd64",
    "aarch64": "arm64",
    "arm64": "arm64",
    "armv7l": "arm",
    "s390x": "s390x",
    "ppc64le": "ppc64le",
}


def get_host_platform() -> tuple[str, str]:
    """Detect the current host's GOOS and GOARCH.

    Returns:
        Tuple of (goos, goarch) for the host machine.
    """
    host_os = _GOOS_MAP.get(platform.system().lower(), "linux")
    host_arch = _GOARCH_MAP.get(platform.machine().lower(), "amd64")
    return host_os, host_arch


def parse_platform_pairs(platforms: Optional[str]) -> List[Tuple[str, str]]:
    """
    Parse platforms string into a list of (os, arch) pairs.

    Args:
        platforms: Comma-separated list of platforms in GOOS/GOARCH format
                   (e.g. "linux/amd64,darwin/arm64")

    Returns:
        List of (os, arch) tuples preserving the exact requested pairs.
    """
    if not platforms:
        return []

    pairs: list[Tuple[str, str]] = []
    seen: set[Tuple[str, str]] = set()

    for plat in platforms.split(","):
        if not plat.strip():
            continue

        parts = plat.split("/")
        if len(parts) != 2:
            continue

        os_name = parts[0].strip()
        arch = parts[1].strip()
        if not os_name or not arch:
            continue

        pair = (os_name, arch)
        if pair not in seen:
            seen.add(pair)
            pairs.append(pair)

    return pairs


def parse_platforms(platforms: Optional[str]) -> Tuple[List[str], List[str]]:
    """
    Parse platforms string into lists of operating systems and architectures.

    Args:
        platforms: Comma-separated list of platforms in GOOS/GOARCH format
                   (e.g. linux/amd64,linux/arm64)

    Returns:
        Tuple of (list of operating systems, list of architectures)
    """
    pairs = parse_platform_pairs(platforms)
    if not pairs:
        return [], []

    os_set = set()
    arch_set = set()
    for os_name, arch in pairs:
        os_set.add(os_name)
        arch_set.add(arch)

    return sorted(list(os_set)), sorted(list(arch_set))


def resolve_platforms(
    platforms: Optional[str] = None,
    goos: Optional[str] = None,
    goarch: Optional[str] = None,
) -> Tuple[List[str], List[str]]:
    """
    Resolve target platforms based on input parameters.

    Priority:
    1. If goos or goarch are explicitly set, they take precedence
    2. If platforms is set and neither goos nor goarch are set, parse platforms
    3. Fall back to defaults (linux/arm64)

    Args:
        platforms: Comma-separated list of platforms in GOOS/GOARCH format
        goos: Comma-separated list of operating systems
        goarch: Comma-separated list of architectures

    Returns:
        Tuple of (list of operating systems, list of architectures)
    """
    host_os, host_arch = get_host_platform()

    # If either goos or goarch is explicitly set, they take precedence
    if goos is not None or goarch is not None:
        return (
            goos.split(",") if goos else [host_os],
            goarch.split(",") if goarch else [host_arch],
        )

    # If platforms is set and neither goos nor goarch are set, parse platforms
    if platforms:
        os_list, arch_list = parse_platforms(platforms)
        return (
            os_list if os_list else [host_os],
            arch_list if arch_list else [host_arch],
        )

    # Default to host platform
    return [host_os], [host_arch]


def resolve_platform_pairs(
    platforms: Optional[str] = None,
    goos: Optional[str] = None,
    goarch: Optional[str] = None,
) -> List[Tuple[str, str]]:
    """
    Resolve target platforms as a list of (os, arch) pairs.

    When --platforms is used, only the exact pairs are returned.
    When --goos/--goarch are used, returns the cross-product.

    Args:
        platforms: Comma-separated list of platforms in GOOS/GOARCH format
        goos: Comma-separated list of operating systems
        goarch: Comma-separated list of architectures

    Returns:
        List of (os, arch) tuples representing exact target platforms.
    """
    host_os, host_arch = get_host_platform()

    # If either goos or goarch is explicitly set, return cross-product
    if goos is not None or goarch is not None:
        os_list = goos.split(",") if goos else [host_os]
        arch_list = goarch.split(",") if goarch else [host_arch]
        return [(o, a) for o in os_list for a in arch_list]

    # If platforms is set, return exact pairs
    if platforms:
        pairs = parse_platform_pairs(platforms)
        if pairs:
            return pairs

    # Default to host platform
    return [(host_os, host_arch)]
