# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Typed runtime failure reports for execution and import surfaces."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_runtime.support.primitives.failures import (
    FailureType,
    suggest_next_action,
)
from bijux_proteomics_runtime.support.workspace import RunWorkspace, write_json_atomic


class RuntimeFailureCategory(StrEnum):
    """Failure categories the runtime package must distinguish."""

    SUBPROCESS = "subprocess"
    CONTAINER = "container"
    SCHEDULER = "scheduler"
    IMPORT = "import"
    VALIDATION = "validation"
    WORKSPACE = "workspace"
    UNKNOWN = "unknown"


class RuntimeFailureReport(JsonModel):
    """Machine-readable runtime failure report."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    failure_type: str = Field(..., min_length=1)
    failure_category: RuntimeFailureCategory
    retryable: bool
    message: str = Field(..., min_length=1)
    next_action: str = Field(..., min_length=1)
    detail_codes: tuple[str, ...] = Field(default_factory=tuple)


def build_runtime_failure_report(
    *,
    run_id: str,
    failure_type: str,
    message: str,
    detail_codes: list[str] | tuple[str, ...] = (),
) -> RuntimeFailureReport:
    """Build a typed runtime failure report from stable codes."""
    normalized_codes = tuple(sorted(str(code) for code in detail_codes if code))
    try:
        failure_enum = FailureType(failure_type)
    except ValueError:
        failure_enum = FailureType.UNKNOWN
    category = classify_runtime_failure(failure_enum, normalized_codes)
    retryable = failure_enum in {
        FailureType.TOOL_TIMEOUT,
        FailureType.TOOL_CRASH,
        FailureType.TOOL_FAILURE,
        FailureType.OOM,
    }
    return RuntimeFailureReport(
        run_id=run_id,
        failure_type=failure_enum.value,
        failure_category=category,
        retryable=retryable,
        message=message,
        next_action=suggest_next_action(failure_enum),
        detail_codes=normalized_codes,
    )


def classify_runtime_failure(
    failure_type: FailureType,
    detail_codes: tuple[str, ...] = (),
) -> RuntimeFailureCategory:
    """Classify one runtime failure using stable failure codes and details."""
    if any(code.startswith("missing_dependency:docker") for code in detail_codes):
        return RuntimeFailureCategory.CONTAINER
    if any(code.startswith("scheduler_") for code in detail_codes):
        return RuntimeFailureCategory.SCHEDULER
    if any(code.startswith("import_") for code in detail_codes):
        return RuntimeFailureCategory.IMPORT
    if any(
        code.startswith(prefix)
        for prefix in (
            "workspace_",
            "missing:config.json",
            "missing:plan.json",
            "missing:state.json",
            "missing:report.json",
            "missing:telemetry.json",
        )
        for code in detail_codes
    ):
        return RuntimeFailureCategory.WORKSPACE
    if failure_type in {
        FailureType.INPUT_INVALID,
        FailureType.INVALID_PLAN,
        FailureType.CAPABILITY_MISSING,
        FailureType.INVALID_OUTPUT,
    }:
        return RuntimeFailureCategory.VALIDATION
    if failure_type in {
        FailureType.TOOL_TIMEOUT,
        FailureType.TOOL_CRASH,
        FailureType.TOOL_FAILURE,
        FailureType.OOM,
    }:
        return RuntimeFailureCategory.SUBPROCESS
    return RuntimeFailureCategory.UNKNOWN


def write_runtime_failure_report(
    workspace: RunWorkspace,
    report: RuntimeFailureReport,
) -> None:
    """Persist a runtime failure report."""
    write_json_atomic(workspace.failure_report_path, report.to_dict())


__all__ = [
    "RuntimeFailureCategory",
    "RuntimeFailureReport",
    "build_runtime_failure_report",
    "classify_runtime_failure",
    "write_runtime_failure_report",
]
