"""Integration tests for the OTel builder system."""

import os
import shutil
import subprocess
import time
from pathlib import Path
import pytest


def get_manifest_files():
    """Get all manifest files from the manifests directory."""
    manifest_dir = Path(__file__).parent / "manifests"
    return list(manifest_dir.glob("*.y*ml"))


def verify_build_artifacts(artifact_path: Path) -> None:
    """Verify all expected build artifacts exist."""
    # Verify expected files exist
    assert (artifact_path / "metadata.json").exists(), "metadata.json not found"
    assert (artifact_path / "artifacts.json").exists(), "artifacts.json not found"
    assert (artifact_path / "config.yaml").exists(), "config.yaml not found"

    # Check for binary packages
    packages = (
        list(artifact_path.glob("*.deb"))
        + list(artifact_path.glob("*.rpm"))
        + list(artifact_path.glob("*.apk"))
        + list(artifact_path.glob("*.tar.gz"))
    )
    assert len(packages) > 0, "No package files found"

    # Check for SBOM files
    sbom_files = list(artifact_path.glob("*.sbom.json"))
    assert len(sbom_files) > 0, "No SBOM files found"

    # Check for checksums file
    checksums = list(artifact_path.glob("*checksums.txt"))
    assert len(checksums) == 1, "Checksums file not found"

    # Check for raw binary
    binary_dirs = list(artifact_path.glob("otelcol_*")) + list(
        artifact_path.glob("otelcol-contrib_*")
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


@pytest.mark.parametrize("manifest_path", get_manifest_files())
def test_build_distribution(manifest_path: Path):
    """Test building a distribution from a manifest file."""
    # Create artifacts directory in the current test directory
    artifact_dir = Path(__file__).parent / "artifacts"
    if artifact_dir.exists():
        shutil.rmtree(artifact_dir, onexc=remove_readonly)
    artifact_dir.mkdir(exist_ok=True)

    try:
        # Run the build using run_local_build.sh
        script_path = Path(__file__).parent.parent / "run_local_build.sh"
        cmd = [str(script_path), "-m", str(manifest_path), "-o", str(artifact_dir)]

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        print("\nBuild Output:")
        print(result.stdout)
        if result.stderr:
            print("\nBuild Errors:")
            print(result.stderr)

        # Debug: Show contents of artifact directory
        print("\nArtifact Directory Contents:")
        artifact_path = Path(artifact_dir)
        if artifact_path.exists():
            print(f"Directory exists: {artifact_path}")
            print("Files:")
            for item in artifact_path.rglob("*"):
                if item.is_file():
                    print(
                        f"  {item.relative_to(artifact_path)} ({item.stat().st_size} bytes)"
                    )
                else:
                    print(f"  {item.relative_to(artifact_path)}/")
        else:
            print(f"Directory does not exist: {artifact_path}")

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

        verify_build_artifacts(artifact_path)

        # After running the binary
        time.sleep(1)  # Give the OS time to release file handles
    finally:
        # Clean up the artifacts directory after the test
        if artifact_dir.exists():
            try:
                shutil.rmtree(artifact_dir, onexc=remove_readonly)
            except (OSError, PermissionError) as e:
                print(f"Failed to clean up {artifact_dir}: {e}")
