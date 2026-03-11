"""Parser for OpenTelemetry Collector configuration files."""

from dataclasses import dataclass, field
from typing import Optional

import yaml

from .component_registry import ComponentInfo, get_registry
from .logger import BuildLogger, get_logger
from .version import DEFAULT_VERSION

logger: BuildLogger = get_logger(__name__)


@dataclass
class ParsedComponents:
    """Container for parsed components from a collector config."""

    receivers: list[str] = field(default_factory=list)
    processors: list[str] = field(default_factory=list)
    exporters: list[str] = field(default_factory=list)
    extensions: list[str] = field(default_factory=list)
    connectors: list[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        """Check if no components were found."""
        return not any(
            [
                self.receivers,
                self.processors,
                self.exporters,
                self.extensions,
                self.connectors,
            ]
        )

    def all_components(self) -> dict[str, list[str]]:
        """Return all components as a dictionary."""
        return {
            "receivers": self.receivers,
            "processors": self.processors,
            "exporters": self.exporters,
            "extensions": self.extensions,
            "connectors": self.connectors,
        }


@dataclass
class ResolvedComponents:
    """Container for resolved components with their Go module paths."""

    receivers: list[ComponentInfo] = field(default_factory=list)
    processors: list[ComponentInfo] = field(default_factory=list)
    exporters: list[ComponentInfo] = field(default_factory=list)
    extensions: list[ComponentInfo] = field(default_factory=list)
    connectors: list[ComponentInfo] = field(default_factory=list)
    unresolved: dict[str, list[str]] = field(default_factory=dict)

    def has_unresolved(self) -> bool:
        """Check if there are any unresolved components."""
        return any(self.unresolved.values())


class ConfigParser:
    """Parser for OpenTelemetry Collector configuration files."""

    # Component sections that must be mappings (dict) when present
    _COMPONENT_SECTIONS = (
        "receivers",
        "processors",
        "exporters",
        "extensions",
        "connectors",
    )

    def __init__(self, config_content: str):
        """Initialize the parser with config content.

        Args:
            config_content: YAML content of the collector config file

        Raises:
            ValueError: If the content is not a valid OTel Collector config structure
        """
        self._config = yaml.safe_load(config_content)
        if self._config is None:
            self._config = {}
        self._validate_config_schema(self._config)

    @staticmethod
    def _validate_config_schema(config: object) -> None:
        """Validate that *config* has the expected OTel Collector structure.

        Checks performed (without requiring external dependencies):
        - Top-level value must be a mapping (dict), not a list or scalar.
        - Component sections (receivers, processors, exporters, extensions,
          connectors), if present, must be mappings.
        - ``service``, if present, must be a mapping.
        - ``service.pipelines``, if present, must be a mapping whose values
          are themselves mappings.
        - ``service.extensions``, if present, must be a sequence (list).

        Args:
            config: The deserialized YAML object to validate.

        Raises:
            ValueError: Describing the first structural problem found.
        """
        if not isinstance(config, dict):
            raise ValueError(
                "Invalid collector config: top-level value must be a YAML mapping "
                f"(got {type(config).__name__}). "
                "Ensure the file is a valid OpenTelemetry Collector configuration."
            )

        # Each component section must be a dict when present
        for section in ConfigParser._COMPONENT_SECTIONS:
            value = config.get(section)
            if value is not None and not isinstance(value, dict):
                raise ValueError(
                    f"Invalid collector config: '{section}' must be a mapping "
                    f"(got {type(value).__name__}). "
                    "Each component section should be a map of component name to config."
                )

        # Validate service block
        service = config.get("service")
        if service is not None:
            if not isinstance(service, dict):
                raise ValueError(
                    f"Invalid collector config: 'service' must be a mapping "
                    f"(got {type(service).__name__})."
                )

            pipelines = service.get("pipelines")
            if pipelines is not None:
                if not isinstance(pipelines, dict):
                    raise ValueError(
                        f"Invalid collector config: 'service.pipelines' must be a mapping "
                        f"(got {type(pipelines).__name__})."
                    )
                for pipeline_name, pipeline_cfg in pipelines.items():
                    if pipeline_cfg is not None and not isinstance(pipeline_cfg, dict):
                        raise ValueError(
                            f"Invalid collector config: pipeline '{pipeline_name}' "
                            f"must be a mapping (got {type(pipeline_cfg).__name__})."
                        )

            extensions = service.get("extensions")
            if extensions is not None and not isinstance(extensions, list):
                raise ValueError(
                    f"Invalid collector config: 'service.extensions' must be a sequence "
                    f"(got {type(extensions).__name__})."
                )

    def parse(self) -> ParsedComponents:
        """Parse the configuration and extract component names.

        Returns:
            ParsedComponents with all discovered component names
        """
        components = ParsedComponents()

        # Extract components from top-level sections
        components.receivers = self._extract_component_names("receivers")
        components.processors = self._extract_component_names("processors")
        components.exporters = self._extract_component_names("exporters")
        components.extensions = self._extract_component_names("extensions")
        components.connectors = self._extract_component_names("connectors")

        # Also check service.pipelines for any components we might have missed
        self._validate_against_service(components)

        return components

    def _extract_component_names(self, section: str) -> list[str]:
        """Extract unique base component names from a config section.

        Args:
            section: Name of the config section (e.g., "receivers")

        Returns:
            List of unique component base names
        """
        section_data = self._config.get(section, {})
        if not section_data:
            return []

        # Extract base names (handle named instances like "otlp/traces")
        base_names = set()
        for key in section_data.keys():
            # Split on "/" to get base name
            base_name = key.split("/")[0]
            base_names.add(base_name)

        return sorted(list(base_names))

    def _validate_against_service(self, components: ParsedComponents) -> None:
        """Validate and augment components based on service.pipelines.

        This ensures we capture any components referenced in pipelines
        that might not have explicit configuration sections.

        Note: Connectors can appear as both receivers (in destination pipelines)
        and exporters (in source pipelines), so we check against connectors too.

        Args:
            components: ParsedComponents to validate and augment
        """
        service = self._config.get("service", {})
        pipelines = service.get("pipelines", {})

        for pipeline_name, pipeline_config in pipelines.items():
            if not pipeline_config:
                continue

            # Check receivers in pipeline
            # Note: Connectors can appear as receivers in destination pipelines
            for receiver in pipeline_config.get("receivers", []):
                base_name = receiver.split("/")[0]
                if base_name not in components.receivers:
                    # Check if it's a connector (connectors act as receivers too)
                    if base_name not in components.connectors:
                        logger.warning(
                            f"Receiver '{receiver}' in pipeline '{pipeline_name}' "
                            f"not found in receivers or connectors section"
                        )
                        components.receivers.append(base_name)
                    # If it's a connector, that's expected - no warning needed

            # Check processors in pipeline
            for processor in pipeline_config.get("processors", []):
                base_name = processor.split("/")[0]
                if base_name not in components.processors:
                    logger.warning(
                        f"Processor '{processor}' in pipeline '{pipeline_name}' "
                        f"not found in processors section"
                    )
                    components.processors.append(base_name)

            # Check exporters in pipeline
            # Note: Connectors can appear as exporters in source pipelines
            for exporter in pipeline_config.get("exporters", []):
                base_name = exporter.split("/")[0]
                if base_name not in components.exporters:
                    # Check if it's a connector (connectors act as exporters too)
                    if base_name not in components.connectors:
                        logger.warning(
                            f"Exporter '{exporter}' in pipeline '{pipeline_name}' "
                            f"not found in exporters or connectors section"
                        )
                        components.exporters.append(base_name)
                    # If it's a connector, that's expected - no warning needed

        # Check extensions from service.extensions
        service_extensions = service.get("extensions", [])
        for ext in service_extensions:
            base_name = ext.split("/")[0]
            if base_name not in components.extensions:
                logger.warning(
                    f"Extension '{ext}' in service.extensions "
                    f"not found in extensions section"
                )
                components.extensions.append(base_name)

        # Sort after augmentation
        components.receivers = sorted(list(set(components.receivers)))
        components.processors = sorted(list(set(components.processors)))
        components.exporters = sorted(list(set(components.exporters)))
        components.extensions = sorted(list(set(components.extensions)))
        components.connectors = sorted(list(set(components.connectors)))


def resolve_components(
    parsed: ParsedComponents,
    version: str = DEFAULT_VERSION,
    custom_mappings: Optional[dict[str, dict[str, str]]] = None,
    core_version: Optional[str] = None,
) -> ResolvedComponents:
    """Resolve parsed component names to their Go module paths.

    Args:
        parsed: ParsedComponents from the config parser
        version: Version to use for contrib components
        custom_mappings: Optional custom component mappings to use
                        Format: {"receivers": {"name": "gomod"}, ...}
        core_version: Version to use for core collector components.
                     Defaults to version if not provided.

    Returns:
        ResolvedComponents with ComponentInfo for each resolved component
    """
    registry = get_registry()
    resolved = ResolvedComponents()
    resolved.unresolved = {
        "receivers": [],
        "processors": [],
        "exporters": [],
        "extensions": [],
        "connectors": [],
    }

    # Helper to resolve a list of component names
    def resolve_list(component_type: str, names: list[str]) -> list[ComponentInfo]:
        result = []
        custom = (custom_mappings or {}).get(component_type, {})

        for name in names:
            # Check custom mappings first
            if name in custom:
                info = ComponentInfo(
                    name=name,
                    gomod=custom[name].replace("__VERSION__", version),
                    source="custom",
                    component_type=component_type,
                )
                result.append(info)
                continue

            # Look up in registry
            looked_up = registry.lookup(
                component_type, name, version, core_version=core_version
            )
            if looked_up:
                result.append(looked_up)
            else:
                resolved.unresolved[component_type].append(name)
                # Try to find similar names for suggestions
                similar = registry.find_similar(component_type, name)
                if similar:
                    logger.warning(
                        f"Unknown {component_type[:-1]} '{name}'. "
                        f"Did you mean: {', '.join(similar)}?"
                    )
                else:
                    logger.warning(
                        f"Unknown {component_type[:-1]} '{name}'. "
                        f"No similar components found."
                    )

        return result

    resolved.receivers = resolve_list("receivers", parsed.receivers)
    resolved.processors = resolve_list("processors", parsed.processors)
    resolved.exporters = resolve_list("exporters", parsed.exporters)
    resolved.extensions = resolve_list("extensions", parsed.extensions)
    resolved.connectors = resolve_list("connectors", parsed.connectors)

    return resolved


def parse_config_file(config_path: str) -> ParsedComponents:
    """Parse an OpenTelemetry Collector config file.

    Args:
        config_path: Path to the config file

    Returns:
        ParsedComponents with all discovered component names
    """
    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()

    parser = ConfigParser(content)
    return parser.parse()


def parse_and_resolve(
    config_path: str,
    version: str = DEFAULT_VERSION,
    custom_mappings: Optional[dict[str, dict[str, str]]] = None,
    core_version: Optional[str] = None,
) -> ResolvedComponents:
    """Parse a config file and resolve components to Go modules.

    Args:
        config_path: Path to the config file
        version: Version to use for contrib components
        custom_mappings: Optional custom component mappings
        core_version: Version to use for core collector components

    Returns:
        ResolvedComponents with all resolved components
    """
    parsed = parse_config_file(config_path)
    return resolve_components(
        parsed, version, custom_mappings, core_version=core_version
    )
