"""Generator for OpenTelemetry Collector Builder (OCB) manifest files."""

import os
from dataclasses import dataclass, field
from typing import Any, Optional

import yaml

from .config_parser import ResolvedComponents
from .logger import BuildLogger, get_logger

logger: BuildLogger = get_logger(__name__)

# Path to bindplane components file
BINDPLANE_COMPONENTS_FILE = os.path.join(
    os.path.dirname(__file__), "bindplane_components.yaml"
)

# Default manifest configuration
DEFAULT_MODULE = "github.com/custom/otelcol-distribution"
DEFAULT_NAME = "otelcol-custom"
DEFAULT_DESCRIPTION = "Custom OpenTelemetry Collector distribution"
DEFAULT_OUTPUT_PATH = "./_build"

# Standard providers that should be included in all manifests
DEFAULT_PROVIDERS = [
    "go.opentelemetry.io/collector/confmap/provider/envprovider",
    "go.opentelemetry.io/collector/confmap/provider/fileprovider",
    "go.opentelemetry.io/collector/confmap/provider/httpprovider",
    "go.opentelemetry.io/collector/confmap/provider/httpsprovider",
    "go.opentelemetry.io/collector/confmap/provider/yamlprovider",
]

# Common replaces that are often needed
DEFAULT_REPLACES = [
    {
        "comment": "See https://github.com/google/gnostic/issues/262",
        "old": "github.com/googleapis/gnostic v0.5.6",
        "new": "github.com/googleapis/gnostic v0.5.5",
    },
    {
        "comment": "See https://github.com/open-telemetry/opentelemetry-collector-contrib/pull/12322#issuecomment-1185029670",
        "old": "github.com/docker/go-connections v0.4.1-0.20210727194412-58542c764a11",
        "new": "github.com/docker/go-connections v0.4.0",
    },
    {
        "comment": "See https://github.com/mattn/go-ieproxy/issues/45",
        "old": "github.com/mattn/go-ieproxy",
        "new": "github.com/mattn/go-ieproxy v0.0.1",
    },
    {
        "comment": "See https://github.com/openshift/api/pull/1515",
        "old": "github.com/openshift/api",
        "new": "github.com/openshift/api v0.0.0-20230726162818-81f778f3b3ec",
    },
]


@dataclass
class ManifestConfig:
    """Configuration for manifest generation."""

    module: str = DEFAULT_MODULE
    name: str = DEFAULT_NAME
    description: str = DEFAULT_DESCRIPTION
    version: str = "1.0.0"
    output_path: str = DEFAULT_OUTPUT_PATH
    otel_version: str = "0.121.0"
    include_providers: bool = True
    include_replaces: bool = True
    include_bindplane: bool = True
    conf_resolver_default_uri_scheme: str = "env"


@dataclass
class GeneratedManifest:
    """Container for a generated manifest."""

    content: str
    yaml_dict: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


class ManifestGenerator:
    """Generator for OCB manifest files from resolved components."""

    def __init__(
        self,
        resolved: ResolvedComponents,
        config: Optional[ManifestConfig] = None,
    ):
        """Initialize the manifest generator.

        Args:
            resolved: ResolvedComponents from the config parser
            config: Optional ManifestConfig for customization
        """
        self._resolved = resolved
        self._config = config or ManifestConfig()
        self._warnings: list[str] = []
        self._bindplane_components: Optional[dict] = None

        if self._config.include_bindplane:
            self._bindplane_components = self._load_bindplane_components()

    def _load_bindplane_components(self) -> Optional[dict]:
        """Load Bindplane collector components from the config file.

        Returns:
            Dictionary with Bindplane collector components or None if file not found
        """
        try:
            with open(BINDPLANE_COMPONENTS_FILE, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # Get the version and apply it to all components
            version = data.get("version", "1.72.0")
            version_str = f"v{version}"

            # Process each component type
            for comp_type in ["extensions", "receivers", "processors", "exporters"]:
                if comp_type in data:
                    for i, item in enumerate(data[comp_type]):
                        if "gomod" in item:
                            data[comp_type][i]["gomod"] = item["gomod"].replace(
                                "__BINDPLANE_VERSION__", version_str
                            )

            logger.info(f"Loaded Bindplane components (version {version})")
            return data

        except FileNotFoundError:
            logger.warning(f"Bindplane components file not found: {BINDPLANE_COMPONENTS_FILE}")
            return None
        except yaml.YAMLError as e:
            logger.warning(f"Failed to parse Bindplane components: {e}")
            return None

    def generate(self) -> GeneratedManifest:
        """Generate the OCB manifest.

        Returns:
            GeneratedManifest containing the YAML content
        """
        manifest: dict[str, Any] = {}

        # Add dist section
        manifest["dist"] = {
            "module": self._config.module,
            "name": self._config.name,
            "description": self._config.description,
            "version": self._config.version,
            "output_path": self._config.output_path,
        }

        # Add conf_resolver section
        manifest["conf_resolver"] = {
            "default_uri_scheme": self._config.conf_resolver_default_uri_scheme,
        }

        # Add component sections (user's components + bindplane components)
        manifest["extensions"] = self._format_components_with_bindplane(
            self._resolved.extensions, "extensions"
        )

        manifest["receivers"] = self._format_components_with_bindplane(
            self._resolved.receivers, "receivers"
        )

        manifest["processors"] = self._format_components_with_bindplane(
            self._resolved.processors, "processors"
        )

        manifest["exporters"] = self._format_components_with_bindplane(
            self._resolved.exporters, "exporters"
        )

        if self._resolved.connectors:
            manifest["connectors"] = self._format_components(
                self._resolved.connectors
            )

        # Remove empty sections
        for key in ["extensions", "receivers", "processors", "exporters"]:
            if not manifest[key]:
                del manifest[key]

        # Add providers
        if self._config.include_providers:
            manifest["providers"] = self._format_providers()

        # Add replaces
        if self._config.include_replaces:
            manifest["replaces"] = self._format_replaces()

        # Check for unresolved components
        if self._resolved.has_unresolved():
            for comp_type, names in self._resolved.unresolved.items():
                for name in names:
                    self._warnings.append(
                        f"Unresolved {comp_type[:-1]}: '{name}' - "
                        f"you may need to add a custom gomod entry"
                    )

        # Generate YAML content
        content = self._generate_yaml(manifest)

        return GeneratedManifest(
            content=content,
            yaml_dict=manifest,
            warnings=self._warnings,
        )

    def _format_components(self, components) -> list[dict]:
        """Format components for the manifest.

        Args:
            components: List of ComponentInfo objects

        Returns:
            List of gomod entries
        """
        return [{"gomod": c.gomod} for c in components]

    def _format_components_with_bindplane(
        self, components, component_type: str
    ) -> list[dict]:
        """Format components and append Bindplane components.

        Args:
            components: List of ComponentInfo objects from user's config
            component_type: Type of component (extensions, receivers, etc.)

        Returns:
            List of gomod entries including Bindplane components
        """
        result = [{"gomod": c.gomod} for c in components]

        # Add Bindplane components if enabled
        if self._bindplane_components and component_type in self._bindplane_components:
            bp_components = self._bindplane_components[component_type]
            for bp in bp_components:
                if "gomod" in bp:
                    # Avoid duplicates
                    if not any(bp["gomod"] in r.get("gomod", "") for r in result):
                        result.append({"gomod": bp["gomod"]})

        return result

    def _format_providers(self) -> list[dict]:
        """Format providers for the manifest.

        Returns:
            List of provider gomod entries
        """
        # Determine provider version based on otel version
        # Provider versions follow a different scheme (1.x.x vs 0.x.x)
        otel_version = self._config.otel_version
        # Extract minor version and convert to provider version
        # e.g., 0.121.0 -> 1.27.0 (roughly)
        parts = otel_version.split(".")
        if len(parts) >= 2:
            minor = int(parts[1])
            # Provider version is typically ~94 versions behind
            provider_minor = minor - 94
            if provider_minor > 0:
                provider_version = f"1.{provider_minor}.0"
            else:
                provider_version = "1.0.0"
        else:
            provider_version = "1.0.0"

        return [
            {"gomod": f"{p} v{provider_version}"}
            for p in DEFAULT_PROVIDERS
        ]

    def _format_replaces(self) -> list[str]:
        """Format replaces for the manifest.

        Returns:
            List of replace directives
        """
        replaces = [f"{r['old']} => {r['new']}" for r in DEFAULT_REPLACES]

        # Add Bindplane replaces if enabled
        if self._bindplane_components and "replaces" in self._bindplane_components:
            for r in self._bindplane_components["replaces"]:
                replace_str = f"{r['old']} => {r['new']}"
                if replace_str not in replaces:
                    replaces.append(replace_str)

        return replaces

    def _generate_yaml(self, manifest: dict) -> str:
        """Generate YAML content with comments.

        Args:
            manifest: The manifest dictionary

        Returns:
            YAML string with comments
        """
        # Use a custom representer for cleaner output
        class CleanDumper(yaml.SafeDumper):
            pass

        def str_representer(dumper, data):
            if "\n" in data:
                return dumper.represent_scalar(
                    "tag:yaml.org,2002:str", data, style="|"
                )
            return dumper.represent_scalar("tag:yaml.org,2002:str", data)

        CleanDumper.add_representer(str, str_representer)

        # Generate base YAML
        content = yaml.dump(
            manifest,
            Dumper=CleanDumper,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

        # Add header comment
        header = (
            "# OpenTelemetry Collector Builder (OCB) Manifest\n"
            "# Generated from collector config.yaml\n"
            f"# Target version: {self._config.otel_version}\n"
            "#\n"
            "# To build: ocb --config manifest.yaml\n"
            "#\n\n"
        )

        return header + content


def generate_manifest(
    resolved: ResolvedComponents,
    module: str = DEFAULT_MODULE,
    name: str = DEFAULT_NAME,
    description: str = DEFAULT_DESCRIPTION,
    version: str = "1.0.0",
    otel_version: str = "0.121.0",
    output_path: Optional[str] = None,
    include_bindplane: bool = True,
) -> GeneratedManifest:
    """Generate an OCB manifest from resolved components.

    Args:
        resolved: ResolvedComponents from the config parser
        module: Go module path for the distribution
        name: Name of the distribution
        description: Description of the distribution
        version: Version of the distribution
        otel_version: Target OpenTelemetry version
        output_path: Output path for built artifacts
        include_bindplane: Whether to include Bindplane components (default: True)

    Returns:
        GeneratedManifest containing the YAML content
    """
    config = ManifestConfig(
        module=module,
        name=name,
        description=description,
        version=version,
        otel_version=otel_version,
        output_path=output_path or DEFAULT_OUTPUT_PATH,
        include_bindplane=include_bindplane,
    )

    generator = ManifestGenerator(resolved, config)
    return generator.generate()


def generate_manifest_from_config(
    config_path: str,
    output_path: Optional[str] = None,
    module: str = DEFAULT_MODULE,
    name: str = DEFAULT_NAME,
    description: str = DEFAULT_DESCRIPTION,
    version: str = "1.0.0",
    otel_version: str = "0.121.0",
    custom_mappings: Optional[dict[str, dict[str, str]]] = None,
    include_bindplane: bool = True,
) -> GeneratedManifest:
    """Generate an OCB manifest directly from a config file.

    Args:
        config_path: Path to the collector config file
        output_path: Optional path to write the manifest to
        module: Go module path for the distribution
        name: Name of the distribution
        description: Description of the distribution
        version: Version of the distribution
        otel_version: Target OpenTelemetry version
        custom_mappings: Optional custom component mappings
        include_bindplane: Whether to include Bindplane components (default: True)

    Returns:
        GeneratedManifest containing the YAML content
    """
    # pylint: disable=import-outside-toplevel
    from .config_parser import parse_and_resolve

    # Parse and resolve components
    resolved = parse_and_resolve(config_path, otel_version, custom_mappings)

    # Generate manifest
    result = generate_manifest(
        resolved=resolved,
        module=module,
        name=name,
        description=description,
        version=version,
        otel_version=otel_version,
        include_bindplane=include_bindplane,
    )

    # Write to file if output path specified
    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result.content)
        logger.success(f"Manifest written to: {output_path}")

    return result
