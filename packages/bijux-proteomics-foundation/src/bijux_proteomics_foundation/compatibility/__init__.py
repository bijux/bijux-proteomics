# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owner paths for schema compatibility and migration contracts."""

from __future__ import annotations

from bijux_proteomics_foundation.compatibility.import_migrations import (
    ImportMigrationSurface,
    compatibility_export_names,
    compatibility_module_dir,
    compatibility_module_getattr,
    emit_compatibility_import_warning,
    import_migration_deprecation_message,
    load_canonical_module,
)
from bijux_proteomics_foundation.compatibility.schema_assessments import (
    SchemaCompatibility,
    SchemaEvolutionAssessment,
    assess_schema_compatibility,
    assess_schema_evolution,
)
from bijux_proteomics_foundation.compatibility.schema_migrations import (
    MigrationRegistry,
    SchemaMigration,
)

__all__ = [
    "ImportMigrationSurface",
    "MigrationRegistry",
    "SchemaCompatibility",
    "SchemaEvolutionAssessment",
    "SchemaMigration",
    "assess_schema_compatibility",
    "assess_schema_evolution",
    "compatibility_export_names",
    "compatibility_module_dir",
    "compatibility_module_getattr",
    "emit_compatibility_import_warning",
    "import_migration_deprecation_message",
    "load_canonical_module",
]
