"""Utility for downloading and managing OpenTelemetry Collector Contrib repository."""

import os
import shutil
import subprocess
import logger

repo_logger = logger.get_logger(__name__)

def clone_repo(output_dir, tag):
    """Clone the OpenTelemetry Collector Contrib repository at a specific tag."""
    repo_url = "https://github.com/open-telemetry/opentelemetry-collector-contrib.git"
    repo_path = os.path.join(output_dir, "collector-contrib")

    # Check if directory already exists
    if os.path.exists(repo_path):
        repo_logger.info(f"Removing existing repository at: {repo_path}")
        shutil.rmtree(repo_path)

    repo_logger.section("Repository Download")
    repo_logger.info("Clone Details:", indent=1)
    repo_logger.info(f"Repository: {repo_url}", indent=2)
    repo_logger.info(f"Tag: {tag}", indent=2)
    repo_logger.info(f"Output: {repo_path}", indent=2)

    try:
        # Clone the repository
        subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", "v" + tag, repo_url, repo_path],
            check=True,
            capture_output=True,
            text=True
        )
        repo_logger.success(f"Successfully cloned repository at tag: {tag}")
   
        # Verify opampsupervisor folder exists
        opamp_path = os.path.join(repo_path, "cmd", "opampsupervisor")
        if not os.path.exists(opamp_path):
            raise RuntimeError(f"opampsupervisor folder not found at: {opamp_path}")

        repo_logger.success("Found opampsupervisor folder")
        return opamp_path

    except subprocess.CalledProcessError as e:
        repo_logger.error(f"Git operation failed: {e.stderr}")
        raise
    except Exception as e:
        repo_logger.error(f"Failed to process repository: {str(e)}")
        raise
