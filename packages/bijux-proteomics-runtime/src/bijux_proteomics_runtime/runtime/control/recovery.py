# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Runtime partial-failure recovery auditing."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_runtime.runtime.context import RuntimeArtifactRetentionClass
from bijux_proteomics_runtime.runtime.control.integrity import (
    build_artifact_integrity_report,
)
from bijux_proteomics_runtime.runtime.control.ledger import load_artifact_ledger
from bijux_proteomics_runtime.runtime.workspace import RunWorkspace


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
    partial_failure: bool
    preserved_artifacts: tuple[FailureRecoveryArtifact, ...] = Field(default_factory=tuple)
    blocked_artifacts: tuple[FailureRecoveryArtifact, ...] = Field(default_factory=tuple)


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
    issue_by_path = {issue.artifact_path: issue.issue_code for issue in integrity_report.issues}
    summary = _load_summary_payload(workspace.run_summary_path)
    failure_type = str(summary.get("failure") or "none")
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
        partial_failure=failure_type != "none" and bool(preserved_artifacts),
        preserved_artifacts=tuple(preserved_artifacts),
        blocked_artifacts=tuple(blocked_artifacts),
    )


def _load_summary_payload(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


__all__ = [
    "FailureRecoveryArtifact",
    "RuntimeFailureRecoveryAudit",
    "build_runtime_failure_recovery_audit",
]
