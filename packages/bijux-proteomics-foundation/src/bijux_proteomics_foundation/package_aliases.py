# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Compatibility import surface for alias-package helpers."""

from __future__ import annotations

from typing import Any

from bijux_proteomics_foundation.compatibility import (
    ImportMigrationSurface,
    compatibility_export_names,
    compatibility_module_dir,
    compatibility_module_getattr,
    emit_compatibility_import_warning,
    import_migration_deprecation_message,
)

MIGRATION_SURFACE = ImportMigrationSurface(
    legacy_import_path="bijux_proteomics_foundation.package_aliases",
    canonical_import_path="bijux_proteomics_foundation._package_aliases",
    retirement_condition=(
        "retire when alias-package wrappers and downstream imports use the private owner "
        "or stop depending on package-level alias forwarding entirely"
    ),
    rationale="alias-package helper ownership moved behind a private implementation module",
)
CANONICAL_IMPORT_PATH = MIGRATION_SURFACE.canonical_import_path
DEPRECATION_MESSAGE = import_migration_deprecation_message(MIGRATION_SURFACE)
__deprecated__ = True
__all__ = compatibility_export_names(MIGRATION_SURFACE)

emit_compatibility_import_warning(MIGRATION_SURFACE)


def __getattr__(name: str) -> Any:
    """Resolve compatibility imports from the canonical private alias-helper owner."""

    return compatibility_module_getattr(MIGRATION_SURFACE, name)


def __dir__() -> list[str]:
    """Expose canonical alias-helper names in interactive discovery."""

    return compatibility_module_dir(globals(), MIGRATION_SURFACE)
