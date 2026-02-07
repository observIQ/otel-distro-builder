"""Tests for the platforms module."""

from unittest.mock import patch

import pytest
from src.platforms import (get_host_platform, parse_platform_pairs,
                           parse_platforms, resolve_platform_pairs,
                           resolve_platforms)

# All tests that depend on default platform behavior mock get_host_platform
# to return ("linux", "amd64") so tests are deterministic on any machine.
MOCK_HOST = ("linux", "amd64")


@pytest.mark.unit
@pytest.mark.parametrize(
    "system,machine,expected",
    [
        ("Linux", "x86_64", ("linux", "amd64")),
        ("Darwin", "arm64", ("darwin", "arm64")),
        ("Darwin", "x86_64", ("darwin", "amd64")),
        ("Windows", "AMD64", ("windows", "amd64")),
        ("Linux", "aarch64", ("linux", "arm64")),
        ("Linux", "armv7l", ("linux", "arm")),
        ("Linux", "s390x", ("linux", "s390x")),
        ("Linux", "ppc64le", ("linux", "ppc64le")),
        # Unknown values fall back to linux/amd64
        ("UnknownOS", "unknown_arch", ("linux", "amd64")),
    ],
)
def test_get_host_platform(system, machine, expected):
    """Test host platform detection with various system/machine combos."""
    with (
        patch("src.platforms.platform.system", return_value=system),
        patch("src.platforms.platform.machine", return_value=machine),
    ):
        assert get_host_platform() == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "platforms,expected",
    [
        (None, []),
        ("", []),
        ("linux/amd64", [("linux", "amd64")]),
        ("linux/amd64,linux/arm64", [("linux", "amd64"), ("linux", "arm64")]),
        ("linux/amd64,darwin/amd64", [("linux", "amd64"), ("darwin", "amd64")]),
        ("linux", []),  # Invalid format
        ("linux/", []),  # Missing arch
        ("/amd64", []),  # Missing os
        ("linux/amd64/v8", []),  # Too many parts
        (
            "linux/amd64,invalid,darwin/arm64",
            [("linux", "amd64"), ("darwin", "arm64")],
        ),  # Skip invalid
        (
            "linux/amd64,linux/,/arm64,darwin/arm64",
            [("linux", "amd64"), ("darwin", "arm64")],  # Skip invalid parts
        ),
        # Deduplication
        (
            "linux/amd64,linux/amd64",
            [("linux", "amd64")],
        ),
    ],
)
def test_parse_platform_pairs(platforms, expected):
    """Test platform pair parsing with various inputs."""
    assert parse_platform_pairs(platforms) == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "platforms,expected",
    [
        (None, ([], [])),
        ("", ([], [])),
        ("linux/amd64", (["linux"], ["amd64"])),
        ("linux/amd64,linux/arm64", (["linux"], ["amd64", "arm64"])),
        ("linux/amd64,darwin/amd64", (["darwin", "linux"], ["amd64"])),
        ("linux", ([], [])),  # Invalid format
        ("linux/", ([], [])),  # Missing arch
        ("/amd64", ([], [])),  # Missing os
        ("linux/amd64/v8", ([], [])),  # Too many parts
        (
            "linux/amd64,invalid,darwin/arm64",
            (["darwin", "linux"], ["amd64", "arm64"]),
        ),  # Skip invalid
        (
            "linux/amd64,linux/,/arm64,darwin/arm64",
            (["darwin", "linux"], ["amd64", "arm64"]),  # Skip invalid parts
        ),
    ],
)
def test_parse_platforms(platforms, expected):
    """Test platform string parsing with various inputs."""
    assert parse_platforms(platforms) == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "platforms,goos,goarch,expected_goos,expected_goarch",
    [
        # Default case - no inputs (falls back to host)
        (None, None, None, ["linux"], ["amd64"]),
        # Platforms only
        (
            "linux/amd64,darwin/arm64",
            None,
            None,
            ["darwin", "linux"],
            ["amd64", "arm64"],
        ),
        # OS and ARCH override platforms
        (
            "linux/amd64,darwin/arm64",
            "windows",
            "arm64,amd64",
            ["windows"],
            ["arm64", "amd64"],
        ),
        # OS only overrides (arch defaults to host)
        (
            "linux/amd64,darwin/arm64",
            "windows,darwin",
            None,
            ["windows", "darwin"],
            ["amd64"],
        ),
        # ARCH only overrides (os defaults to host)
        (
            "linux/amd64,darwin/arm64",
            None,
            "amd64,arm64",
            ["linux"],
            ["amd64", "arm64"],
        ),
        # Invalid platforms with no overrides
        (
            "invalid,format",
            None,
            None,
            ["linux"],
            ["amd64"],
        ),
        # Empty string inputs
        ("", "", "", ["linux"], ["amd64"]),
        # OS override with empty ARCH (arch defaults to host)
        (None, "windows", "", ["windows"], ["amd64"]),
        # ARCH override with empty OS (os defaults to host)
        (None, "", "amd64", ["linux"], ["amd64"]),
    ],
)
def test_resolve_platforms(platforms, goos, goarch, expected_goos, expected_goarch):
    """Test platform resolution with various input combinations."""
    with patch("src.platforms.get_host_platform", return_value=MOCK_HOST):
        result_goos, result_goarch = resolve_platforms(
            platforms=platforms,
            goos=goos,
            goarch=goarch,
        )
    assert result_goos == expected_goos
    assert result_goarch == expected_goarch


@pytest.mark.unit
@pytest.mark.parametrize(
    "platforms,goos,goarch,expected_pairs",
    [
        # Default case - no inputs (falls back to host)
        (None, None, None, [("linux", "amd64")]),
        # Platforms preserves exact pairs (no cross-product)
        (
            "darwin/arm64,linux/amd64",
            None,
            None,
            [("darwin", "arm64"), ("linux", "amd64")],
        ),
        # goos/goarch produce cross-product
        (
            None,
            "darwin,linux",
            "amd64,arm64",
            [
                ("darwin", "amd64"),
                ("darwin", "arm64"),
                ("linux", "amd64"),
                ("linux", "arm64"),
            ],
        ),
        # goos/goarch override platforms (cross-product)
        (
            "darwin/arm64,linux/amd64",
            "windows",
            "arm64,amd64",
            [("windows", "arm64"), ("windows", "amd64")],
        ),
        # Single platform
        (
            "darwin/arm64",
            None,
            None,
            [("darwin", "arm64")],
        ),
        # Invalid platforms fall back to host default
        (
            "invalid,format",
            None,
            None,
            [("linux", "amd64")],
        ),
    ],
)
def test_resolve_platform_pairs(platforms, goos, goarch, expected_pairs):
    """Test platform pair resolution preserves exact pairs from --platforms."""
    with patch("src.platforms.get_host_platform", return_value=MOCK_HOST):
        result = resolve_platform_pairs(
            platforms=platforms,
            goos=goos,
            goarch=goarch,
        )
    assert result == expected_pairs
