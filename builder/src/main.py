"""Command-line interface for the OTel Distro Builder."""

import argparse
import logging
import os
import sys
from typing import Optional

import yaml

from . import build
from .logger import BuildLogger, get_logger
from .platforms import resolve_platforms

logger: BuildLogger = get_logger(__name__)

# Fixed container artifacts directory
CONTAINER_ARTIFACTS_DIR = "/artifacts"


def get_latest_otel_version() -> str:
    """Get the latest OpenTelemetry version from versions.yaml.

    Returns:
        The latest version string, or a fallback default if not found.
    """
    fallback_version = "0.144.0"

    try:
        versions_path = os.path.join(
            os.path.dirname(__file__), "..", "versions.yaml"
        )
        with open(versions_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if data and "versions" in data:
            # Get the first (latest) version key
            versions = list(data["versions"].keys())
            if versions:
                return versions[0]
    except (FileNotFoundError, yaml.YAMLError, KeyError):
        pass

    return fallback_version


# Get default version at module load time
DEFAULT_OTEL_VERSION = get_latest_otel_version()


def generate_from_config(
    config_path: str,
    output_manifest: Optional[str] = None,
    otel_version: Optional[str] = None,
    dist_name: str = "otelcol-custom",
    dist_module: str = "github.com/custom/otelcol-distribution",
    dist_version: str = "1.0.0",
    include_bindplane: bool = True,
) -> str:
    """Generate a manifest from a collector config file.

    Args:
        config_path: Path to the collector config.yaml file
        output_manifest: Optional path to write the manifest to
        otel_version: Target OpenTelemetry version (defaults to latest)
        dist_name: Name of the distribution
        dist_module: Go module path for the distribution
        dist_version: Version of the distribution
        include_bindplane: Whether to include Bindplane collector components (default: True)

    Returns:
        The generated manifest content
    """
    # pylint: disable=import-outside-toplevel
    from .manifest_generator import generate_manifest_from_config

    # Use default version if not specified
    if otel_version is None:
        otel_version = DEFAULT_OTEL_VERSION

    logger.section("Config to Manifest Generation")
    logger.info(f"Reading config from: {config_path}")
    logger.info(f"Target OTel version: {otel_version}")
    logger.info(f"Include Bindplane collector components: {include_bindplane}")

    result = generate_manifest_from_config(
        config_path=config_path,
        output_path=output_manifest,
        module=dist_module,
        name=dist_name,
        version=dist_version,
        otel_version=otel_version,
        include_bindplane=include_bindplane,
    )

    # Log any warnings
    if result.warnings:
        logger.section("Warnings")
        for warning in result.warnings:
            logger.warning(warning)

    return result.content


def main() -> None:
    """
    Main entry point for the OpenTelemetry Distribution Builder.
    Handles command-line arguments, builds and packages the collector, and logs
    performance metrics.
    """
    parser = argparse.ArgumentParser(
        description="Build and package a custom OpenTelemetry Collector Distribution."
    )

    # Manifest source - either direct manifest or generate from config
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--manifest", type=str, help="Path to the manifest file"
    )
    source_group.add_argument(
        "--from-config",
        type=str,
        metavar="CONFIG_PATH",
        help="Generate manifest from an existing collector config.yaml file",
    )

    # Config-to-manifest specific options
    parser.add_argument(
        "--output-manifest",
        type=str,
        help="Path to write the generated manifest (only with --from-config)",
    )
    parser.add_argument(
        "--generate-only",
        action="store_true",
        help="Only generate the manifest, don't build (only with --from-config)",
    )
    parser.add_argument(
        "--otel-version",
        type=str,
        default=DEFAULT_OTEL_VERSION,
        help=f"Target OpenTelemetry version for generated manifest (default: {DEFAULT_OTEL_VERSION})",
    )
    parser.add_argument(
        "--dist-name",
        type=str,
        default="otelcol-custom",
        help="Name of the distribution (default: otelcol-custom)",
    )
    parser.add_argument(
        "--dist-module",
        type=str,
        default="github.com/custom/otelcol-distribution",
        help="Go module path for the distribution",
    )
    parser.add_argument(
        "--dist-version",
        type=str,
        default="1.0.0",
        help="Version of the distribution (default: 1.0.0)",
    )
    parser.add_argument(
        "--no-bindplane",
        action="store_true",
        help="Exclude Bindplane/observIQ components from the generated manifest",
    )

    # Build options
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
        # Handle --from-config mode
        if args.from_config:
            manifest_content = generate_from_config(
                config_path=args.from_config,
                output_manifest=args.output_manifest,
                otel_version=args.otel_version,
                dist_name=args.dist_name,
                dist_module=args.dist_module,
                dist_version=args.dist_version,
                include_bindplane=not args.no_bindplane,
            )

            # If generate-only, print manifest and exit
            if args.generate_only:
                if not args.output_manifest:
                    print("\n# Generated Manifest:")
                    print(manifest_content)
                logger.success("Manifest generation complete")
                sys.exit(0)
        else:
            # Read manifest file directly
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
