# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Artifact integrity and size guards for runtime bundle reuse."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_runtime.runs.ledger import (
    RuntimeArtifactLedger,
    load_artifact_ledger,
)
from bijux_proteomics_runtime.support.workspace import RunWorkspace, write_json_atomic


class LargeArtifactGuardDecision(JsonModel):
    """Decision for one size guard check."""

    model_config = ConfigDict(extra="forbid")

    allowed: bool
    actual_size_bytes: int = Field(..., ge=0)
    max_size_bytes: int = Field(..., ge=1)
    artifact_label: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


class ArtifactIntegrityIssue(JsonModel):
    """One integrity issue that blocks bundle reuse."""

    model_config = ConfigDict(extra="forbid")

    artifact_kind: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    issue_code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class ArtifactIntegrityReport(JsonModel):
    """Integrity report for one runtime-managed run bundle."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    verified: bool
    max_artifact_bytes: int = Field(..., ge=1)
    checked_artifacts: int = Field(..., ge=0)
    issues: tuple[ArtifactIntegrityIssue, ...] = Field(default_factory=tuple)


def guard_path_size(path: Path, *, max_size_bytes: int) -> LargeArtifactGuardDecision:
    """Return whether one file is small enough for safe runtime bundle capture."""
    actual_size = path.stat().st_size
    allowed = actual_size <= max_size_bytes
    return LargeArtifactGuardDecision(
        allowed=allowed,
        actual_size_bytes=actual_size,
        max_size_bytes=max_size_bytes,
        artifact_label=str(path),
        reason=(
            "artifact size is within the runtime bundle guard"
            if allowed
            else "artifact exceeds the runtime bundle guard"
        ),
    )


def guard_payload_size(
    payload: dict[str, Any], *, artifact_label: str, max_size_bytes: int
) -> LargeArtifactGuardDecision:
    """Return whether one JSON payload is small enough for safe bundle capture."""
    actual_size = len(json.dumps(payload, sort_keys=True).encode("utf-8"))
    allowed = actual_size <= max_size_bytes
    return LargeArtifactGuardDecision(
        allowed=allowed,
        actual_size_bytes=actual_size,
        max_size_bytes=max_size_bytes,
        artifact_label=artifact_label,
        reason=(
            "payload size is within the runtime bundle guard"
            if allowed
            else "payload exceeds the runtime bundle guard"
        ),
    )


def build_artifact_integrity_report(
    *,
    workspace: RunWorkspace,
    run_id: str,
    artifact_ledger: RuntimeArtifactLedger,
    max_artifact_bytes: int,
    include_transient_artifacts: bool = True,
) -> ArtifactIntegrityReport:
    """Build an integrity report from the current artifact ledger."""
    issues: list[ArtifactIntegrityIssue] = []
    for entry in artifact_ledger.entries:
        if (
            not include_transient_artifacts
            and entry.retention_class.value == "transient"
        ):
            continue
        path = Path(entry.path)
        if not path.exists():
            issues.append(
                ArtifactIntegrityIssue(
                    artifact_kind=entry.artifact_kind,
                    artifact_path=entry.path,
                    issue_code="artifact_missing",
                    message="artifact listed in the ledger is missing on disk",
                )
            )
            continue
        if path.stat().st_size > max_artifact_bytes:
            issues.append(
                ArtifactIntegrityIssue(
                    artifact_kind=entry.artifact_kind,
                    artifact_path=entry.path,
                    issue_code="artifact_too_large",
                    message="artifact exceeds the configured bundle reuse guard",
                )
            )
        current_sha = hashlib.sha256(path.read_bytes()).hexdigest()
        if current_sha != entry.content_sha256:
            issues.append(
                ArtifactIntegrityIssue(
                    artifact_kind=entry.artifact_kind,
                    artifact_path=entry.path,
                    issue_code="artifact_corrupted",
                    message="artifact content no longer matches the recorded ledger hash",
                )
            )
    return ArtifactIntegrityReport(
        run_id=run_id,
        verified=not issues,
        max_artifact_bytes=max_artifact_bytes,
        checked_artifacts=len(artifact_ledger.entries),
        issues=tuple(issues),
    )


def write_artifact_integrity_report(
    workspace: RunWorkspace, report: ArtifactIntegrityReport
) -> None:
    """Persist one artifact integrity report."""
    write_json_atomic(workspace.integrity_report_path, report.to_dict())


def load_artifact_integrity_report(workspace: RunWorkspace) -> ArtifactIntegrityReport:
    """Load one persisted integrity report."""
    return ArtifactIntegrityReport.load_json(workspace.integrity_report_path)


def verify_runtime_artifact_integrity(
    workspace: RunWorkspace,
    *,
    run_id: str,
    max_artifact_bytes: int,
) -> ArtifactIntegrityReport:
    """Build and persist a fresh integrity report for one run."""
    report = build_artifact_integrity_report(
        workspace=workspace,
        run_id=run_id,
        artifact_ledger=load_artifact_ledger(workspace, run_id),
        max_artifact_bytes=max_artifact_bytes,
    )
    write_artifact_integrity_report(workspace, report)
    return report


def require_reusable_artifact_bundle(
    workspace: RunWorkspace,
    *,
    run_id: str,
    max_artifact_bytes: int,
    required_artifact_kinds: tuple[str, ...],
) -> None:
    """Fail when runtime-managed artifacts are unsafe to reuse."""
    report = build_artifact_integrity_report(
        workspace=workspace,
        run_id=run_id,
        artifact_ledger=load_artifact_ledger(workspace, run_id),
        max_artifact_bytes=max_artifact_bytes,
        include_transient_artifacts=False,
    )
    missing_required = {
        kind
        for kind in required_artifact_kinds
        if kind
        not in {
            entry.artifact_kind
            for entry in load_artifact_ledger(workspace, run_id).entries
        }
    }
    if report.verified and not missing_required:
        return
    reasons = [issue.issue_code for issue in report.issues]
    if missing_required:
        reasons.append(f"missing_required:{','.join(sorted(missing_required))}")
    raise ValueError(";".join(reasons) or "artifact_bundle_not_reusable")


__all__ = [
    "ArtifactIntegrityIssue",
    "ArtifactIntegrityReport",
    "LargeArtifactGuardDecision",
    "build_artifact_integrity_report",
    "guard_path_size",
    "guard_payload_size",
    "load_artifact_integrity_report",
    "require_reusable_artifact_bundle",
    "verify_runtime_artifact_integrity",
    "write_artifact_integrity_report",
]
