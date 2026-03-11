"""Tests for the main module."""

import os
from unittest.mock import mock_open, patch

import pytest
from src.main import _get_version, main


@pytest.mark.unit
@pytest.mark.parametrize(
    "args,expected_goos,expected_goarch,expected_pairs",
    [
        # Default case - just manifest
        (["--manifest", "test.yaml"], ["linux"], ["amd64"], [("linux", "amd64")]),
        # Platforms only - preserves exact pairs (no cross-product)
        (
            ["--manifest", "test.yaml", "--platforms", "linux/amd64,darwin/arm64"],
            ["darwin", "linux"],
            ["amd64", "arm64"],
            [("linux", "amd64"), ("darwin", "arm64")],
        ),
        # OS and ARCH override platforms (cross-product)
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
            [("windows", "arm64"), ("windows", "amd64")],
        ),
        # OS only (cross-product with default arch)
        (
            ["--manifest", "test.yaml", "--goos", "windows,darwin"],
            ["windows", "darwin"],
            ["amd64"],
            [("windows", "amd64"), ("darwin", "amd64")],
        ),
        # ARCH only (cross-product with default os)
        (
            ["--manifest", "test.yaml", "--goarch", "amd64,arm64"],
            ["linux"],
            ["amd64", "arm64"],
            [("linux", "amd64"), ("linux", "arm64")],
        ),
        # Invalid platforms
        (
            ["--manifest", "test.yaml", "--platforms", "invalid,format"],
            ["linux"],
            ["amd64"],
            [("linux", "amd64")],
        ),
    ],
)
def test_main_argument_handling(args, expected_goos, expected_goarch, expected_pairs):
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
        patch("src.platforms.get_host_platform", return_value=("linux", "amd64")),
        patch("os.getcwd", return_value="/tmp"),
    ):

        mock_build.return_value = True

        # Expect SystemExit(0) for success
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

        # Verify build called with expected arguments (artifact_dir = host default)
        mock_build.assert_called_once_with(
            manifest_content=manifest_content,
            artifact_dir="/tmp/artifacts",
            goos=expected_goos,
            goarch=expected_goarch,
            platform_pairs=expected_pairs,
            ocb_version=None,
            supervisor_version=None,
            go_version=None,
            parallelism=4,
            keep_build_dir=False,
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


@pytest.mark.unit
@pytest.mark.parametrize("flag", ["--version", "-V"])
def test_version_flag(flag, capsys):
    """--version and -V print the version and exit 0."""
    with patch("sys.argv", ["main.py", flag]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    output = capsys.readouterr().out.strip()
    # Should be a non-empty version string (e.g. "1.0.0")
    assert output
    assert "." in output


@pytest.mark.unit
def test_from_config_generate_only_writes_manifest_to_artifacts():
    """--from-config --generate-only writes manifest to artifact_dir/manifest.yaml."""
    fake_manifest = "dist:\n  name: test\n"

    with (
        patch(
            "sys.argv",
            [
                "main.py",
                "--from-config",
                "config.yaml",
                "--generate-only",
                "--artifacts",
                "/tmp/test-artifacts",
            ],
        ),
        patch("src.main.generate_from_config", return_value=fake_manifest) as mock_gen,
        patch("src.main.logger"),
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

        mock_gen.assert_called_once()
        call_kwargs = mock_gen.call_args
        assert call_kwargs.kwargs["output_manifest"] == os.path.join(
            "/tmp/test-artifacts", "manifest.yaml"
        )


@pytest.mark.unit
def test_from_config_generate_only_default_artifacts():
    """--from-config --generate-only without --artifacts uses default artifacts dir."""
    fake_manifest = "dist:\n  name: test\n"

    with (
        patch(
            "sys.argv",
            ["main.py", "--from-config", "config.yaml", "--generate-only"],
        ),
        patch("src.main.generate_from_config", return_value=fake_manifest) as mock_gen,
        patch("src.main.logger"),
        patch("os.getcwd", return_value="/home/user/project"),
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

        mock_gen.assert_called_once()
        call_kwargs = mock_gen.call_args
        assert call_kwargs.kwargs["output_manifest"] == os.path.join(
            "/home/user/project", "artifacts", "manifest.yaml"
        )


@pytest.mark.unit
def test_get_version_installed():
    """_get_version returns metadata version when the package is installed."""
    with patch("importlib.metadata.version", return_value="2.3.4"):
        assert _get_version() == "2.3.4"


@pytest.mark.unit
def test_get_version_fallback():
    """_get_version returns fallback when package metadata is unavailable."""
    with patch("importlib.metadata.version", side_effect=ImportError):
        assert _get_version() == "1.0.0"
