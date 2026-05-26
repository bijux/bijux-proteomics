# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Workflow-owned structured failure reports."""

from __future__ import annotations

from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_runtime.runs.failure_reports import (
    RuntimeFailureCategory,
    classify_runtime_failure,
)
from bijux_proteomics_runtime.support.primitives.failures import (
    FailureType,
    suggest_next_action,
)
from bijux_proteomics_runtime.support.workspace import write_json_atomic


class WorkflowFailureReport(JsonModel):
    """Machine-readable failure report for workflow-owned execution surfaces."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    workflow_name: str = Field(..., min_length=1)
    stage_id: str | None = None
    failure_type: str = Field(..., min_length=1)
    failure_category: RuntimeFailureCategory
    retryable: bool
    message: str = Field(..., min_length=1)
    next_action: str = Field(..., min_length=1)
    reason_codes: tuple[str, ...] = Field(default_factory=tuple)


def build_workflow_failure_report(
    *,
    workflow_id: str,
    workflow_name: str,
    failure_type: str,
    message: str,
    stage_id: str | None = None,
    reason_codes: tuple[str, ...] | list[str] = (),
) -> WorkflowFailureReport:
    """Build one deterministic workflow failure report."""

    normalized_reason_codes = tuple(
        sorted({str(reason_code) for reason_code in reason_codes if reason_code})
    )
    try:
        failure_enum = FailureType(failure_type)
    except ValueError:
        failure_enum = FailureType.UNKNOWN
    category = classify_runtime_failure(failure_enum, normalized_reason_codes)
    retryable = failure_enum in {
        FailureType.TOOL_TIMEOUT,
        FailureType.TOOL_CRASH,
        FailureType.TOOL_FAILURE,
        FailureType.OOM,
    }
    return WorkflowFailureReport(
        workflow_id=workflow_id,
        workflow_name=workflow_name,
        stage_id=stage_id,
        failure_type=failure_enum.value,
        failure_category=category,
        retryable=retryable,
        message=message,
        next_action=suggest_next_action(failure_enum),
        reason_codes=normalized_reason_codes,
    )


def write_workflow_failure_report(
    output_dir: Path,
    report: WorkflowFailureReport,
) -> Path:
    """Persist one workflow failure report into a workflow output directory."""

    path = output_dir / "failure_report.json"
    write_json_atomic(path, report.to_dict())
    return path


__all__ = [
    "WorkflowFailureReport",
    "build_workflow_failure_report",
    "write_workflow_failure_report",
]
