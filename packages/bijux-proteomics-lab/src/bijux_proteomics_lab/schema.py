# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Schema metadata and compatibility helpers for lab artifacts."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import DocumentSchema as SchemaMetadata
from bijux_proteomics_foundation import JsonModel


class LabSchemaProfile(JsonModel):
    """Version profile for lab planning and outcome artifacts."""

    model_config = ConfigDict(extra="forbid")

    profile_id: str = Field(..., min_length=1, description="Stable schema profile identifier.")
    minimum_schema_version: str = Field(..., min_length=1, description="Minimum compatible schema version.")
    recommended_schema_version: str = Field(..., min_length=1, description="Recommended schema version.")


class LabSchemaCompatibilityReport(JsonModel):
    """Compatibility report for a lab document schema."""

    model_config = ConfigDict(extra="forbid")

    profile_id: str = Field(..., min_length=1, description="Schema profile identifier.")
    schema_version: str = Field(..., min_length=1, description="Document schema version under evaluation.")
    compatible: bool = Field(..., description="Whether the schema is compatible.")
    notes: list[str] = Field(default_factory=list, description="Compatibility rationale.")


class LabArtifactSchemaContract(JsonModel):
    """Schema contract for a specific lab artifact kind."""

    model_config = ConfigDict(extra="forbid")

    artifact_kind: str = Field(..., min_length=1, description="Artifact kind such as plan, outcome, or feedback.")
    required_created_by: str = Field(..., min_length=1, description="Expected created_by provenance value.")
    minimum_schema_version: str = Field(..., min_length=1, description="Minimum allowed schema version.")


def default_lab_schema_profile() -> LabSchemaProfile:
    """Return the default schema profile for lab artifacts."""
    return LabSchemaProfile(
        profile_id="lab-default-profile",
        minimum_schema_version="1.0.0",
        recommended_schema_version="1.0.0",
    )


def evaluate_lab_schema_compatibility(
    schema: SchemaMetadata,
    *,
    profile: LabSchemaProfile | None = None,
) -> LabSchemaCompatibilityReport:
    """Evaluate schema metadata compatibility for lab package artifacts."""
    profile = profile or default_lab_schema_profile()
    compatible = schema.schema_version >= profile.minimum_schema_version
    notes = (
        ["schema version satisfies minimum compatibility requirement"]
        if compatible
        else ["schema version is below minimum compatibility requirement"]
    )
    if schema.schema_version != profile.recommended_schema_version:
        notes.append("schema version differs from recommended profile version")
    return LabSchemaCompatibilityReport(
        profile_id=profile.profile_id,
        schema_version=schema.schema_version,
        compatible=compatible,
        notes=notes,
    )


def evaluate_lab_artifact_schema_contract(
    schema: SchemaMetadata,
    *,
    contract: LabArtifactSchemaContract,
) -> LabSchemaCompatibilityReport:
    """Evaluate schema metadata against an artifact-specific contract."""
    compatible = schema.schema_version >= contract.minimum_schema_version and schema.created_by == contract.required_created_by
    notes: list[str] = []
    if schema.schema_version < contract.minimum_schema_version:
        notes.append("schema version is below artifact contract minimum")
    if schema.created_by != contract.required_created_by:
        notes.append("created_by does not match artifact contract")
    if not notes:
        notes.append("artifact schema contract is satisfied")
    return LabSchemaCompatibilityReport(
        profile_id=f"artifact:{contract.artifact_kind}",
        schema_version=schema.schema_version,
        compatible=compatible,
        notes=notes,
    )


__all__ = [
    "SchemaMetadata",
    "LabSchemaProfile",
    "LabSchemaCompatibilityReport",
    "default_lab_schema_profile",
    "evaluate_lab_schema_compatibility",
    "LabArtifactSchemaContract",
    "evaluate_lab_artifact_schema_contract",
]
