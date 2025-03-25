"""Core build system for creating custom OpenTelemetry Collector distributions."""

import os
import subprocess
import shutil
import time
from typing import Optional
from dataclasses import dataclass
import yaml
import psutil
import ocb_downloader as ocb
import supervisor_downloader as supervisor
import logger


logger = logger.get_logger(__name__)

# Fixed build workspace directory
BUILD_DIR = "/build"


class BuildMetrics:
    """Tracks performance metrics for the build process."""

    def __init__(self):
        self.start_time = time.time()
        self.phase_timings = {}
        self.current_phase = None
        self.phase_start = None
        self.peak_memory = 0  # Peak memory usage in MB
        self.disk_read = 0  # Total bytes read
        self.disk_write = 0  # Total bytes written
        self.process = psutil.Process()

    def start_phase(self, name: str):
        """Start timing a build phase."""
        if name not in ["generate_sources", "build_release"]:
            return
        self.current_phase = name
        self.phase_start = time.time()

    def end_phase(self, name: str):
        """End timing a build phase."""
        if name not in ["generate_sources", "build_release"]:
            return
        if self.phase_start and name == self.current_phase:
            duration = time.time() - self.phase_start
            self.phase_timings[name] = duration
            self.current_phase = None
            self.phase_start = None

    def update_resource_usage(self):
        """Update peak resource usage metrics."""
        # Memory usage in MB
        memory = self.process.memory_info().rss / (1024 * 1024)
        self.peak_memory = max(self.peak_memory, memory)

        # Disk I/O
        io = self.process.io_counters()
        self.disk_read = io.read_bytes
        self.disk_write = io.write_bytes

    def get_total_duration(self):
        """Get total build duration in seconds."""
        return time.time() - self.start_time

    def log_summary(self):
        """Log a summary of collected metrics."""
        logger.section("Build Metrics")

        # Overall duration
        duration = self.get_total_duration()
        logger.info(f"Total Duration: {duration:.2f}s", indent=1)

        # Phase timings
        logger.info("Phase Durations:", indent=1)
        for phase, duration in self.phase_timings.items():
            logger.info(f"{phase}: {duration:.2f}s", indent=2)

        # Resource usage
        logger.info("Resource Usage:", indent=1)
        logger.info(f"Peak Memory: {self.peak_memory:.1f}MB", indent=2)
        logger.info(f"Total Disk Read: {self.disk_read / (1024*1024):.1f}MB", indent=2)
        logger.info(
            f"Total Disk Write: {self.disk_write / (1024*1024):.1f}MB", indent=2
        )


@dataclass
class BuildContext:
    """Holds all the paths and configuration for a build."""

    working_dir: str  # Root of builder project
    build_dir: str  # Main build workspace
    source_dir: str  # Generated Go files directory
    artifact_dir: str  # Build artifacts directory
    ocb_dir: str  # OCB binaries directory
    templates_dir: str  # Template files directory
    distribution: str  # Name of the distribution
    goos_yaml: str  # Target OS in YAML format
    goarch_yaml: str  # Target architecture in YAML format
    ocb_version: str  # Version of OCB to use
    supervisor_version: str  # Version of supervisor to use
    go_version: str  # Version of Go to use
    manifest_path: str  # Path to the manifest file

    @classmethod
    # pylint: disable=too-many-positional-arguments
    def create(
        cls,
        manifest_content: str,
        goos: Optional[list[str]] = None,
        goarch: Optional[list[str]] = None,
        ocb_version: Optional[str] = "0.121.0",
        supervisor_version: Optional[str] = "0.122.0",
        go_version: Optional[str] = "1.24.1",
    ):
        """Create a BuildContext from manifest content."""
        goos = goos or ["linux"]
        goarch = goarch or ["arm64"]
        # Parse manifest
        manifest = yaml.safe_load(manifest_content)

        # Extract required fields
        distribution = manifest["dist"]["name"]
        # Format as YAML array
        goos_yaml = "[" + ", ".join(goos) + "]"
        goarch_yaml = "[" + ", ".join(goarch) + "]"

        # Set up build paths
        working_dir = os.path.abspath(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        )
        source_dir = os.path.join(BUILD_DIR, "_build")
        artifact_dir = os.path.join(BUILD_DIR, "dist")
        ocb_dir = os.path.join(working_dir, "ocb")
        templates_dir = os.path.join(working_dir, "builder", "templates")
        manifest_path = os.path.join(BUILD_DIR, "manifest.yaml")

        # Update manifest output_path to point to source_dir
        manifest["dist"]["output_path"] = "_build"

        # Write prepared manifest
        os.makedirs(BUILD_DIR, exist_ok=True)
        with open(manifest_path, "w", encoding="utf-8") as f:
            yaml.dump(manifest, f)
        logger.success("Manifest prepared successfully")

        # Create instance
        return cls(
            working_dir=working_dir,
            build_dir=BUILD_DIR,
            source_dir=source_dir,
            artifact_dir=artifact_dir,
            ocb_dir=ocb_dir,
            templates_dir=templates_dir,
            distribution=distribution,
            goos_yaml=goos_yaml,
            goarch_yaml=goarch_yaml,
            ocb_version=ocb_version,
            supervisor_version=supervisor_version,
            go_version=go_version,
            manifest_path=manifest_path,
        )


def validate_environment():
    """Validate that required tools are available."""
    logger.section("Environment Validation")

    go_binary = shutil.which("go")
    if not go_binary:
        logger.error(
            "Go binary not found. Please ensure Go is installed and in your PATH."
        )
        raise RuntimeError("Go binary not found")

    go_version = subprocess.check_output(["go", "version"], text=True).strip()
    logger.success(f"Go found: {go_version}")


def create_directories(ctx: BuildContext):
    """Create all necessary directories for the build."""
    logger.section("Directory Setup")
    for directory in [ctx.build_dir, ctx.source_dir, ctx.artifact_dir, ctx.ocb_dir, os.path.join(ctx.build_dir, "_contrib")]:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}", indent=1)
    logger.success("All directories created")


def write_file(path: str, content: str, mode="w"):
    """Write content to a file."""
    with open(path, mode, encoding="utf-8") as file:
        file.write(content)


def generate_sources(ctx: BuildContext) -> None:
    """Generate source files using OCB."""

    # Download OCB
    ocb_path = ocb.download_ocb(ctx.ocb_version, ctx.ocb_dir)
    logger.success(f"OCB {ctx.ocb_version} ready")

    # Run OCB
    logger.section("Source Generation")

    cmd = f"{ocb_path} --skip-compilation=true --config {ctx.manifest_path}"
    logger.info("Running OCB builder:", indent=1)
    logger.command(cmd)

    result = subprocess.run(
        [ocb_path, "--skip-compilation=true", "--config", ctx.manifest_path],
        cwd=ctx.build_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    build_log = result.stdout.decode()

    # Write build log
    log_path = os.path.join(ctx.source_dir, "build.log")
    write_file(log_path, build_log)
    logger.info(f"Build log written to: {log_path}", indent=1)

    if result.returncode != 0:
        logger.error(f"Failed to generate source files for '{ctx.distribution}'")
        logger.info("Build Log:", indent=1)
        logger.info(build_log, indent=2)
        raise RuntimeError(f"Build failed: {build_log}")

    logger.success(f"Source files generated for '{ctx.distribution}'")

def download_supervisor(ctx: BuildContext):
    # Download supervisor
    supervisor.download_supervisor(os.path.join(ctx.build_dir, "_contrib"), ctx.supervisor_version)
    logger.success("Supervisor binaries downloaded")

def process_templates(ctx: BuildContext):
    """Process and copy template files."""
    logger.section("Template Processing")

    templates = [
        (".goreleaser.yaml", ".goreleaser.yaml"),
        ("collector_config.yaml", "collector_config.yaml"),
        ("Dockerfile", "Dockerfile"),
        ("postinstall.sh", "postinstall.sh"),
        ("preinstall.sh", "preinstall.sh"),
        ("preremove.sh", "preremove.sh"),
        ("supervisor_config.yaml", "supervisor_config.yaml"),
        ("template.conf", f"{ctx.distribution}.conf"),
        ("template.service", f"{ctx.distribution}.service"),
        ("template_otelcol.conf", f"{ctx.distribution}_otelcol.conf"),
        ("template_otelcol.service", f"{ctx.distribution}_otelcol.service"),
    ]

    # Copy and update template files
    for template, dest in templates:
        template_path = os.path.join(ctx.templates_dir, template)
        dest_path = os.path.join(ctx.build_dir, dest)
        with open(template_path, "r", encoding="utf-8") as src_file:
            content = src_file.read()
            content = content.replace("__DISTRIBUTION__", ctx.distribution)
            content = content.replace("__GOOS__", ctx.goos_yaml)
            content = content.replace("__GOARCH__", ctx.goarch_yaml)
            write_file(dest_path, content)
        logger.info(f"Processed: {template} → {dest}", indent=1)

    # Make script files executable
    for script in ["postinstall.sh", "preinstall.sh", "preremove.sh"]:
        os.chmod(os.path.join(ctx.build_dir, script), 0o755)
        logger.info(f"Made executable: {script}", indent=1)

    logger.success("All templates processed")

def move_files(ctx: BuildContext):
    """Move files to the build directory."""
    logger.section("Moving Files")

    # Move additional files
    files = [
        "LICENSE",
        "VERSION",
    ]
    for file in files:
        src = os.path.join(ctx.working_dir, file)
        dst = os.path.join(ctx.build_dir, file)
        shutil.copy2(src, dst)
        logger.info(f"Moved: {file}", indent=1)

def release_preparation(ctx: BuildContext, metrics: BuildMetrics):
    """Prepare the release."""
    logger.section("Release Preparation")

    # Generate sources
    metrics.start_phase("generate_sources")
    generate_sources(ctx)
    metrics.update_resource_usage()
    metrics.end_phase("generate_sources")

    # Retrieve supervisor source
    metrics.start_phase("download_supervisor")
    download_supervisor(ctx)
    metrics.update_resource_usage()
    metrics.end_phase("download_supervisor")

    # Process templates
    metrics.start_phase("process_templates")
    process_templates(ctx)
    metrics.update_resource_usage()
    metrics.end_phase("process_templates")

    # Move additional files to build directory
    metrics.start_phase("move_files")
    move_files(ctx)
    metrics.update_resource_usage()
    metrics.end_phase("move_files")

def build_release(ctx: BuildContext) -> bool:
    """Build the final release using goreleaser."""
    logger.section("Release Building")
    logger.info(f"Building release for {ctx.distribution} with goreleaser")

    cmd = "goreleaser --snapshot --clean"
    logger.command(cmd)

    result = subprocess.run(
        ["goreleaser", "--snapshot", "--clean"],
        cwd=ctx.build_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )  # Ensure output is decoded as text

    # Always show goreleaser output
    if result.stdout:
        logger.info("Goreleaser Output:", indent=1)
        for line in result.stdout.splitlines():
            if line.strip():  # Skip empty lines
                logger.info(line, indent=2)

    if result.returncode != 0:
        logger.error("Goreleaser build failed")
        return False

    logger.success("Release built successfully")
    return True


def copy_artifacts(ctx: BuildContext, artifact_dir: str) -> None:
    """Copy build artifacts to the specified directory."""
    logger.section("Copying Artifacts")

    if not os.path.exists(ctx.artifact_dir):
        logger.error(f"Build artifacts directory not found: {ctx.artifact_dir}")
        raise RuntimeError("Build artifacts not found")

    os.makedirs(artifact_dir, exist_ok=True)

    # Copy all files from dist directory
    for item in os.listdir(ctx.artifact_dir):
        src = os.path.join(ctx.artifact_dir, item)
        dst = os.path.join(artifact_dir, item)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
            logger.info(f"Copied: {item}", indent=1)
        elif os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
            logger.info(f"Copied directory: {item}", indent=1)

    logger.success(f"Artifacts copied to: {artifact_dir}")


# pylint: disable=too-many-positional-arguments
def build(
    manifest_content: str,
    artifact_dir: Optional[str] = None,
    goos: Optional[list[str]] = None,
    goarch: Optional[list[str]] = None,
    ocb_version: Optional[str] = "0.121.0",
    supervisor_version: Optional[str] = "0.122.0",
    go_version: Optional[str] = "1.24.1",
) -> bool:
    """Build an OpenTelemetry Collector distribution.

    Args:
        manifest_content: Content of the manifest file
        artifact_dir: Optional directory to copy artifacts to after build
        goos: Comma-separated list of target operating systems
        goarch: Comma-separated list of target architectures
        ocb_version: Version of OpenTelemetry Collector Builder to use
        supervisor_version: Version of OpenTelemetry Collector Supervisor to use
        go_version: Version of Go to use for building

    Returns:
        bool: True if build succeeded, False otherwise
    """
    # Initialize metrics tracking
    metrics = BuildMetrics()
    metrics.start_phase("setup")

    logger.section("Build Configuration")

    # Create build context
    ctx = BuildContext.create(manifest_content, goos, goarch, ocb_version, supervisor_version, go_version)

    # Log build information
    logger.info("Build Details:", indent=1)
    logger.info(f"Working Directory: {ctx.working_dir}", indent=2)
    logger.info(f"Build Directory: {ctx.build_dir}", indent=2)
    logger.info(f"Source Directory: {ctx.source_dir}", indent=2)
    logger.info(f"Artifact Directory: {ctx.artifact_dir}", indent=2)
    if artifact_dir:
        logger.info(f"Final Artifacts Will Be Copied To: {artifact_dir}", indent=2)
    logger.info(f"OCB Directory: {ctx.ocb_dir}", indent=2)
    logger.info(f"OCB Version: {ctx.ocb_version}", indent=2)
    logger.info(f"Supervisor Version: {ctx.supervisor_version}", indent=2)
    logger.info(f"Go Version: {ctx.go_version}", indent=2)

    metrics.end_phase("setup")

    try:
        # Validate environment
        metrics.start_phase("validate")
        validate_environment()
        metrics.end_phase("validate")

        # Create directories
        metrics.start_phase("create_dirs")
        create_directories(ctx)
        metrics.end_phase("create_dirs")

        # Release preparation
        metrics.start_phase("release_preparation")
        release_preparation(ctx, metrics)
        metrics.update_resource_usage()
        metrics.end_phase("release_preparation")

        # Build release
        metrics.start_phase("build_release")
        success = build_release(ctx)
        metrics.update_resource_usage()
        metrics.end_phase("build_release")

        if success:
            logger.section("Build Summary")
            logger.success(f"Build completed successfully for {ctx.distribution}")

            # Copy artifacts if a destination was specified
            if artifact_dir:
                metrics.start_phase("copy_artifacts")
                copy_artifacts(ctx, artifact_dir)
                metrics.update_resource_usage()
                metrics.end_phase("copy_artifacts")

            # Log final metrics
            metrics.log_summary()

        return success

    except (RuntimeError, OSError, yaml.YAMLError) as e:
        logger.error(f"Build failed: {str(e)}")
        return False
