# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Shared helpers for compatibility import surfaces over moved modules."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from importlib import import_module
from types import ModuleType
from typing import Any
import warnings

__all__ = [
    "ImportMigrationSurface",
    "compatibility_export_names",
    "compatibility_module_dir",
    "compatibility_module_getattr",
    "emit_compatibility_import_warning",
    "import_migration_deprecation_message",
    "load_canonical_module",
]


@dataclass(frozen=True)
class ImportMigrationSurface:
    """One compatibility import path and its canonical replacement."""

    legacy_import_path: str
    canonical_import_path: str
    retirement_condition: str
    rationale: str


def import_migration_deprecation_message(surface: ImportMigrationSurface) -> str:
    """Return the deprecation message for one compatibility import surface."""

    return (
        f"{surface.legacy_import_path} is a compatibility import surface; "
        f"import {surface.canonical_import_path} instead. "
        f"{surface.retirement_condition}"
    )


def emit_compatibility_import_warning(surface: ImportMigrationSurface) -> None:
    """Emit one deprecation warning for a compatibility import surface."""

    warnings.warn(
        import_migration_deprecation_message(surface),
        DeprecationWarning,
        stacklevel=3,
    )


def load_canonical_module(surface: ImportMigrationSurface) -> ModuleType:
    """Load the canonical module behind one compatibility surface."""

    return import_module(surface.canonical_import_path)


def compatibility_export_names(surface: ImportMigrationSurface) -> tuple[str, ...]:
    """Return the exported names for a compatibility module."""

    canonical_module = load_canonical_module(surface)
    exported_names = getattr(canonical_module, "__all__", None)
    if exported_names is not None:
        return tuple(str(name) for name in exported_names)
    return tuple(name for name in dir(canonical_module) if not name.startswith("_"))


def compatibility_module_getattr(surface: ImportMigrationSurface, name: str) -> Any:
    """Resolve one attribute from the canonical module for a compatibility path."""

    return getattr(load_canonical_module(surface), name)


def compatibility_module_dir(
    module_globals: Mapping[str, object],
    surface: ImportMigrationSurface,
) -> list[str]:
    """Expose canonical names in interactive discovery for compatibility imports."""

    return sorted(set(module_globals) | set(dir(load_canonical_module(surface))))
