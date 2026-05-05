# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Artifact-ledger helpers for replay-safe runtime outputs."""

from __future__ import annotations

import hashlib
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_runtime.runtime.context import (
    RuntimeArtifactPolicy,
    RuntimeArtifactRetentionClass,
)
from bijux_proteomics_runtime.runtime.workspace import RunWorkspace, write_json_atomic


class ArtifactLedgerEntry(JsonModel):
    """Ledger entry for one runtime-managed output artifact."""

    model_config = ConfigDict(extra="forbid")

    artifact_role: str = Field(..., min_length=1)
    artifact_kind: str = Field(..., min_length=1)
    path: str = Field(..., min_length=1)
    producer: str = Field(..., min_length=1)
    retention_class: RuntimeArtifactRetentionClass
    content_sha256: str = Field(..., min_length=1)
    size_bytes: int = Field(..., ge=0)


class RuntimeArtifactLedger(JsonModel):
    """Stable runtime artifact ledger for one run."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    entries: tuple[ArtifactLedgerEntry, ...] = Field(default_factory=tuple)


_TOP_LEVEL_ARTIFACTS: tuple[tuple[str, str, str], ...] = (
    ("config_path", "run_config", "runtime-config"),
    ("plan_path", "run_plan", "runtime-plan"),
    ("state_path", "run_state", "runtime-state"),
    ("report_path", "run_report", "runtime-report"),
    ("telemetry_path", "run_telemetry", "runtime-telemetry"),
    ("analysis_path", "run_analysis", "runtime-analysis"),
    ("execution_path", "run_execution", "runtime-execution"),
    ("timings_path", "run_timings", "runtime-timings"),
    ("run_summary_path", "run_summary", "runtime-status"),
    ("run_output_path", "run_output", "runtime-output"),
    ("run_context_path", "run_context", "runtime-run-context"),
    ("error_path", "run_error", "runtime-error"),
    ("failure_report_path", "failure_report", "runtime-failure-report"),
    ("lifecycle_path", "run_lifecycle", "runtime-lifecycle"),
    (
        "execution_snapshots_path",
        "execution_snapshots",
        "runtime-execution-snapshots",
    ),
    (
        "telemetry_snapshots_path",
        "telemetry_snapshots",
        "runtime-telemetry-snapshots",
    ),
    ("human_decision_path", "human_decision", "runtime-human-decision"),
    (
        "candidate_selection_path",
        "candidate_selection",
        "runtime-candidate-selection",
    ),
    ("replay_contract_path", "replay_contract", "runtime-replay-contract"),
    ("local_run_bundle_path", "local_run_bundle", "runtime-local-run-bundle"),
    (
        "container_run_bundle_path",
        "container_run_bundle",
        "runtime-container-run-bundle",
    ),
    (
        "scheduler_job_bundle_path",
        "scheduler_job_bundle",
        "runtime-scheduler-job-bundle",
    ),
    ("import_trace_path", "import_trace", "runtime-import-trace"),
    ("import_run_bundle_path", "import_run_bundle", "runtime-import-run-bundle"),
    ("resume_checkpoint_path", "resume_checkpoint", "runtime-resume-checkpoint"),
    ("integrity_report_path", "integrity_report", "runtime-integrity-report"),
    ("preflight_report_path", "preflight_report", "runtime-preflight-report"),
)


def load_artifact_ledger(workspace: RunWorkspace, run_id: str) -> RuntimeArtifactLedger:
    """Load the current artifact ledger or return an empty one."""
    if not workspace.artifact_ledger_path.exists():
        return RuntimeArtifactLedger(run_id=run_id, entries=())
    return RuntimeArtifactLedger.load_json(workspace.artifact_ledger_path)


def record_artifact_entry(
    workspace: RunWorkspace,
    *,
    run_id: str,
    artifact_role: str,
    artifact_kind: str,
    path: Path,
    producer: str,
    retention_class: RuntimeArtifactRetentionClass,
) -> ArtifactLedgerEntry:
    """Record or update one artifact ledger entry."""
    entry = ArtifactLedgerEntry(
        artifact_role=artifact_role,
        artifact_kind=artifact_kind,
        path=str(path),
        producer=producer,
        retention_class=retention_class,
        content_sha256=_sha256(path),
        size_bytes=path.stat().st_size,
    )
    ledger = load_artifact_ledger(workspace, run_id)
    keyed_entries = {(item.artifact_role, item.path): item for item in ledger.entries}
    keyed_entries[(entry.artifact_role, entry.path)] = entry
    updated = RuntimeArtifactLedger(
        run_id=run_id,
        entries=tuple(
            keyed_entries[key]
            for key in sorted(keyed_entries, key=lambda value: (value[0], value[1]))
        ),
    )
    write_json_atomic(workspace.artifact_ledger_path, updated.to_dict())
    return entry


def refresh_runtime_artifact_ledger(
    workspace: RunWorkspace,
    *,
    run_id: str,
    artifact_policy: RuntimeArtifactPolicy,
    producer: str,
) -> RuntimeArtifactLedger:
    """Refresh the ledger for all known top-level and item artifacts."""
    for property_name, artifact_role, artifact_kind in _TOP_LEVEL_ARTIFACTS:
        path = getattr(workspace, property_name)
        if not path.exists():
            continue
        retention_class = artifact_policy.retention_by_role.get(
            artifact_kind,
            RuntimeArtifactRetentionClass.TRANSIENT,
        )
        record_artifact_entry(
            workspace,
            run_id=run_id,
            artifact_role=artifact_role,
            artifact_kind=artifact_kind,
            path=path,
            producer=producer,
            retention_class=retention_class,
        )
    for path in sorted(workspace.artifact_items_dir.glob("*.json")):
        record_artifact_entry(
            workspace,
            run_id=run_id,
            artifact_role="artifact_item",
            artifact_kind="runtime-artifact-item",
            path=path,
            producer=producer,
            retention_class=RuntimeArtifactRetentionClass.REVIEW_REQUIRED,
        )
    return load_artifact_ledger(workspace, run_id)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


__all__ = [
    "ArtifactLedgerEntry",
    "RuntimeArtifactLedger",
    "load_artifact_ledger",
    "record_artifact_entry",
    "refresh_runtime_artifact_ledger",
]
