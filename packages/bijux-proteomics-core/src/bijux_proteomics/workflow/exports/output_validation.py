# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Structured validation over completed workflow-owned output directories."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.errors import InvalidWorkflowError, ScientificEvidenceError
from bijux_proteomics.workflow.exports.artifact_layout import (
    WorkflowArtifactLayoutManifest,
    load_workflow_artifact_manifest,
    validate_workflow_artifact_manifest,
)
from bijux_proteomics_foundation import JsonModel


class WorkflowOutputValidationStatus(StrEnum):
    """Stable outcome states for completed workflow output validation."""

    VALID = "valid"
    INVALID = "invalid"


class WorkflowOutputValidationCheck(StrEnum):
    """Owned workflow contract checks applied to completed output directories."""

    MANIFEST_ARTIFACT_LAYOUT = "manifest_artifact_layout"
    DECLARED_ARTIFACT_COMPLETENESS = "declared_artifact_completeness"
    ARTIFACT_INVENTORY = "artifact_inventory"


class WorkflowOutputValidationIssueCode(StrEnum):
    """Stable failure categories for completed workflow output validation."""

    MISSING_MANIFEST = "missing_manifest"
    MISSING_REQUIRED_ARTIFACT = "missing_required_artifact"
    SCHEMA_MISMATCH = "schema_mismatch"
    ROW_COUNT_MISMATCH = "row_count_mismatch"
    CHECKSUM_MISMATCH = "checksum_mismatch"
    INVENTORY_MISMATCH = "inventory_mismatch"
    CONTRACT_VIOLATION = "contract_violation"


class WorkflowOutputValidationIssue(JsonModel):
    """One blocking workflow contract failure for a completed run."""

    model_config = ConfigDict(extra="forbid")

    check: WorkflowOutputValidationCheck
    code: WorkflowOutputValidationIssueCode
    message: str = Field(..., min_length=1)
    artifact_relative_path: str | None = None
    blocking: bool = True


class WorkflowOutputValidationReport(JsonModel):
    """Structured validation report over one completed workflow output directory."""

    model_config = ConfigDict(extra="forbid")

    validator_name: str = "workflow_output_contract"
    validator_schema_version: str = "2026-05-26"
    output_dir: str = Field(..., min_length=1)
    status: WorkflowOutputValidationStatus
    checks: tuple[WorkflowOutputValidationCheck, ...] = Field(
        default_factory=lambda: (
            WorkflowOutputValidationCheck.MANIFEST_ARTIFACT_LAYOUT,
            WorkflowOutputValidationCheck.DECLARED_ARTIFACT_COMPLETENESS,
            WorkflowOutputValidationCheck.ARTIFACT_INVENTORY,
        )
    )
    layout_name: str | None = None
    manifest_schema_version: str | None = None
    producer_function: str | None = None
    artifact_count: int = Field(..., ge=0)
    issue_count: int = Field(..., ge=0)
    issues: tuple[WorkflowOutputValidationIssue, ...] = Field(default_factory=tuple)


def build_workflow_output_validation_report(
    output_dir: Path,
) -> WorkflowOutputValidationReport:
    """Validate one completed workflow run against the owned workflow contract."""

    manifest, missing_manifest_issue = _load_validation_manifest(output_dir)
    if missing_manifest_issue is not None:
        return _build_validation_report(
            output_dir=output_dir,
            manifest=None,
            status=WorkflowOutputValidationStatus.INVALID,
            issues=(missing_manifest_issue,),
        )

    assert manifest is not None
    try:
        validate_workflow_artifact_manifest(output_dir)
    except (ScientificEvidenceError, InvalidWorkflowError) as error:
        return _build_validation_report(
            output_dir=output_dir,
            manifest=manifest,
            status=WorkflowOutputValidationStatus.INVALID,
            issues=(_classify_workflow_output_validation_issue(error),),
        )
    return _build_validation_report(
        output_dir=output_dir,
        manifest=manifest,
        status=WorkflowOutputValidationStatus.VALID,
        issues=(),
    )


def _load_validation_manifest(
    output_dir: Path,
) -> tuple[WorkflowArtifactLayoutManifest | None, WorkflowOutputValidationIssue | None]:
    try:
        return load_workflow_artifact_manifest(output_dir), None
    except ScientificEvidenceError as error:
        return None, WorkflowOutputValidationIssue(
            check=WorkflowOutputValidationCheck.MANIFEST_ARTIFACT_LAYOUT,
            code=WorkflowOutputValidationIssueCode.MISSING_MANIFEST,
            message=str(error),
            artifact_relative_path="manifest.json",
        )


def _build_validation_report(
    *,
    output_dir: Path,
    manifest: WorkflowArtifactLayoutManifest | None,
    status: WorkflowOutputValidationStatus,
    issues: tuple[WorkflowOutputValidationIssue, ...],
) -> WorkflowOutputValidationReport:
    return WorkflowOutputValidationReport(
        output_dir=str(output_dir),
        status=status,
        layout_name=None if manifest is None else manifest.layout_name,
        manifest_schema_version=(
            None if manifest is None else manifest.manifest_schema_version
        ),
        producer_function=None if manifest is None else manifest.producer_function,
        artifact_count=0 if manifest is None else len(manifest.artifacts),
        issue_count=len(issues),
        issues=issues,
    )


def _classify_workflow_output_validation_issue(
    error: ScientificEvidenceError | InvalidWorkflowError,
) -> WorkflowOutputValidationIssue:
    message = str(error)
    return WorkflowOutputValidationIssue(
        check=_classify_workflow_output_validation_check(message),
        code=_classify_workflow_output_validation_code(message),
        message=message,
        artifact_relative_path=_extract_artifact_relative_path(message),
    )


def _classify_workflow_output_validation_check(
    message: str,
) -> WorkflowOutputValidationCheck:
    if "inventory" in message:
        return WorkflowOutputValidationCheck.ARTIFACT_INVENTORY
    if "declared at " in message:
        return WorkflowOutputValidationCheck.DECLARED_ARTIFACT_COMPLETENESS
    return WorkflowOutputValidationCheck.MANIFEST_ARTIFACT_LAYOUT


def _classify_workflow_output_validation_code(
    message: str,
) -> WorkflowOutputValidationIssueCode:
    if "workflow artifact manifest is missing" in message:
        return WorkflowOutputValidationIssueCode.MISSING_MANIFEST
    if "missing file" in message or "missing required file" in message or "declared at " in message:
        return WorkflowOutputValidationIssueCode.MISSING_REQUIRED_ARTIFACT
    if "inventory" in message:
        return WorkflowOutputValidationIssueCode.INVENTORY_MISMATCH
    if "checksum mismatch" in message:
        return WorkflowOutputValidationIssueCode.CHECKSUM_MISMATCH
    if "schema mismatch" in message:
        return WorkflowOutputValidationIssueCode.SCHEMA_MISMATCH
    if "row-count mismatch" in message or "row count mismatch" in message:
        return WorkflowOutputValidationIssueCode.ROW_COUNT_MISMATCH
    return WorkflowOutputValidationIssueCode.CONTRACT_VIOLATION


def _extract_artifact_relative_path(message: str) -> str | None:
    if " declared at " in message and "missing " in message:
        return message.split("missing ", maxsplit=1)[1].split(
            " declared at ",
            maxsplit=1,
        )[0]
    for token in message.replace(":", " ").split():
        if "/" in token or "." in token:
            return token.strip("',\"")
    return None


__all__ = [
    "WorkflowOutputValidationCheck",
    "WorkflowOutputValidationIssue",
    "WorkflowOutputValidationIssueCode",
    "WorkflowOutputValidationReport",
    "WorkflowOutputValidationStatus",
    "build_workflow_output_validation_report",
]
