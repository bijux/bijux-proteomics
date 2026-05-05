# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Artifact contracts and envelopes for lab planning outputs."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import DocumentSchema as SchemaMetadata, JsonModel


class LabArtifactProfile(JsonModel):
    """Version profile for lab planning and outcome artifacts."""

    model_config = ConfigDict(extra="forbid")

    profile_id: str = Field(
        ..., min_length=1, description="Stable artifact profile identifier."
    )
    minimum_schema_version: str = Field(
        ..., min_length=1, description="Minimum compatible schema version."
    )
    recommended_schema_version: str = Field(
        ..., min_length=1, description="Recommended schema version."
    )


class LabArtifactCompatibilityReport(JsonModel):
    """Compatibility report for a lab document schema."""

    model_config = ConfigDict(extra="forbid")

    profile_id: str = Field(
        ..., min_length=1, description="Artifact profile identifier."
    )
    schema_version: str = Field(
        ..., min_length=1, description="Document schema version under evaluation."
    )
    compatible: bool = Field(..., description="Whether the schema is compatible.")
    notes: list[str] = Field(
        default_factory=list, description="Compatibility rationale."
    )


class LabArtifactUpgradeAdvisory(JsonModel):
    """Upgrade advisory derived from artifact compatibility evaluation."""

    model_config = ConfigDict(extra="forbid")

    profile_id: str = Field(..., min_length=1, description="Profile identifier.")
    current_schema_version: str = Field(..., min_length=1)
    recommended_schema_version: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)
    notes: list[str] = Field(default_factory=list, description="Upgrade rationale.")


class LabArtifactSchemaContract(JsonModel):
    """Schema contract for a specific lab artifact kind."""

    model_config = ConfigDict(extra="forbid")

    artifact_kind: str = Field(..., min_length=1)
    required_created_by: str = Field(..., min_length=1)
    minimum_schema_version: str = Field(..., min_length=1)


class LabArtifactContractRegistry(JsonModel):
    """Registry of artifact contracts used in lab schema validation."""

    model_config = ConfigDict(extra="forbid")

    contracts: list[LabArtifactSchemaContract] = Field(default_factory=list)


class LabArtifactContractIssue(JsonModel):
    """Validation issue for artifact contract registry quality."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


def default_lab_artifact_profile() -> LabArtifactProfile:
    """Return the default artifact profile for lab outputs."""
    return LabArtifactProfile(
        profile_id="lab-default-profile",
        minimum_schema_version="1.0.0",
        recommended_schema_version="1.0.0",
    )


def evaluate_lab_artifact_compatibility(
    schema: SchemaMetadata,
    *,
    profile: LabArtifactProfile | None = None,
) -> LabArtifactCompatibilityReport:
    """Evaluate schema metadata compatibility for lab package artifacts."""
    profile = profile or default_lab_artifact_profile()
    compatible = schema.schema_version >= profile.minimum_schema_version
    notes = (
        ["schema version satisfies minimum compatibility requirement"]
        if compatible
        else ["schema version is below minimum compatibility requirement"]
    )
    if schema.schema_version != profile.recommended_schema_version:
        notes.append("schema version differs from recommended profile version")
    return LabArtifactCompatibilityReport(
        profile_id=profile.profile_id,
        schema_version=schema.schema_version,
        compatible=compatible,
        notes=notes,
    )


def evaluate_lab_artifact_schema_contract(
    schema: SchemaMetadata,
    *,
    contract: LabArtifactSchemaContract,
) -> LabArtifactCompatibilityReport:
    """Evaluate schema metadata against an artifact-specific contract."""
    compatible = (
        schema.schema_version >= contract.minimum_schema_version
        and schema.created_by == contract.required_created_by
    )
    notes: list[str] = []
    if schema.schema_version < contract.minimum_schema_version:
        notes.append("schema version is below artifact contract minimum")
    if schema.created_by != contract.required_created_by:
        notes.append("created_by does not match artifact contract")
    if not notes:
        notes.append("artifact schema contract is satisfied")
    return LabArtifactCompatibilityReport(
        profile_id=f"artifact:{contract.artifact_kind}",
        schema_version=schema.schema_version,
        compatible=compatible,
        notes=notes,
    )


def default_lab_artifact_contract_registry() -> LabArtifactContractRegistry:
    """Return a default registry for canonical lab artifacts."""
    return LabArtifactContractRegistry(
        contracts=[
            LabArtifactSchemaContract(
                artifact_kind="plan",
                required_created_by="bijux-proteomics-lab",
                minimum_schema_version="1.0.0",
            ),
            LabArtifactSchemaContract(
                artifact_kind="outcome",
                required_created_by="bijux-proteomics-lab",
                minimum_schema_version="1.0.0",
            ),
            LabArtifactSchemaContract(
                artifact_kind="feedback",
                required_created_by="bijux-proteomics-lab",
                minimum_schema_version="1.0.0",
            ),
        ]
    )


def evaluate_lab_artifact_with_registry(
    schema: SchemaMetadata,
    *,
    artifact_kind: str,
    registry: LabArtifactContractRegistry | None = None,
) -> LabArtifactCompatibilityReport:
    """Evaluate schema metadata by resolving an artifact contract from a registry."""
    registry = registry or default_lab_artifact_contract_registry()
    contract = next(
        (item for item in registry.contracts if item.artifact_kind == artifact_kind),
        None,
    )
    if contract is None:
        return LabArtifactCompatibilityReport(
            profile_id=f"artifact:{artifact_kind}",
            schema_version=schema.schema_version,
            compatible=False,
            notes=[
                f"no schema contract registered for artifact kind '{artifact_kind}'"
            ],
        )
    return evaluate_lab_artifact_schema_contract(schema, contract=contract)


def build_lab_artifact_upgrade_advisory(
    schema: SchemaMetadata,
    *,
    profile: LabArtifactProfile | None = None,
) -> LabArtifactUpgradeAdvisory:
    """Build actionable schema upgrade guidance for lab artifacts."""
    profile = profile or default_lab_artifact_profile()
    compatibility = evaluate_lab_artifact_compatibility(schema, profile=profile)
    if not compatibility.compatible:
        action = "upgrade"
        notes = ["schema is below minimum compatibility threshold"]
    elif schema.schema_version != profile.recommended_schema_version:
        action = "investigate"
        notes = ["schema is compatible but differs from recommended profile version"]
    else:
        action = "keep"
        notes = ["schema aligns with recommended profile"]
    return LabArtifactUpgradeAdvisory(
        profile_id=profile.profile_id,
        current_schema_version=schema.schema_version,
        recommended_schema_version=profile.recommended_schema_version,
        action=action,
        notes=notes,
    )


def lint_lab_artifact_contract_registry(
    registry: LabArtifactContractRegistry,
) -> list[LabArtifactContractIssue]:
    """Lint contract registry for duplicate kinds and invalid version ranges."""
    issues: list[LabArtifactContractIssue] = []
    seen: set[str] = set()
    for contract in registry.contracts:
        if contract.artifact_kind in seen:
            issues.append(
                LabArtifactContractIssue(
                    code="duplicate-artifact-kind",
                    message=f"duplicate contract for artifact kind '{contract.artifact_kind}'",
                )
            )
        seen.add(contract.artifact_kind)
        if contract.minimum_schema_version > "9.9.9":
            issues.append(
                LabArtifactContractIssue(
                    code="schema-version-suspicious",
                    message=f"contract '{contract.artifact_kind}' has suspicious minimum schema version",
                )
            )
    return issues


__all__ = [
    "LabArtifactCompatibilityReport",
    "LabArtifactContractIssue",
    "LabArtifactContractRegistry",
    "LabArtifactProfile",
    "LabArtifactSchemaContract",
    "LabArtifactUpgradeAdvisory",
    "build_lab_artifact_upgrade_advisory",
    "default_lab_artifact_contract_registry",
    "default_lab_artifact_profile",
    "evaluate_lab_artifact_compatibility",
    "evaluate_lab_artifact_schema_contract",
    "evaluate_lab_artifact_with_registry",
    "lint_lab_artifact_contract_registry",
]
