# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Runtime partial-failure recovery auditing."""

from __future__ import annotations

from enum import StrEnum
import json
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_runtime.core.failures import FailureType
from bijux_proteomics_runtime.runs.contracts import RuntimeArtifactRetentionClass
from bijux_proteomics_runtime.runs.failure_reports import (
    RuntimeFailureCategory,
    RuntimeFailureReport,
    classify_runtime_failure,
)
from bijux_proteomics_runtime.runs.integrity import (
    build_artifact_integrity_report,
)
from bijux_proteomics_runtime.runs.ledger import load_artifact_ledger
from bijux_proteomics_runtime.runtime.workspace import RunWorkspace


class RuntimeRecoveryAction(StrEnum):
    """Operator-facing recovery actions for failed runtime runs."""

    RETRY_EXECUTION = "retry_execution"
    REPAIR_CONTAINER_RUNTIME = "repair_container_runtime"
    INSPECT_SCHEDULER_REJECTION = "inspect_scheduler_rejection"
    RESUME_INTERRUPTED_RUN = "resume_interrupted_run"
    MANUAL_REVIEW = "manual_review"


class FailureRecoveryArtifact(JsonModel):
    """One runtime artifact evaluated after a failed run."""

    model_config = ConfigDict(extra="forbid")

    artifact_kind: str = Field(..., min_length=1)
    path: str = Field(..., min_length=1)
    retention_class: RuntimeArtifactRetentionClass
    reusable: bool
    reason: str = Field(..., min_length=1)


class RuntimeFailureRecoveryAudit(JsonModel):
    """Failure audit that identifies preserved good artifacts after a failure."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    failure_type: str = Field(..., min_length=1)
    failure_category: RuntimeFailureCategory
    retryable: bool
    partial_failure: bool
    recovery_action: RuntimeRecoveryAction
    operator_summary: str = Field(..., min_length=1)
    preserved_artifacts: tuple[FailureRecoveryArtifact, ...] = Field(
        default_factory=tuple
    )
    blocked_artifacts: tuple[FailureRecoveryArtifact, ...] = Field(
        default_factory=tuple
    )


def build_runtime_failure_recovery_audit(
    workspace: RunWorkspace,
    *,
    run_id: str,
    max_artifact_bytes: int = 1_000_000,
) -> RuntimeFailureRecoveryAudit:
    """Audit which runtime artifacts remain reusable after a failed run."""
    ledger = load_artifact_ledger(workspace, run_id)
    integrity_report = build_artifact_integrity_report(
        workspace=workspace,
        run_id=run_id,
        artifact_ledger=ledger,
        max_artifact_bytes=max_artifact_bytes,
    )
    issue_by_path = {
        issue.artifact_path: issue.issue_code for issue in integrity_report.issues
    }
    summary = _load_summary_payload(workspace.run_summary_path)
    persisted_report = _load_failure_report(workspace.failure_report_path)
    failure_type = str(
        (persisted_report.failure_type if persisted_report is not None else None)
        or summary.get("failure")
        or "none"
    )
    failure_category = (
        persisted_report.failure_category
        if persisted_report is not None
        else classify_runtime_failure_tuple(failure_type)
    )
    retryable = (
        persisted_report.retryable
        if persisted_report is not None
        else failure_type in {"tool_timeout", "tool_crash", "tool_failure", "oom"}
    )
    preserved_artifacts: list[FailureRecoveryArtifact] = []
    blocked_artifacts: list[FailureRecoveryArtifact] = []
    for entry in ledger.entries:
        if entry.retention_class is RuntimeArtifactRetentionClass.TRANSIENT:
            continue
        path = Path(entry.path)
        issue_code = issue_by_path.get(entry.path)
        reusable = path.exists() and issue_code is None
        artifact = FailureRecoveryArtifact(
            artifact_kind=entry.artifact_kind,
            path=entry.path,
            retention_class=entry.retention_class,
            reusable=reusable,
            reason=(
                "artifact survives the failed phase and still matches the runtime integrity check"
                if reusable
                else f"artifact cannot be reused because {issue_code or 'artifact_missing'}"
            ),
        )
        if artifact.reusable:
            preserved_artifacts.append(artifact)
        else:
            blocked_artifacts.append(artifact)
    return RuntimeFailureRecoveryAudit(
        run_id=run_id,
        failure_type=failure_type,
        failure_category=failure_category,
        retryable=retryable,
        partial_failure=failure_type != "none" and bool(preserved_artifacts),
        recovery_action=_recovery_action(
            failure_type=failure_type,
            failure_category=failure_category,
            workspace=workspace,
            retryable=retryable,
        ),
        operator_summary=_operator_summary(
            failure_type=failure_type,
            failure_category=failure_category,
            preserved_artifacts=tuple(preserved_artifacts),
            blocked_artifacts=tuple(blocked_artifacts),
        ),
        preserved_artifacts=tuple(preserved_artifacts),
        blocked_artifacts=tuple(blocked_artifacts),
    )


def _load_summary_payload(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _load_failure_report(path: Path) -> RuntimeFailureReport | None:
    if not path.exists():
        return None
    return RuntimeFailureReport.load_json(path)


def classify_runtime_failure_tuple(failure_type: str) -> RuntimeFailureCategory:
    try:
        failure_enum = FailureType(failure_type)
    except ValueError:
        return RuntimeFailureCategory.UNKNOWN
    return classify_runtime_failure(
        failure_type=failure_enum,
        detail_codes=(),
    )


def _recovery_action(
    *,
    failure_type: str,
    failure_category: RuntimeFailureCategory,
    workspace: RunWorkspace,
    retryable: bool,
) -> RuntimeRecoveryAction:
    if workspace.resume_checkpoint_path.exists():
        return RuntimeRecoveryAction.RESUME_INTERRUPTED_RUN
    if failure_category is RuntimeFailureCategory.CONTAINER:
        return RuntimeRecoveryAction.REPAIR_CONTAINER_RUNTIME
    if failure_category is RuntimeFailureCategory.SCHEDULER:
        return RuntimeRecoveryAction.INSPECT_SCHEDULER_REJECTION
    if retryable:
        return RuntimeRecoveryAction.RETRY_EXECUTION
    if failure_type == "unknown":
        return RuntimeRecoveryAction.RESUME_INTERRUPTED_RUN
    return RuntimeRecoveryAction.MANUAL_REVIEW


def _operator_summary(
    *,
    failure_type: str,
    failure_category: RuntimeFailureCategory,
    preserved_artifacts: tuple[FailureRecoveryArtifact, ...],
    blocked_artifacts: tuple[FailureRecoveryArtifact, ...],
) -> str:
    return (
        f"runtime recorded {failure_type} in {failure_category.value} mode; "
        f"{len(preserved_artifacts)} preserved artifacts remain reusable and "
        f"{len(blocked_artifacts)} artifacts require regeneration"
    )


__all__ = [
    "FailureRecoveryArtifact",
    "RuntimeRecoveryAction",
    "RuntimeFailureRecoveryAudit",
    "build_runtime_failure_recovery_audit",
]
