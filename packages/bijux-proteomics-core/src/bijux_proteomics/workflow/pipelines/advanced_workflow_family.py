# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Shared protocol over the advanced workflow family."""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class AdvancedWorkflowResultKind(StrEnum):
    """Stable major result classes carried by advanced workflow owners."""

    BIOLOGY_RESULT = "biology_result"


class AdvancedWorkflowFamilyConfigContract(JsonModel):
    """Normalized config-field groups shared by advanced workflow owners."""

    model_config = ConfigDict(extra="forbid")

    output_dir_field: str = "output_dir"
    primary_input_fields: tuple[str, ...] = Field(default_factory=tuple)
    design_input_fields: tuple[str, ...] = Field(default_factory=tuple)
    reference_input_fields: tuple[str, ...] = Field(default_factory=tuple)
    annotation_input_fields: tuple[str, ...] = Field(default_factory=tuple)
    comparison_input_fields: tuple[str, ...] = Field(default_factory=tuple)


class AdvancedWorkflowFamilyArtifactContract(JsonModel):
    """Normalized output roles shared by advanced workflow owners."""

    model_config = ConfigDict(extra="forbid")

    workflow_manifest_json: str = Field(..., min_length=1)
    base_workflow_manifest_json: str = Field(..., min_length=1)
    review_manifest_json: str | None = None
    summary_tsv: str = Field(..., min_length=1)
    rejected_evidence_tsv: str = Field(..., min_length=1)
    supported_claim_tsv: str | None = None
    rejected_claim_tsv: str | None = None


class AdvancedWorkflowFamilyContract(JsonModel):
    """Canonical family contract shared by advanced workflow configs and outputs."""

    model_config = ConfigDict(extra="forbid")

    family_name: str = "canonical_advanced_workflow_family"
    family_schema_version: str = "2026-05-26"
    workflow_name: str = Field(..., min_length=1)
    result_kind: AdvancedWorkflowResultKind = AdvancedWorkflowResultKind.BIOLOGY_RESULT
    config: AdvancedWorkflowFamilyConfigContract
    artifacts: AdvancedWorkflowFamilyArtifactContract
    note: str = Field(..., min_length=1)


def build_advanced_workflow_family_contract(
    *,
    workflow_name: str,
    config: JsonModel,
    primary_input_fields: tuple[str, ...],
    design_input_fields: tuple[str, ...] = (),
    reference_input_fields: tuple[str, ...] = (),
    annotation_input_fields: tuple[str, ...] = (),
    comparison_input_fields: tuple[str, ...] = (),
    artifacts: AdvancedWorkflowFamilyArtifactContract,
    note: str,
) -> AdvancedWorkflowFamilyContract:
    """Build and validate one shared advanced-workflow family contract."""

    config_fields = type(config).model_fields
    field_groups = {
        "output_dir_field": ("output_dir",),
        "primary_input_fields": primary_input_fields,
        "design_input_fields": design_input_fields,
        "reference_input_fields": reference_input_fields,
        "annotation_input_fields": annotation_input_fields,
        "comparison_input_fields": comparison_input_fields,
    }
    failures = _validate_config_field_groups(
        config_fields=config_fields,
        field_groups=field_groups,
    )
    contract = AdvancedWorkflowFamilyContract(
        workflow_name=workflow_name,
        config=AdvancedWorkflowFamilyConfigContract(
            primary_input_fields=primary_input_fields,
            design_input_fields=design_input_fields,
            reference_input_fields=reference_input_fields,
            annotation_input_fields=annotation_input_fields,
            comparison_input_fields=comparison_input_fields,
        ),
        artifacts=artifacts,
        note=note,
    )
    failures.extend(validate_advanced_workflow_family_contract(contract))
    if failures:
        raise ValueError("; ".join(failures))
    return contract


def validate_advanced_workflow_family_contract(
    contract: AdvancedWorkflowFamilyContract,
) -> tuple[str, ...]:
    """Validate one advanced-workflow family contract for protocol drift."""

    failures: list[str] = []
    if not contract.workflow_name.startswith("advanced_"):
        failures.append("advanced workflow family contract requires an advanced_* workflow_name")
    if contract.config.output_dir_field != "output_dir":
        failures.append("advanced workflow family contract requires output_dir_field='output_dir'")
    if not contract.config.primary_input_fields:
        failures.append("advanced workflow family contract requires at least one primary_input_field")
    failures.extend(_validate_unique_field_groups(contract.config))
    expected_manifest_name = f"{contract.workflow_name}_workflow_manifest.json"
    if contract.artifacts.workflow_manifest_json != expected_manifest_name:
        failures.append(
            "advanced workflow family contract requires workflow_manifest_json "
            f"{expected_manifest_name!r}"
        )
    expected_summary_name = f"{contract.workflow_name}_summary.tsv"
    if contract.artifacts.summary_tsv != expected_summary_name:
        failures.append(
            "advanced workflow family contract requires summary_tsv "
            f"{expected_summary_name!r}"
        )
    if contract.artifacts.rejected_evidence_tsv != "rejected_evidence.tsv":
        failures.append(
            "advanced workflow family contract requires rejected_evidence_tsv "
            "'rejected_evidence.tsv'"
        )
    for artifact_name in (
        contract.artifacts.workflow_manifest_json,
        contract.artifacts.base_workflow_manifest_json,
        contract.artifacts.review_manifest_json,
    ):
        if artifact_name is not None and not artifact_name.endswith(".json"):
            failures.append(
                f"advanced workflow family contract manifest artifact {artifact_name!r} must end with .json"
            )
    for artifact_name in (
        contract.artifacts.summary_tsv,
        contract.artifacts.rejected_evidence_tsv,
        contract.artifacts.supported_claim_tsv,
        contract.artifacts.rejected_claim_tsv,
    ):
        if artifact_name is not None and not artifact_name.endswith(".tsv"):
            failures.append(
                f"advanced workflow family contract table artifact {artifact_name!r} must end with .tsv"
            )
    supported_claims_present = contract.artifacts.supported_claim_tsv is not None
    rejected_claims_present = contract.artifacts.rejected_claim_tsv is not None
    if supported_claims_present != rejected_claims_present:
        failures.append(
            "advanced workflow family contract must declare supported_claim_tsv and rejected_claim_tsv together"
        )
    return tuple(failures)


def _validate_config_field_groups(
    *,
    config_fields: Mapping[str, object],
    field_groups: dict[str, tuple[str, ...]],
) -> list[str]:
    failures: list[str] = []
    for group_name, field_names in field_groups.items():
        for field_name in field_names:
            if field_name not in config_fields:
                failures.append(
                    f"advanced workflow family config field {field_name!r} declared in {group_name} is missing"
                )
    return failures


def _validate_unique_field_groups(
    config_contract: AdvancedWorkflowFamilyConfigContract,
) -> list[str]:
    seen: dict[str, str] = {}
    failures: list[str] = []
    for group_name, field_names in (
        ("primary_input_fields", config_contract.primary_input_fields),
        ("design_input_fields", config_contract.design_input_fields),
        ("reference_input_fields", config_contract.reference_input_fields),
        ("annotation_input_fields", config_contract.annotation_input_fields),
        ("comparison_input_fields", config_contract.comparison_input_fields),
    ):
        for field_name in field_names:
            previous_group = seen.get(field_name)
            if previous_group is None:
                seen[field_name] = group_name
                continue
            failures.append(
                "advanced workflow family config field "
                f"{field_name!r} is declared in both {previous_group} and {group_name}"
            )
    return failures


__all__ = [
    "AdvancedWorkflowFamilyArtifactContract",
    "AdvancedWorkflowFamilyConfigContract",
    "AdvancedWorkflowFamilyContract",
    "AdvancedWorkflowResultKind",
    "build_advanced_workflow_family_contract",
    "validate_advanced_workflow_family_contract",
]
