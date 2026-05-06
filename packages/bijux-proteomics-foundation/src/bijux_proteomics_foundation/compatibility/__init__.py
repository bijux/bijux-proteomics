# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owner paths for schema compatibility and migration contracts."""

from __future__ import annotations

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
    "MigrationRegistry",
    "SchemaCompatibility",
    "SchemaEvolutionAssessment",
    "SchemaMigration",
    "assess_schema_compatibility",
    "assess_schema_evolution",
]
