# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Runtime-owned transport contracts for durable execution artifacts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.serialization.json_contracts import JsonModel
from bijux_proteomics_foundation.serialization.stable_hashes import (
    StableHashPolicy,
    default_hash_policy,
)


class ArtifactFormat(StrEnum):
    """Supported durable runtime artifact encodings."""

    JSON = "json"
    JSONL = "jsonl"
    TSV = "tsv"
    ARTIFACT_BUNDLE = "artifact_bundle"


class SchemaFormatContract(JsonModel):
    """Transport contract for one runtime-managed document artifact."""

    model_config = ConfigDict(extra="forbid")

    document_kind: str = Field(..., min_length=1, description="Document kind name.")
    artifact_format: ArtifactFormat = Field(..., description="Output transport format.")
    schema_version: str = Field(..., min_length=1, description="Schema version.")
    hash_policy_id: str = Field(..., min_length=1, description="Hash policy name.")
    nullability_policy_id: str = Field(
        default="scientific-nullability-v1",
        min_length=1,
        description="Nullability contract expected by the artifact.",
    )
    canonical_required: bool = Field(
        default=True,
        description="Whether canonical field ordering is required.",
    )


class SchemaFormatCompatibilityReport(JsonModel):
    """Compatibility report for one runtime transport contract."""

    model_config = ConfigDict(extra="forbid")

    document_kind: str = Field(..., min_length=1)
    artifact_format: ArtifactFormat
    compatible: bool
    notes: list[str] = Field(default_factory=list)


def build_schema_format_contract(
    *,
    document_kind: str,
    artifact_format: ArtifactFormat,
    schema_version: str,
    hash_policy: StableHashPolicy | None = None,
) -> SchemaFormatContract:
    """Build one explicit runtime transport contract."""
    hash_policy = hash_policy or default_hash_policy()
    return SchemaFormatContract(
        document_kind=document_kind,
        artifact_format=artifact_format,
        schema_version=schema_version,
        hash_policy_id=hash_policy.policy_id,
    )


def default_schema_format_contracts(
    *,
    document_kind: str,
    schema_version: str,
) -> tuple[SchemaFormatContract, ...]:
    """Return the default runtime transport contracts for one document kind."""
    return tuple(
        build_schema_format_contract(
            document_kind=document_kind,
            artifact_format=artifact_format,
            schema_version=schema_version,
        )
        for artifact_format in ArtifactFormat
    )


def evaluate_schema_format_contract(
    contract: SchemaFormatContract,
    *,
    expected_schema_version: str,
    expected_hash_policy_id: str | None = None,
) -> SchemaFormatCompatibilityReport:
    """Evaluate whether one transport contract matches current runtime rules."""
    notes: list[str] = []
    compatible = True
    if contract.schema_version != expected_schema_version:
        compatible = False
        notes.append("schema version differs from expected transport schema version")
    if (
        expected_hash_policy_id is not None
        and contract.hash_policy_id != expected_hash_policy_id
    ):
        compatible = False
        notes.append("hash policy differs from expected transport hash policy")
    if compatible:
        notes.append("format contract matches expected transport requirements")
    return SchemaFormatCompatibilityReport(
        document_kind=contract.document_kind,
        artifact_format=contract.artifact_format,
        compatible=compatible,
        notes=notes,
    )


__all__ = [
    "ArtifactFormat",
    "SchemaFormatCompatibilityReport",
    "SchemaFormatContract",
    "build_schema_format_contract",
    "default_schema_format_contracts",
    "evaluate_schema_format_contract",
]
