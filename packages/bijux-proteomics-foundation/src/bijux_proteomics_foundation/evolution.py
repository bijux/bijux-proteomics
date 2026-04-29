# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Schema evolution assessments built on compatibility and migration rules."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.migrations import MigrationRegistry
from bijux_proteomics_foundation.schema import SchemaCompatibility, assess_schema_compatibility
from bijux_proteomics_foundation.serialization import JsonModel


class SchemaEvolutionAssessment(JsonModel):
    """Compatibility and migration assessment between two schema versions."""

    model_config = ConfigDict(extra="forbid")

    observed_version: str = Field(..., min_length=1)
    target_version: str = Field(..., min_length=1)
    compatibility: SchemaCompatibility
    migration_required: bool
    migration_available: bool
    deprecated_target: bool
    notes: list[str] = Field(default_factory=list)


def assess_schema_evolution(
    *,
    observed_version: str,
    target_version: str,
    registry: MigrationRegistry | None = None,
) -> SchemaEvolutionAssessment:
    """Assess whether a schema can evolve safely to a target version."""
    compatibility = assess_schema_compatibility(observed_version, target_version)
    migration_required = observed_version != target_version
    deprecated_target = registry.is_deprecated(target_version) if registry else False
    migration_available = (
        registry.can_migrate_to(observed_version, target_version)
        if registry and migration_required and not deprecated_target
        else not migration_required
    )
    notes: list[str] = []
    if compatibility is SchemaCompatibility.BACKWARD_INCOMPATIBLE:
        notes.append("major schema version differs and requires coordinated upgrade")
    elif compatibility is SchemaCompatibility.FORWARD_INCOMPATIBLE:
        notes.append("observed schema is older than the target contract")
    else:
        notes.append("schema versions remain within compatible major/minor bounds")
    if migration_required:
        if migration_available:
            notes.append("migration path is available for the target schema version")
        else:
            notes.append("no migration path is available for the target schema version")
    else:
        notes.append("no migration is required")
    if deprecated_target:
        notes.append("target schema version is deprecated")
    return SchemaEvolutionAssessment(
        observed_version=observed_version,
        target_version=target_version,
        compatibility=compatibility,
        migration_required=migration_required,
        migration_available=migration_available,
        deprecated_target=deprecated_target,
        notes=notes,
    )
