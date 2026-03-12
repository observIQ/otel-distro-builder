"""Tests for local Go module resolution in the build system."""

import os
import tempfile

import pytest
from src.build import _resolve_local_modules


@pytest.mark.unit
class TestResolveLocalModules:
    """Tests for _resolve_local_modules."""

    def test_copies_local_module_to_build_dir(self, tmp_path):
        """Local module directory is copied into the build directory."""
        # Create a fake local module
        source_dir = tmp_path / "manifest_dir"
        source_dir.mkdir()
        module_dir = source_dir / "myprocessor"
        module_dir.mkdir()
        (module_dir / "go.mod").write_text("module github.com/example/myprocessor\n")
        (module_dir / "main.go").write_text("package main\n")

        build_dir = tmp_path / "build"
        build_dir.mkdir()

        manifest = {
            "dist": {"name": "test"},
            "processors": [
                {
                    "gomod": "github.com/example/myprocessor v1.0.0",
                    "path": "./myprocessor",
                },
            ],
        }

        _resolve_local_modules(manifest, str(source_dir), str(build_dir))

        # Module should be copied
        copied = build_dir / "myprocessor"
        assert copied.is_dir()
        assert (copied / "go.mod").exists()
        assert (copied / "main.go").exists()

        # Path in manifest should be updated
        assert manifest["processors"][0]["path"] == "./myprocessor"

    def test_resolves_relative_path(self, tmp_path):
        """Relative paths are resolved against manifest_source_dir."""
        source_dir = tmp_path / "project"
        source_dir.mkdir()
        module_dir = source_dir / "libs" / "myext"
        module_dir.mkdir(parents=True)
        (module_dir / "go.mod").write_text("module github.com/example/myext\n")

        build_dir = tmp_path / "build"
        build_dir.mkdir()

        manifest = {
            "dist": {"name": "test"},
            "extensions": [
                {"gomod": "github.com/example/myext v0.1.0", "path": "./libs/myext"},
            ],
        }

        _resolve_local_modules(manifest, str(source_dir), str(build_dir))

        # Should be copied using basename
        assert (build_dir / "myext").is_dir()
        assert (build_dir / "myext" / "go.mod").exists()
        assert manifest["extensions"][0]["path"] == "./myext"

    def test_skips_entries_without_path(self, tmp_path):
        """Entries without a path key are left unchanged."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        manifest = {
            "dist": {"name": "test"},
            "receivers": [
                {
                    "gomod": "go.opentelemetry.io/collector/receiver/otlpreceiver v0.127.0"
                },
            ],
        }

        # Should not raise
        _resolve_local_modules(manifest, str(tmp_path), str(build_dir))

        # Entry unchanged
        assert "path" not in manifest["receivers"][0]

    def test_skips_missing_sections(self, tmp_path):
        """Sections not present in the manifest are silently skipped."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        manifest = {"dist": {"name": "test"}}

        # Should not raise
        _resolve_local_modules(manifest, str(tmp_path), str(build_dir))

    def test_raises_on_missing_module_directory(self, tmp_path):
        """RuntimeError is raised when the local module path does not exist."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        manifest = {
            "dist": {"name": "test"},
            "processors": [
                {"gomod": "github.com/example/missing v1.0.0", "path": "./missing"},
            ],
        }

        with pytest.raises(RuntimeError, match="Local module path does not exist"):
            _resolve_local_modules(manifest, str(tmp_path), str(build_dir))

    def test_multiple_local_modules(self, tmp_path):
        """Multiple local modules across different component types are all copied."""
        source_dir = tmp_path / "manifest_dir"
        source_dir.mkdir()

        for name in ["myprocessor", "myexporter"]:
            mod = source_dir / name
            mod.mkdir()
            (mod / "go.mod").write_text(f"module github.com/example/{name}\n")

        build_dir = tmp_path / "build"
        build_dir.mkdir()

        manifest = {
            "dist": {"name": "test"},
            "processors": [
                {
                    "gomod": "github.com/example/myprocessor v1.0.0",
                    "path": "./myprocessor",
                },
            ],
            "exporters": [
                {
                    "gomod": "github.com/example/myexporter v1.0.0",
                    "path": "./myexporter",
                },
            ],
        }

        _resolve_local_modules(manifest, str(source_dir), str(build_dir))

        assert (build_dir / "myprocessor").is_dir()
        assert (build_dir / "myexporter").is_dir()

    def test_overwrites_existing_destination(self, tmp_path):
        """If a module directory already exists in build_dir, it is replaced."""
        source_dir = tmp_path / "manifest_dir"
        source_dir.mkdir()
        module_dir = source_dir / "mymod"
        module_dir.mkdir()
        (module_dir / "go.mod").write_text("module github.com/example/mymod\n")
        (module_dir / "new_file.go").write_text("package main\n")

        build_dir = tmp_path / "build"
        build_dir.mkdir()
        # Pre-existing stale copy
        stale = build_dir / "mymod"
        stale.mkdir()
        (stale / "old_file.go").write_text("stale\n")

        manifest = {
            "dist": {"name": "test"},
            "receivers": [
                {"gomod": "github.com/example/mymod v1.0.0", "path": "./mymod"},
            ],
        }

        _resolve_local_modules(manifest, str(source_dir), str(build_dir))

        copied = build_dir / "mymod"
        assert (copied / "new_file.go").exists()
        assert not (copied / "old_file.go").exists()

    def test_mixed_local_and_remote_entries(self, tmp_path):
        """Only entries with path are processed; remote-only entries are untouched."""
        source_dir = tmp_path / "manifest_dir"
        source_dir.mkdir()
        module_dir = source_dir / "custom"
        module_dir.mkdir()
        (module_dir / "go.mod").write_text("module github.com/example/custom\n")

        build_dir = tmp_path / "build"
        build_dir.mkdir()

        manifest = {
            "dist": {"name": "test"},
            "processors": [
                {
                    "gomod": "go.opentelemetry.io/collector/processor/batchprocessor v0.127.0"
                },
                {"gomod": "github.com/example/custom v1.0.0", "path": "./custom"},
                {
                    "gomod": "github.com/open-telemetry/opentelemetry-collector-contrib/processor/filterprocessor v0.127.0"
                },
            ],
        }

        _resolve_local_modules(manifest, str(source_dir), str(build_dir))

        # Remote entries unchanged
        assert "path" not in manifest["processors"][0]
        assert "path" not in manifest["processors"][2]

        # Local entry updated
        assert manifest["processors"][1]["path"] == "./custom"
        assert (build_dir / "custom").is_dir()
