# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Schema compatibility assessments for durable document contracts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.compatibility.schema_migrations import (
    MigrationRegistry,
)
from bijux_proteomics_foundation.compatibility.schema_versions import SchemaVersion
from bijux_proteomics_foundation.serialization.json_contracts import JsonModel


class SchemaCompatibility(StrEnum):
    """Compatibility status for expected versus observed schema versions."""

    COMPATIBLE = "compatible"
    FORWARD_INCOMPATIBLE = "forward_incompatible"
    BACKWARD_INCOMPATIBLE = "backward_incompatible"


def assess_schema_compatibility(
    observed: str,
    expected: str,
) -> SchemaCompatibility:
    """Assess compatibility using major and minor version semantics."""
    observed_version = SchemaVersion.parse(observed)
    expected_version = SchemaVersion.parse(expected)
    if observed_version.major != expected_version.major:
        return SchemaCompatibility.BACKWARD_INCOMPATIBLE
    if not observed_version.is_additive_compatible_with(expected_version):
        return SchemaCompatibility.FORWARD_INCOMPATIBLE
    return SchemaCompatibility.COMPATIBLE


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


__all__ = [
    "SchemaCompatibility",
    "SchemaEvolutionAssessment",
    "assess_schema_compatibility",
    "assess_schema_evolution",
]
