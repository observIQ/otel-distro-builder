"""Command-line interface for the OTel Distro Builder."""

import argparse
import logging
import sys

from . import build
from .logger import BuildLogger, get_logger
from .platforms import resolve_platforms

logger: BuildLogger = get_logger(__name__)

# Fixed container artifacts directory
CONTAINER_ARTIFACTS_DIR = "/artifacts"


def main() -> None:
    """
    Main entry point for the OpenTelemetry Distribution Builder.
    Handles command-line arguments, builds and packages the collector, and logs
    performance metrics.
    """
    parser = argparse.ArgumentParser(
        description="Build and package a custom OpenTelemetry Collector Distribution."
    )
    parser.add_argument(
        "--manifest", type=str, required=True, help="Path to the manifest file"
    )
    parser.add_argument(
        "--artifacts",
        type=str,
        help=f"Directory to copy final artifacts to (default: {CONTAINER_ARTIFACTS_DIR})",
    )
    parser.add_argument(
        "--platforms",
        type=str,
        help="Comma-separated list of platforms in GOOS/GOARCH format (e.g. linux/amd64,linux/arm64)",
    )
    parser.add_argument(
        "--goos",
        type=str,
        help="Comma-separated list of target operating systems (overrides manifest)",
    )
    parser.add_argument(
        "--goarch",
        type=str,
        help="Comma-separated list of target architectures (overrides manifest)",
    )
    parser.add_argument(
        "--ocb-version",
        type=str,
        help="Version of OpenTelemetry Collector Builder to use (detected from manifest if not provided)",
    )
    parser.add_argument(
        "--supervisor-version",
        type=str,
        help="Version of OpenTelemetry Collector Supervisor to use (detected from manifest if not provided)",
    )
    parser.add_argument(
        "--go-version",
        type=str,
        default="1.24.1",
        help="Version of Go to use for building",
    )
    parser.add_argument(
        "--parallelism",
        type=int,
        default=4,
        help="Number of parallel builds to run (default: 4)",
    )
    args = parser.parse_args()

    # Set log level to INFO
    logging.getLogger().setLevel(logging.INFO)

    try:
        # Read manifest file
        logger.section("Reading Manifest")
        with open(args.manifest, "r", encoding="utf-8") as f:
            manifest_content = f.read()
        logger.success(f"Manifest read from {args.manifest}")

        # Resolve target platforms
        goos, goarch = resolve_platforms(
            platforms=args.platforms, goos=args.goos, goarch=args.goarch
        )

        # Build the collector
        success = build.build(
            manifest_content=manifest_content,
            artifact_dir=args.artifacts or CONTAINER_ARTIFACTS_DIR,
            goos=goos,
            goarch=goarch,
            ocb_version=args.ocb_version,
            supervisor_version=args.supervisor_version,
            go_version=args.go_version,
            parallelism=args.parallelism,
        )

        sys.exit(0 if success else 1)

    except (FileNotFoundError, PermissionError) as e:
        logger.error(f"File error: {str(e)}")
        sys.exit(1)
    except (ValueError, RuntimeError) as e:
        logger.error(f"Build failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
