"""Integration tests for the OTel builder system."""

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

# Expected artifacts for each build type
LINUX_ARM64_ARTIFACTS = [
    # collector-only artifacts
    "otelcol-contrib_otelcol_v0.122.1_linux_arm64.rpm",
    "otelcol-contrib_otelcol_v0.122.1_linux_arm64.rpm.sbom.json",
    "otelcol-contrib_otelcol_v0.122.1_linux_arm64.apk",
    "otelcol-contrib_otelcol_v0.122.1_linux_arm64.apk.sbom.json",
    "otelcol-contrib_otelcol_v0.122.1_linux_arm64.tar.gz",
    "otelcol-contrib_otelcol_v0.122.1_linux_arm64.tar.gz.sbom.json",
    "otelcol-contrib_otelcol_v0.122.1_linux_arm64.deb",
    "otelcol-contrib_otelcol_v0.122.1_linux_arm64.deb.sbom.json",
    # collector + supervisor artifacts
    "otelcol-contrib_v0.122.1_linux_arm64.rpm",
    "otelcol-contrib_v0.122.1_linux_arm64.rpm.sbom.json",
    "otelcol-contrib_v0.122.1_linux_arm64.apk",
    "otelcol-contrib_v0.122.1_linux_arm64.apk.sbom.json",
    "otelcol-contrib_v0.122.1_linux_arm64.tar.gz",
    "otelcol-contrib_v0.122.1_linux_arm64.tar.gz.sbom.json",
    "otelcol-contrib_v0.122.1_linux_arm64.deb",
    "otelcol-contrib_v0.122.1_linux_arm64.deb.sbom.json",
    # checksums (always present)
    "otelcol-contrib_checksums.txt",
]

LINUX_AMD64_ARTIFACTS = [
    # collector-only artifacts
    "otelcol-contrib_otelcol_v0.122.1_linux_amd64.rpm",
    "otelcol-contrib_otelcol_v0.122.1_linux_amd64.rpm.sbom.json",
    "otelcol-contrib_otelcol_v0.122.1_linux_amd64.apk",
    "otelcol-contrib_otelcol_v0.122.1_linux_amd64.apk.sbom.json",
    "otelcol-contrib_otelcol_v0.122.1_linux_amd64.tar.gz",
    "otelcol-contrib_otelcol_v0.122.1_linux_amd64.tar.gz.sbom.json",
    "otelcol-contrib_otelcol_v0.122.1_linux_amd64.deb",
    "otelcol-contrib_otelcol_v0.122.1_linux_amd64.deb.sbom.json",
    # collector + supervisor artifacts
    "otelcol-contrib_v0.122.1_linux_amd64.rpm",
    "otelcol-contrib_v0.122.1_linux_amd64.rpm.sbom.json",
    "otelcol-contrib_v0.122.1_linux_amd64.apk",
    "otelcol-contrib_v0.122.1_linux_amd64.apk.sbom.json",
    "otelcol-contrib_v0.122.1_linux_amd64.tar.gz",
    "otelcol-contrib_v0.122.1_linux_amd64.tar.gz.sbom.json",
    "otelcol-contrib_v0.122.1_linux_amd64.deb",
    "otelcol-contrib_v0.122.1_linux_amd64.deb.sbom.json",
    # checksums (always present)
    "otelcol-contrib_checksums.txt",
]


def get_current_platform() -> str:
    """Get the current platform identifier."""
    if sys.platform.startswith("linux"):
        return "linux"
    if sys.platform.startswith("darwin"):
        return "darwin"
    if sys.platform.startswith("win"):
        return "windows"
    return sys.platform


def verify_build_artifacts(artifact_path: Path, expected_artifacts: list[str]) -> None:
    """Verify all expected build artifacts exist."""
    for pattern in expected_artifacts:
        matches = list(artifact_path.glob(pattern))
        assert len(matches) > 0, f"Expected artifact {pattern} not found"

    # Check for raw binary - support both underscore and hyphen variants
    binary_dirs = (
        list(artifact_path.glob("otelcol_*"))
        + list(artifact_path.glob("otelcol-*"))
        + list(artifact_path.glob("otelcol-contrib"))  # Exact match without suffix
    )
    assert len(binary_dirs) > 0, "No binary directories found"
    for binary_dir in binary_dirs:
        if binary_dir.is_dir():  # Skip if it's a package file
            assert any(binary_dir.iterdir()), f"Binary directory {binary_dir} is empty"


def remove_readonly(func, path, _exc):
    """Handle permission errors during deletion by recursively changing permissions"""
    try:
        # Recursively change permissions for directories
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                for d in dirs:
                    dirpath = os.path.join(root, d)
                    os.chmod(dirpath, 0o666)  # rw permissions
                for f in files:
                    filepath = os.path.join(root, f)
                    # Remove execute bit first
                    os.chmod(filepath, 0o666)  # rw permissions

        # Change permissions of the path itself
        if os.path.isfile(path):
            os.chmod(path, 0o666)  # rw permissions
        else:
            os.chmod(path, 0o777)  # rwx for directories
        func(path)
    except (OSError, PermissionError) as e:
        print(f"Error while removing {path}: {e}")


def run_build_test(
    manifest_name: str, expected_artifacts: list[str], env_inputs: dict | None = None
) -> None:
    """Run a build test for a specific manifest file.

    Args:
        manifest_name: Name of the manifest file to use
        expected_artifacts: List of artifacts to verify
        env_inputs: Optional dict of environment variables (for GitHub Actions style inputs)
    """
    manifest_path = Path(__file__).parent / "manifests" / manifest_name
    assert manifest_path.exists(), f"Manifest file not found: {manifest_name}"

    # Create artifacts directory in the workspace root
    workspace_root = Path(__file__).parent.parent.parent
    artifact_dir = workspace_root / "artifacts"
    if artifact_dir.exists():
        shutil.rmtree(artifact_dir, onexc=remove_readonly)
    artifact_dir.mkdir(exist_ok=True)

    try:
        # Build the Docker image
        builder_dir = workspace_root / "builder"
        image_name = "otel-distro-builder"
        build_result = subprocess.run(
            ["docker", "build", "-t", image_name, "."],
            cwd=builder_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        if build_result.returncode != 0:
            print("\nDocker Build Output:")
            print(build_result.stdout)
            print("\nDocker Build Errors:")
            print(build_result.stderr)
            raise RuntimeError("Docker build failed")

        # Run the container with fixed mount points like run_local_build.sh
        cmd = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{manifest_path}:/manifest.yaml:ro",
            "-v",
            f"{artifact_dir}:/artifacts",
        ]

        # Add any environment variables if provided
        if env_inputs:
            for k, v in env_inputs.items():
                cmd.extend(["-e", f"{k}={v}"])

        cmd.append(image_name)
        cmd.extend(["--manifest", "/manifest.yaml"])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        print("\nBuild Output:")
        print(result.stdout)
        if result.stderr:
            print("\nBuild Errors:")
            print(result.stderr)

        # Debug: Show contents of artifact directory
        print("\nArtifact Directory Contents:")
        if artifact_dir.exists():
            print(f"Directory exists: {artifact_dir}")
            print("Files:")
            for item in artifact_dir.rglob("*"):
                if item.is_file():
                    print(
                        f"  {item.relative_to(artifact_dir)} ({item.stat().st_size} bytes)"
                    )
                else:
                    print(f"  {item.relative_to(artifact_dir)}/")
        else:
            print(f"Directory does not exist: {artifact_dir}")

        # Debug: Check directory permissions
        print("\nDirectory Permissions:")
        try:
            stat = os.stat(artifact_dir)
            print(f"Mode: {stat.st_mode:o}")
            print(f"Owner: {stat.st_uid}")
            print(f"Group: {stat.st_gid}")
        except (OSError, PermissionError) as e:
            print(f"Error getting permissions: {e}")

        assert (
            result.returncode == 0
        ), f"Build failed with return code {result.returncode}"
        verify_build_artifacts(artifact_dir, expected_artifacts)

        # After running the binary
        time.sleep(1)  # Give the OS time to release file handles
    finally:
        # Clean up the artifacts directory after the test
        if artifact_dir.exists():
            try:
                shutil.rmtree(artifact_dir, onexc=remove_readonly)
            except (OSError, PermissionError) as e:
                print(f"Failed to clean up {artifact_dir}: {e}")


@pytest.mark.build
def test_simple_build() -> None:
    """Test building a simple distribution with minimal components."""
    run_build_test("simple.yaml", LINUX_ARM64_ARTIFACTS)


@pytest.mark.build
def test_simple_build_env() -> None:
    """Test building using GitHub Actions style environment variables.

    This test simulates how the GitHub Action would be used by a customer,
    using the same environment variables defined in action.yml.
    """
    env_inputs = {
        "INPUT_MANIFEST": "/manifest.yaml",  # Use fixed path in container
        "INPUT_ARTIFACT_DIR": "/artifacts",  # Use fixed path in container
        "INPUT_OS": "linux",
        "INPUT_ARCH": "amd64",
    }
    run_build_test("simple.yaml", LINUX_AMD64_ARTIFACTS, env_inputs=env_inputs)


@pytest.mark.release
def test_contrib_build() -> None:
    """Test building a full contrib distribution with all components."""
    run_build_test("contrib.yaml", LINUX_ARM64_ARTIFACTS)
