"""Platform handling utilities for the OTel Distro Builder."""

from typing import List, Optional, Tuple


def parse_platforms(platforms: Optional[str]) -> Tuple[List[str], List[str]]:
    """
    Parse platforms string into lists of operating systems and architectures.

    Args:
        platforms: Comma-separated list of platforms in GOOS/GOARCH format (e.g. linux/amd64,linux/arm64)

    Returns:
        Tuple of (list of operating systems, list of architectures)
    """
    if not platforms:
        return [], []

    os_set = set()
    arch_set = set()

    for platform in platforms.split(","):
        # Skip empty platforms
        if not platform.strip():
            continue

        parts = platform.split("/")
        # Only accept exactly 2 parts: os/arch
        if len(parts) != 2:
            continue

        # Skip if either part is empty
        if not parts[0].strip() or not parts[1].strip():
            continue

        os_set.add(parts[0].strip())
        arch_set.add(parts[1].strip())

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
    # If either goos or goarch is explicitly set, they take precedence
    if goos is not None or goarch is not None:
        return (
            goos.split(",") if goos else ["linux"],
            goarch.split(",") if goarch else ["arm64"],
        )

    # If platforms is set and neither goos nor goarch are set, parse platforms
    if platforms:
        os_list, arch_list = parse_platforms(platforms)
        return (
            os_list if os_list else ["linux"],
            arch_list if arch_list else ["arm64"],
        )

    # Default to linux/arm64
    return ["linux"], ["arm64"]
