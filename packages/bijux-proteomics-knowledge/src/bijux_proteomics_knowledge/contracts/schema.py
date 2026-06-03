# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Schema metadata and compatibility checks for knowledge documents."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import DocumentSchema as SchemaMetadata
from bijux_proteomics_foundation import JsonModel


class KnowledgeSchemaProfile(JsonModel):
    """Versioned schema profile for knowledge package documents."""

    model_config = ConfigDict(extra="forbid")

    profile_id: str = Field(
        ..., min_length=1, description="Stable schema profile identifier."
    )
    package: str = Field(
        default="bijux-proteomics-knowledge",
        min_length=1,
        description="Owning package name.",
    )
    minimum_schema_version: str = Field(
        ..., min_length=1, description="Minimum compatible schema version."
    )
    recommended_schema_version: str = Field(
        ..., min_length=1, description="Recommended schema version."
    )


class SchemaCompatibilityReport(JsonModel):
    """Compatibility report for a given document schema."""

    model_config = ConfigDict(extra="forbid")

    profile_id: str = Field(..., min_length=1, description="Schema profile identifier.")
    schema_version: str = Field(
        ..., min_length=1, description="Version from evaluated document schema."
    )
    compatible: bool = Field(
        ..., description="Whether the schema version is compatible with the profile."
    )
    notes: list[str] = Field(
        default_factory=list, description="Compatibility rationale."
    )


def default_knowledge_schema_profile() -> KnowledgeSchemaProfile:
    """Return the default schema compatibility profile for knowledge artifacts."""
    return KnowledgeSchemaProfile(
        profile_id="knowledge-default-profile",
        minimum_schema_version="1.0.0",
        recommended_schema_version="1.0.0",
    )


def evaluate_schema_compatibility(
    schema: SchemaMetadata,
    *,
    profile: KnowledgeSchemaProfile | None = None,
) -> SchemaCompatibilityReport:
    """Evaluate schema metadata compatibility against the package profile.

    Inputs:
    ``schema`` supplies persisted knowledge schema metadata and ``profile``
    optionally overrides the default compatibility profile.

    Outputs:
    Returns one ``SchemaCompatibilityReport`` describing compatibility status
    and advisory notes for the schema version.

    Failure Modes:
    This function does not raise governed public exceptions under normal typed
    input use.

    Scientific Caveats:
    Compatibility here covers owned document-version policy only; it does not
    prove annotation completeness, biological quality, or source correctness.
    """
    profile = profile or default_knowledge_schema_profile()
    notes: list[str] = []
    compatible = schema.schema_version >= profile.minimum_schema_version
    if compatible:
        notes.append("schema version satisfies minimum compatibility requirement")
    else:
        notes.append("schema version is below minimum compatibility requirement")
    if schema.schema_version != profile.recommended_schema_version:
        notes.append("schema version differs from recommended profile version")
    return SchemaCompatibilityReport(
        profile_id=profile.profile_id,
        schema_version=schema.schema_version,
        compatible=compatible,
        notes=notes,
    )


__all__ = [
    "SchemaMetadata",
    "KnowledgeSchemaProfile",
    "SchemaCompatibilityReport",
    "default_knowledge_schema_profile",
    "evaluate_schema_compatibility",
]
