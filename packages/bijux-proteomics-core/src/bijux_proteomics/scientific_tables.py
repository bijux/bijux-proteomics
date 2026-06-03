# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Compatibility import surface for governed scientific-table schema helpers."""

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
    legacy_import_path="bijux_proteomics.scientific_tables",
    canonical_import_path="bijux_proteomics._scientific_tables",
    retirement_condition=(
        "retire when downstream callers import the canonical private scientific-table "
        "owner or move to narrower workflow and contract surfaces"
    ),
    rationale="governed scientific-table schema validation moved behind a private owner",
)
CANONICAL_IMPORT_PATH = MIGRATION_SURFACE.canonical_import_path
DEPRECATION_MESSAGE = import_migration_deprecation_message(MIGRATION_SURFACE)
__deprecated__ = True
__all__ = compatibility_export_names(MIGRATION_SURFACE)

emit_compatibility_import_warning(MIGRATION_SURFACE)


def __getattr__(name: str) -> Any:
    """Resolve compatibility imports from the canonical private scientific-table owner."""

    return compatibility_module_getattr(MIGRATION_SURFACE, name)


def __dir__() -> list[str]:
    """Expose canonical scientific-table names in interactive discovery."""

    return compatibility_module_dir(globals(), MIGRATION_SURFACE)
