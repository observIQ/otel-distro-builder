"""Command-line interface for the OTel Distro Builder."""

import argparse
import logging
import sys

import build
from logger import BuildLogger, get_logger

logger: BuildLogger = get_logger(__name__)


def main() -> None:
    """
    Main entry point for the OTel Hub Builder Node.
    Handles command-line arguments, builds and packages the collector, and logs performance metrics.
    """
    parser = argparse.ArgumentParser(
        description="Build and package a custom OpenTelemetry Collector Distribution."
    )
    parser.add_argument(
        "--manifest", type=str, required=True, help="Path to the manifest file"
    )
    parser.add_argument(
        "--artifacts", type=str, help="Directory to copy final artifacts to (optional)"
    )
    parser.add_argument(
        "--goos",
        type=str,
        default="linux",
        help="Comma-separated list of target operating systems (overrides manifest)",
    )
    parser.add_argument(
        "--goarch",
        type=str,
        default="arm64",
        help="Comma-separated list of target architectures (overrides manifest)",
    )
    parser.add_argument(
        "--ocb-version",
        type=str,
        default="0.121.0",
        help="Version of OpenTelemetry Collector Builder to use",
    )
    parser.add_argument(
        "--supervisor-version",
        type=str,
        default="0.122.0",
        help="Version of OpenTelemetry Collector Supervisor to use",
    )
    parser.add_argument(
        "--go-version",
        type=str,
        default="1.24.1",
        help="Version of Go to use for building",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    args = parser.parse_args()

    build_logger: BuildLogger = get_logger(__name__)

    if args.debug:
        build_logger.logger.setLevel(logging.DEBUG)
    elif args.verbose:
        build_logger.logger.setLevel(logging.INFO)
    else:
        build_logger.logger.setLevel(logging.WARNING)

    try:
        # Read manifest file
        logger.section("Reading Manifest")
        with open(args.manifest, "r", encoding="utf-8") as f:
            manifest_content = f.read()
        logger.success(f"Manifest read from {args.manifest}")

        # Build the collector
        success = build.build(
            manifest_content=manifest_content,
            artifact_dir=args.artifacts,
            goos=args.goos.split(","),
            goarch=args.goarch.split(","),
            ocb_version=args.ocb_version,
            supervisor_version=args.supervisor_version,
            go_version=args.go_version,
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
