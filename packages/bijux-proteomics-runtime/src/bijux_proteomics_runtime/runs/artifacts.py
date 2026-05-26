# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Artifact writing and inspection helpers for runtime control."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_intelligence.candidates import (
    candidate_to_domain,
    select_candidates,
)
from bijux_proteomics_intelligence.candidates.records import CandidateSelection
from bijux_proteomics_intelligence.candidates.schema import Candidate
from bijux_proteomics_runtime.runs.context import RunContext
from bijux_proteomics_runtime.runs.contracts import RuntimeArtifactRetentionClass
from bijux_proteomics_runtime.runs.failure_reports import (
    build_runtime_failure_report,
    write_runtime_failure_report,
)
from bijux_proteomics_runtime.runs.ledger import record_artifact_entry
from bijux_proteomics_runtime.state.schemas import ArtifactMetadata
from bijux_proteomics_runtime.support.primitives.failures import (
    FailureType,
    suggest_next_action,
)
from bijux_proteomics_runtime.support.primitives.hashing import sha256_hex
from bijux_proteomics_runtime.support.primitives.tooling import ToolError
from bijux_proteomics_runtime.support.workspace import (
    RunWorkspace,
    write_json_atomic,
    write_text_atomic,
)

__all__ = [
    "CandidateSelectionScoreSnapshot",
    "CandidateSelectionSnapshot",
    "ExecutionSnapshots",
    "HumanDecisionPayload",
    "HumanDecisionValidationReport",
    "RunComparisonReport",
    "TelemetryHooks",
    "_sign_payload",
    "compare_runs",
    "load_artifact",
    "map_failure_type",
    "require_human_decision",
    "selection_as_dict",
    "validate_human_decision",
    "write_artifact",
    "write_failure_artifacts",
]


class CandidateSelectionScoreSnapshot(JsonModel):
    """Stable score record for one human-review candidate."""

    candidate_id: str
    score: float
    rank: int
    reasons: tuple[str, ...] = ()


class CandidateSelectionSnapshot(JsonModel):
    """Typed review snapshot for one candidate selection decision."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    scores: tuple[CandidateSelectionScoreSnapshot, ...] = ()
    pareto_front: tuple[str, ...] = ()
    frozen_ids: tuple[str, ...] = ()
    human_required: bool
    metadata_raw_json: dict[str, Any] = Field(default_factory=dict, alias="metadata")


class HumanDecisionPayload(JsonModel):
    """Typed runtime payload for one human decision artifact."""

    status: str
    approved_ids: tuple[str, ...] = ()
    rejected_ids: tuple[str, ...] = ()
    notes: str = ""
    signature: str = ""


class HumanDecisionValidationReport(JsonModel):
    """Validation result for one persisted human decision payload."""

    passed: bool
    errors: tuple[str, ...] = ()
    payload: HumanDecisionPayload | None = None


class RunOutcomeSnapshot(JsonModel):
    """Stable outcome summary for one runtime run."""

    tool_status: str | None = None
    qc_status: str | None = None
    failure_type: str | None = None
    coordinator_decision: str | None = None


class RunIdentifierPair(JsonModel):
    """Stable pair of run identifiers for comparison output."""

    run_a: str | None = None
    run_b: str | None = None


class RunOutcomePair(JsonModel):
    """Stable pair of run outcomes for comparison output."""

    run_a: RunOutcomeSnapshot
    run_b: RunOutcomeSnapshot


class RunComparisonReport(JsonModel):
    """Typed comparison report across two runtime run directories."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    run_ids: RunIdentifierPair
    final_outcome: RunOutcomePair
    candidate_trajectories_raw_json: dict[str, Any] = Field(
        default_factory=dict,
        alias="candidate_trajectories",
    )
    iteration_deltas_raw_json: dict[str, Any] = Field(
        default_factory=dict,
        alias="iteration_deltas",
    )


def map_failure_type(status: str, error: ToolError | None) -> str:
    """map_failure_type."""
    if status == "success":
        return ""
    if error and error.error_type == "timeout":
        return FailureType.TOOL_TIMEOUT.value
    if error and error.error_type == "oom":
        return FailureType.OOM.value
    if error and error.error_type == "invalid_output":
        return FailureType.INVALID_OUTPUT.value
    if error and error.error_type == "tool_error":
        return FailureType.TOOL_CRASH.value
    return FailureType.UNKNOWN.value


def write_failure_artifacts(
    run_context: RunContext, failure_type: FailureType, details: Mapping[str, Any]
) -> None:
    """write_failure_artifacts."""
    payload = {
        "failure_type": failure_type.value,
        "details": dict(details),
        "next_action": suggest_next_action(failure_type),
    }
    write_json_atomic(run_context.workspace.error_path, payload)
    write_runtime_failure_report(
        run_context.workspace,
        build_runtime_failure_report(
            run_id=run_context.run_id,
            failure_type=failure_type.value,
            message=str(dict(details)),
            detail_codes=tuple(sorted(details.keys())),
        ),
    )
    record_artifact_entry(
        run_context.workspace,
        run_id=run_context.run_id,
        artifact_role="run_error",
        artifact_kind="runtime-error",
        path=run_context.workspace.error_path,
        producer="bijux_proteomics_runtime.runs.artifacts",
        retention_class=RuntimeArtifactRetentionClass.FAILURE_FORENSICS,
    )


def write_artifact(
    workspace: RunWorkspace,
    kind: str,
    payload: Mapping[str, Any],
    description: str = "",
    tags: list[str] | None = None,
) -> ArtifactMetadata:
    """write_artifact."""
    tags = tags or []
    if not description:
        description = "unspecified"
    materialized_payload = dict(payload)
    normalized = json.dumps(materialized_payload, sort_keys=True, separators=(",", ":"))
    artifact_id = sha256_hex(f"{kind}:{normalized}")
    path = workspace.artifact_items_dir / f"{artifact_id}.json"
    write_json_atomic(path, materialized_payload)
    record_artifact_entry(
        workspace,
        run_id=workspace.run_id,
        artifact_role="artifact_item",
        artifact_kind="runtime-artifact-item",
        path=path,
        producer="bijux_proteomics_runtime.runs.artifacts",
        retention_class=RuntimeArtifactRetentionClass.REVIEW_REQUIRED,
    )
    return ArtifactMetadata(
        artifact_id=artifact_id,
        kind=kind,
        description=description,
        tags=tags,
    )


def load_artifact(workspace: RunWorkspace, artifact_id: str) -> Mapping[str, Any]:
    """load_artifact."""
    path = workspace.artifact_items_dir / f"{artifact_id}.json"
    payload = json.loads(path.read_text())
    return dict(payload) if isinstance(payload, dict) else {}


@dataclass
class ExecutionSnapshots:
    """ExecutionSnapshots."""

    path: Path
    snapshots: list[dict[str, Any]] = field(default_factory=list)

    def record(
        self,
        iteration_index: int,
        state: dict[str, Any],
        decisions: list[dict[str, Any]],
        tool_outputs: list[dict[str, Any]],
    ) -> None:
        """record."""
        self.snapshots.append(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "iteration_index": iteration_index,
                "state": state,
                "decisions": decisions,
                "tool_outputs": tool_outputs,
            }
        )

    def write(self) -> None:
        """write."""
        write_text_atomic(
            self.path,
            json.dumps(self.snapshots, indent=2, sort_keys=True, default=str),
        )


class TelemetryHooks:
    """TelemetryHooks."""

    def __init__(self, run_context: RunContext) -> None:
        """__init__."""
        self._run_context = run_context
        self._snapshots: list[dict[str, Any]] = []
        self._execution_snapshots = ExecutionSnapshots(
            self._run_context.workspace.execution_snapshots_path
        )
        self._telemetry_path = self._run_context.workspace.telemetry_snapshots_path

    def record_snapshot(
        self, agent_name: str, iteration_index: int, payload: dict[str, Any]
    ) -> None:
        """record_snapshot."""
        self._snapshots.append(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "agent": agent_name,
                "iteration_index": iteration_index,
                "payload": payload,
            }
        )

    def record_execution_snapshot(
        self,
        iteration_index: int,
        state: dict[str, Any],
        decisions: list[dict[str, Any]],
        tool_outputs: list[dict[str, Any]],
    ) -> None:
        """record_execution_snapshot."""
        self._execution_snapshots.record(
            iteration_index,
            state=state,
            decisions=decisions,
            tool_outputs=tool_outputs,
        )

    def finalize(self) -> None:
        """finalize."""
        write_text_atomic(
            self._telemetry_path,
            json.dumps(self._snapshots, indent=2, sort_keys=True, default=str),
        )
        self._execution_snapshots.write()


def compare_runs(run_a: Path, run_b: Path) -> RunComparisonReport:
    """compare_runs."""
    data_a = _load_run(run_a)
    data_b = _load_run(run_b)
    analysis_a = _load_analysis(run_a)
    analysis_b = _load_analysis(run_b)

    return RunComparisonReport(
        run_ids=RunIdentifierPair(
            run_a=data_a.get("run_id"),
            run_b=data_b.get("run_id"),
        ),
        final_outcome=RunOutcomePair(
            run_a=RunOutcomeSnapshot(
                tool_status=data_a.get("tool_status"),
                qc_status=data_a.get("qc_status"),
                failure_type=data_a.get("failure_type"),
                coordinator_decision=data_a.get("coordinator_decision"),
            ),
            run_b=RunOutcomeSnapshot(
                tool_status=data_b.get("tool_status"),
                qc_status=data_b.get("qc_status"),
                failure_type=data_b.get("failure_type"),
                coordinator_decision=data_b.get("coordinator_decision"),
            ),
        ),
        candidate_trajectories_raw_json={
            "run_a": analysis_a.get("candidate_timeline", {}),
            "run_b": analysis_b.get("candidate_timeline", {}),
        },
        iteration_deltas_raw_json={
            "run_a": analysis_a.get("iteration_deltas", []),
            "run_b": analysis_b.get("iteration_deltas", []),
        },
    )


def require_human_decision(
    candidates: list[Candidate],
    workspace: RunWorkspace,
    top_n: int = 3,
) -> CandidateSelection:
    """require_human_decision."""
    selection = select_candidates(
        [candidate_to_domain(candidate) for candidate in candidates], top_n=top_n
    )
    _write_json(workspace.candidate_selection_path, selection_as_dict(selection).to_dict())
    _write_json(
        workspace.human_decision_path,
        {
            "status": "pending",
            "approved_ids": [],
            "rejected_ids": [],
            "notes": "",
            "signature": "",
        },
    )
    return selection


def selection_as_dict(selection: CandidateSelection) -> CandidateSelectionSnapshot:
    """selection_as_dict."""
    return CandidateSelectionSnapshot(
        scores=tuple(
            CandidateSelectionScoreSnapshot(
                candidate_id=score.candidate_id,
                score=score.score,
                rank=score.rank,
                reasons=tuple(score.reasons),
            )
            for score in selection.scores
        ),
        pareto_front=tuple(selection.pareto_front),
        frozen_ids=tuple(selection.frozen_ids),
        human_required=selection.human_required,
        metadata_raw_json=dict(selection.metadata),
    )


def validate_human_decision(path: Path) -> HumanDecisionValidationReport:
    """validate_human_decision."""
    errors: list[str] = []
    if not path.exists():
        return HumanDecisionValidationReport(
            passed=False,
            errors=("missing_human_decision",),
            payload=None,
        )
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        return HumanDecisionValidationReport(
            passed=False,
            errors=("invalid_human_decision_payload",),
            payload=None,
        )
    required_fields = {"status", "approved_ids", "rejected_ids", "notes", "signature"}
    missing = required_fields - set(payload.keys())
    if missing:
        errors.append(f"missing_fields:{','.join(sorted(missing))}")
    status = payload.get("status")
    if status not in {"approved", "rejected"}:
        errors.append("decision_not_finalized")
    signature = payload.get("signature")
    if not signature:
        errors.append("missing_signature")
    else:
        expected = _sign_payload(payload)
        if signature != expected:
            errors.append("signature_mismatch")
    decision_payload = HumanDecisionPayload.model_validate(payload)
    return HumanDecisionValidationReport(
        passed=not errors,
        errors=tuple(errors),
        payload=decision_payload,
    )


def _sign_payload(payload: Mapping[str, Any]) -> str:
    """_sign_payload."""
    normalized = {k: v for k, v in payload.items() if k != "signature"}
    blob = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return sha256_hex(blob)


def _load_run(path: Path) -> Mapping[str, Any]:
    """_load_run."""
    if path.is_file():
        target = path
    else:
        workspace = _workspace_for_dir(path)
        target = workspace.run_output_path if workspace else path / "run_output.json"
    payload = json.loads(target.read_text())
    return dict(payload) if isinstance(payload, dict) else {}


def _load_analysis(path: Path) -> Mapping[str, Any]:
    """_load_analysis."""
    if path.is_file():
        target = path
    else:
        workspace = _workspace_for_dir(path)
        target = workspace.analysis_path if workspace else path / "analysis.json"
    if not target.exists():
        return {}
    payload = json.loads(target.read_text())
    return dict(payload) if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """_write_json."""
    write_json_atomic(path, dict(payload))


def _workspace_for_dir(path: Path) -> RunWorkspace | None:
    """_workspace_for_dir."""
    if path.is_dir() and path.parent.name == "artifacts":
        return RunWorkspace.for_run(path.parent.parent, path.name)
    return None
