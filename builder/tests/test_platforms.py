"""Tests for the platforms module."""

from unittest.mock import patch, mock_open
import pytest

from src.platforms import parse_platforms, resolve_platforms


@pytest.mark.base
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


@pytest.mark.base
@pytest.mark.parametrize(
    "platforms,goos,goarch,expected_goos,expected_goarch",
    [
        # Default case - no inputs
        (None, None, None, ["linux"], ["arm64"]),
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
        # OS only overrides
        (
            "linux/amd64,darwin/arm64",
            "windows,darwin",
            None,
            ["windows", "darwin"],
            ["arm64"],
        ),
        # ARCH only overrides
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
            ["arm64"],
        ),
        # Empty string inputs
        ("", "", "", ["linux"], ["arm64"]),
        # OS override with empty ARCH
        (None, "windows", "", ["windows"], ["arm64"]),
        # ARCH override with empty OS
        (None, "", "amd64", ["linux"], ["amd64"]),
    ],
)
def test_resolve_platforms(platforms, goos, goarch, expected_goos, expected_goarch):
    """Test platform resolution with various input combinations."""
    result_goos, result_goarch = resolve_platforms(
        platforms=platforms,
        goos=goos,
        goarch=goarch,
    )
    assert result_goos == expected_goos
    assert result_goarch == expected_goarch
