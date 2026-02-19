"""Resolve paths to package data (templates, YAML) for installed or frozen CLI.

Supports:
- PyInstaller: data under sys._MEIPASS (e.g. builder/versions.yaml, builder/templates/)
- Installed package / development: __file__-relative (package is on disk)
"""

import os
import sys
from functools import lru_cache
from typing import Optional


def _frozen_base() -> Optional[str]:
    """Return base path when running as PyInstaller one-file binary."""
    return getattr(sys, "_MEIPASS", None)


def _get_versions_yaml_path_impl() -> str:
    """Return path to builder/versions.yaml."""
    meipass = _frozen_base()
    if meipass:
        path = os.path.join(meipass, "builder", "versions.yaml")
        if os.path.isfile(path):
            return path
    # Installed or development: this file is in builder/src, builder/ is parent of parent
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "versions.yaml")
    )


def _get_templates_dir_impl() -> str:
    """Return path to builder/templates directory."""
    meipass = _frozen_base()
    if meipass:
        path = os.path.join(meipass, "builder", "templates")
        if os.path.isdir(path):
            return path
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "templates"))


def _get_components_yaml_path_impl() -> str:
    """Return path to builder/src/components.yaml."""
    meipass = _frozen_base()
    if meipass:
        path = os.path.join(meipass, "builder", "src", "components.yaml")
        if os.path.isfile(path):
            return path
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "components.yaml"))


def _get_bindplane_components_yaml_path_impl() -> str:
    """Return path to builder/src/bindplane_components.yaml."""
    meipass = _frozen_base()
    if meipass:
        path = os.path.join(meipass, "builder", "src", "bindplane_components.yaml")
        if os.path.isfile(path):
            return path
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), "bindplane_components.yaml")
    )


@lru_cache(maxsize=1)
def get_versions_yaml_path() -> str:
    """Return path to versions.yaml (cached)."""
    return _get_versions_yaml_path_impl()


@lru_cache(maxsize=1)
def get_templates_dir() -> str:
    """Return path to templates directory (cached)."""
    return _get_templates_dir_impl()


@lru_cache(maxsize=1)
def get_components_yaml_path() -> str:
    """Return path to components.yaml (cached)."""
    return _get_components_yaml_path_impl()


@lru_cache(maxsize=1)
def get_bindplane_components_yaml_path() -> str:
    """Return path to bindplane_components.yaml (cached)."""
    return _get_bindplane_components_yaml_path_impl()
