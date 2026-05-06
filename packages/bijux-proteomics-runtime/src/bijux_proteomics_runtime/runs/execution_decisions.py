# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Operator-facing execution decision reports for degraded and refused runs."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_runtime.runs.failure_reports import RuntimeFailureReport
from bijux_proteomics_runtime.runs.preflight import (
    PreflightCheckState,
    RuntimePreflightReport,
)
from bijux_proteomics_runtime.support.workspace import RunWorkspace, write_json_atomic


class ExecutionDecisionState(StrEnum):
    """Decision classes that operators need explained explicitly."""

    DEGRADED = "degraded"
    REFUSED = "refused"


class ExecutionDecisionFinding(JsonModel):
    """One operator-facing fact behind a runtime decision."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(..., min_length=1)
    state: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    operator_guidance: str = Field(..., min_length=1)


class RuntimeExecutionDecisionReport(JsonModel):
    """Stable report that explains runtime refusal and degraded execution."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    provider_name: str = Field(..., min_length=1)
    decision_state: ExecutionDecisionState
    failure_type: str | None = None
    failure_category: str | None = None
    retryable: bool | None = None
    findings: tuple[ExecutionDecisionFinding, ...] = Field(default_factory=tuple)
    next_action: str = Field(..., min_length=1)
    operator_summary: str = Field(..., min_length=1)


def build_runtime_refusal_decision_report(
    *,
    provider_name: str,
    preflight_report: RuntimePreflightReport | None = None,
    failure_report: RuntimeFailureReport | None = None,
) -> RuntimeExecutionDecisionReport:
    """Explain why runtime refused to proceed."""
    if preflight_report is None and failure_report is None:
        raise ValueError("refusal report requires preflight or failure evidence")
    run_id = (
        preflight_report.run_id
        if preflight_report is not None
        else failure_report.run_id  # type: ignore[union-attr]
    )
    findings: list[ExecutionDecisionFinding] = []
    if preflight_report is not None:
        findings.extend(
            ExecutionDecisionFinding(
                source_id=check.check_id,
                state=check.state.value,
                message=check.message,
                operator_guidance=_preflight_guidance(check.check_id),
            )
            for check in preflight_report.checks
            if check.state is not PreflightCheckState.PASS
        )
    if failure_report is not None:
        findings.extend(
            ExecutionDecisionFinding(
                source_id=detail_code,
                state="fail",
                message=failure_report.message,
                operator_guidance=failure_report.next_action,
            )
            for detail_code in failure_report.detail_codes
            if detail_code
        )
    next_action = (
        failure_report.next_action
        if failure_report is not None
        else "inspect the failed preflight checks and satisfy missing runtime requirements"
    )
    return RuntimeExecutionDecisionReport(
        run_id=run_id,
        provider_name=provider_name,
        decision_state=ExecutionDecisionState.REFUSED,
        failure_type=(
            failure_report.failure_type if failure_report is not None else None
        ),
        failure_category=(
            failure_report.failure_category.value
            if failure_report is not None
            else None
        ),
        retryable=failure_report.retryable if failure_report is not None else None,
        findings=tuple(findings),
        next_action=next_action,
        operator_summary=(
            f"runtime refused to proceed for {provider_name} because "
            f"{len(findings)} decision findings blocked a safe start"
        ),
    )


def build_runtime_degraded_execution_report(
    run_summary: dict[str, Any],
) -> RuntimeExecutionDecisionReport:
    """Explain why runtime completed in a degraded mode."""
    if str(run_summary.get("tool_status")) != "degraded":
        raise ValueError("degraded execution report requires degraded tool_status")
    warnings = tuple(str(warning) for warning in run_summary.get("warnings", ()))
    findings = tuple(
        ExecutionDecisionFinding(
            source_id=warning.split(":", 1)[0],
            state="warn",
            message=warning,
            operator_guidance=_degraded_guidance(warning),
        )
        for warning in warnings
        if warning.startswith(("cpu_fallback:", "cpu_mode:"))
    )
    return RuntimeExecutionDecisionReport(
        run_id=str(run_summary["run_id"]),
        provider_name=str(run_summary.get("provider", "unknown")),
        decision_state=ExecutionDecisionState.DEGRADED,
        findings=findings,
        next_action="review the fallback warning and confirm the degraded result is acceptable",
        operator_summary=(
            f"runtime completed in degraded mode for {run_summary.get('provider', 'unknown')} "
            f"because {len(findings)} fallback warnings forced a non-primary execution path"
        ),
    )


def write_runtime_execution_decision_report(
    workspace: RunWorkspace,
    report: RuntimeExecutionDecisionReport,
) -> None:
    """Persist one execution decision report."""
    write_json_atomic(workspace.execution_decision_report_path, report.to_dict())


def load_runtime_execution_decision_report(
    workspace: RunWorkspace,
) -> RuntimeExecutionDecisionReport:
    """Load one persisted execution decision report."""
    return RuntimeExecutionDecisionReport.load_json(
        workspace.execution_decision_report_path
    )


def _preflight_guidance(check_id: str) -> str:
    if check_id == "provider_requirements":
        return "install or expose the missing runtime dependencies before launching the provider"
    if check_id == "source_dataset":
        return "restore the declared source dataset before importing external evidence"
    if check_id == "source_dataset_layout":
        return "repair the source dataset structure so runtime can trust the import payload"
    if check_id == "tool_versions":
        return "align the configured tool version requirements with the actual execution engine"
    if check_id == "workspace_layout":
        return "repair the runtime workspace layout before retrying execution"
    return "inspect the failed preflight check and resolve it before retrying"


def _degraded_guidance(warning: str) -> str:
    if warning.startswith("cpu_fallback:"):
        return "verify that CPU fallback is scientifically acceptable for this run"
    if warning.startswith("cpu_mode:"):
        return "confirm that the requested provider can run under the forced CPU mode"
    return "inspect the degraded execution warning before accepting the result"


__all__ = [
    "ExecutionDecisionFinding",
    "ExecutionDecisionState",
    "RuntimeExecutionDecisionReport",
    "build_runtime_degraded_execution_report",
    "build_runtime_refusal_decision_report",
    "load_runtime_execution_decision_report",
    "write_runtime_execution_decision_report",
]
