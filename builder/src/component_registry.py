"""Component registry for mapping OTel Collector config names to Go modules."""

import os
from dataclasses import dataclass
from typing import Optional

import yaml

from .logger import BuildLogger, get_logger

logger: BuildLogger = get_logger(__name__)


@dataclass
class ComponentInfo:
    """Information about an OpenTelemetry Collector component."""

    name: str
    gomod: str
    source: str  # "core", "contrib", or "bindplane"
    component_type: str  # "receiver", "processor", "exporter", "extension", "connector"


class ComponentRegistry:
    """Registry for looking up component Go modules from config names."""

    def __init__(self, components_file: Optional[str] = None):
        """Initialize the component registry.

        Args:
            components_file: Path to components.yaml file. If not provided,
                           uses the default file in the same directory.
        """
        if components_file is None:
            components_file = os.path.join(
                os.path.dirname(__file__), "components.yaml"
            )

        self._components: dict[str, dict[str, ComponentInfo]] = {
            "receivers": {},
            "processors": {},
            "exporters": {},
            "extensions": {},
            "connectors": {},
            "providers": {},
        }

        self._load_components(components_file)

    def _load_components(self, components_file: str) -> None:
        """Load components from YAML file."""
        with open(components_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        for component_type, components_dict in self._components.items():
            if component_type in data:
                for name, info in data[component_type].items():
                    components_dict[name] = ComponentInfo(
                        name=name,
                        gomod=info["gomod"],
                        source=info.get("source", "contrib"),
                        component_type=component_type,
                    )

    def lookup(
        self, component_type: str, name: str, version: str = "0.121.0"
    ) -> Optional[ComponentInfo]:
        """Look up a component by type and name.

        Args:
            component_type: Type of component (receivers, processors, etc.)
            name: Name of the component as used in config (e.g., "otlp", "batch")
            version: Version to use for the gomod

        Returns:
            ComponentInfo if found, None otherwise
        """
        # Normalize component type to plural form
        if not component_type.endswith("s"):
            component_type = component_type + "s"

        # Handle named instances (e.g., "otlp/traces" -> "otlp")
        base_name = name.split("/")[0]

        component = self._components.get(component_type, {}).get(base_name)

        if component:
            # Create a new ComponentInfo with the versioned gomod
            versioned_gomod = self._apply_version(component.gomod, version)
            return ComponentInfo(
                name=component.name,
                gomod=versioned_gomod,
                source=component.source,
                component_type=component.component_type,
            )

        return None

    def _apply_version(self, gomod: str, version: str) -> str:
        """Apply version to a gomod string.

        Args:
            gomod: The gomod path (may contain __VERSION__ placeholder)
            version: The version to apply

        Returns:
            Gomod string with version applied
        """
        if "__VERSION__" in gomod:
            return gomod.replace("__VERSION__", version)
        return gomod

    def get_all_components(self, component_type: str) -> dict[str, ComponentInfo]:
        """Get all components of a specific type.

        Args:
            component_type: Type of component (receivers, processors, etc.)

        Returns:
            Dictionary of component name to ComponentInfo
        """
        if not component_type.endswith("s"):
            component_type = component_type + "s"
        return self._components.get(component_type, {})

    def find_similar(
        self, component_type: str, name: str, max_results: int = 3
    ) -> list[str]:
        """Find similar component names for typo suggestions.

        Args:
            component_type: Type of component
            name: Name that wasn't found
            max_results: Maximum number of suggestions

        Returns:
            List of similar component names
        """
        if not component_type.endswith("s"):
            component_type = component_type + "s"

        all_names = list(self._components.get(component_type, {}).keys())

        # Simple similarity based on common prefix/suffix
        suggestions = []
        name_lower = name.lower()

        for candidate in all_names:
            candidate_lower = candidate.lower()
            # Check for partial matches
            if (
                name_lower in candidate_lower
                or candidate_lower in name_lower
                or self._levenshtein_distance(name_lower, candidate_lower) <= 2
            ):
                suggestions.append(candidate)
                if len(suggestions) >= max_results:
                    break

        return suggestions

    @staticmethod
    def _levenshtein_distance(s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            # pylint: disable=arguments-out-of-order
            return ComponentRegistry._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row: list[int] = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]


# Global registry instance (lazy loaded)
_registry: Optional[ComponentRegistry] = None


def get_registry(components_file: Optional[str] = None) -> ComponentRegistry:
    """Get the global component registry instance.

    Args:
        components_file: Optional path to components.yaml file

    Returns:
        ComponentRegistry instance
    """
    global _registry  # pylint: disable=global-statement
    if _registry is None or components_file is not None:
        _registry = ComponentRegistry(components_file)
    return _registry
