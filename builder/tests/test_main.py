"""Tests for the main module."""

from unittest.mock import mock_open, patch

import pytest
from src.main import main


@pytest.mark.unit
@pytest.mark.parametrize(
    "args,expected_goos,expected_goarch",
    [
        # Default case - just manifest
        (["--manifest", "test.yaml"], ["linux"], ["arm64"]),
        # Platforms only
        (
            ["--manifest", "test.yaml", "--platforms", "linux/amd64,darwin/arm64"],
            ["darwin", "linux"],
            ["amd64", "arm64"],
        ),
        # OS and ARCH override platforms
        (
            [
                "--manifest",
                "test.yaml",
                "--platforms",
                "linux/amd64,darwin/arm64",
                "--goos",
                "windows",
                "--goarch",
                "arm64,amd64",
            ],
            ["windows"],
            ["arm64", "amd64"],
        ),
        # OS only
        (
            ["--manifest", "test.yaml", "--goos", "windows,darwin"],
            ["windows", "darwin"],
            ["arm64"],
        ),
        # ARCH only
        (
            ["--manifest", "test.yaml", "--goarch", "amd64,arm64"],
            ["linux"],
            ["amd64", "arm64"],
        ),
        # Invalid platforms
        (
            ["--manifest", "test.yaml", "--platforms", "invalid,format"],
            ["linux"],
            ["arm64"],
        ),
    ],
)
def test_main_argument_handling(args, expected_goos, expected_goarch):
    """Test main function argument handling."""
    manifest_content = """
    dist:
      name: test-collector
      description: Test OpenTelemetry Collector distribution
      version: 0.1.0
    
    exporters:
      - gomod: github.com/open-telemetry/opentelemetry-collector-contrib/exporter/fileexporter v0.122.0
    """

    with (
        patch("builtins.open", mock_open(read_data=manifest_content)),
        patch("src.main.build.build") as mock_build,
        patch("sys.argv", ["main.py"] + args),
        patch("os.makedirs"),
        patch("src.main.logger"),
    ):  # Mock logger to prevent actual logging

        mock_build.return_value = True

        # Expect SystemExit(0) for success
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

        # Verify build called with expected arguments
        mock_build.assert_called_once_with(
            manifest_content=manifest_content,
            artifact_dir="/artifacts",
            goos=expected_goos,
            goarch=expected_goarch,
            ocb_version=None,
            supervisor_version=None,
            go_version="1.24.1",
            parallelism=14,
        )


@pytest.mark.unit
@pytest.mark.parametrize(
    "error,expected_message,expected_exit_code",
    [
        (FileNotFoundError("test.yaml"), "File error: test.yaml", 1),
        (PermissionError("test.yaml"), "File error: test.yaml", 1),
        (ValueError("Invalid manifest"), "Build failed: Invalid manifest", 1),
        (RuntimeError("Build error"), "Build failed: Build error", 1),
    ],
)
def test_main_error_handling(error, expected_message, expected_exit_code):
    """Test main function error handling."""
    with (
        patch("builtins.open", side_effect=error),
        patch("src.main.logger.error") as mock_error,
        patch("sys.argv", ["main.py", "--manifest", "test.yaml"]),
    ):

        # Expect SystemExit(1) for errors
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == expected_exit_code
        mock_error.assert_called_once_with(expected_message)
