# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Artifact writing and inspection helpers for runtime control."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from agentic_proteins.core.failures import FailureType, suggest_next_action
from agentic_proteins.core.hashing import sha256_hex
from agentic_proteins.domain.candidates.model import Candidate
from agentic_proteins.domain.candidates.selection import (
    CandidateSelection,
    select_candidates,
)
from agentic_proteins.runtime.context import RunContext
from agentic_proteins.runtime.workspace import (
    RunWorkspace,
    write_json_atomic,
    write_text_atomic,
)
from agentic_proteins.state.schemas import ArtifactMetadata


def map_failure_type(status: str, error) -> str:
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
    run_context: RunContext, failure_type: FailureType, details: dict
) -> None:
    """write_failure_artifacts."""
    payload = {
        "failure_type": failure_type.value,
        "details": details,
        "next_action": suggest_next_action(failure_type),
    }
    write_json_atomic(run_context.workspace.error_path, payload)


def write_artifact(
    workspace: RunWorkspace,
    kind: str,
    payload: dict[str, Any],
    description: str = "",
    tags: list[str] | None = None,
) -> ArtifactMetadata:
    """write_artifact."""
    tags = tags or []
    if not description:
        description = "unspecified"
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    artifact_id = sha256_hex(f"{kind}:{normalized}")
    path = workspace.artifact_items_dir / f"{artifact_id}.json"
    write_json_atomic(path, payload)
    return ArtifactMetadata(
        artifact_id=artifact_id,
        kind=kind,
        description=description,
        tags=tags,
    )


def load_artifact(workspace: RunWorkspace, artifact_id: str) -> dict[str, Any]:
    """load_artifact."""
    path = workspace.artifact_items_dir / f"{artifact_id}.json"
    return json.loads(path.read_text())


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
        state: dict,
        decisions: list[dict],
        tool_outputs: list[dict],
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


def compare_runs(run_a: Path, run_b: Path) -> dict[str, Any]:
    """compare_runs."""
    data_a = _load_run(run_a)
    data_b = _load_run(run_b)
    analysis_a = _load_analysis(run_a)
    analysis_b = _load_analysis(run_b)

    return {
        "run_ids": {
            "run_a": data_a.get("run_id"),
            "run_b": data_b.get("run_id"),
        },
        "final_outcome": {
            "run_a": {
                "tool_status": data_a.get("tool_status"),
                "qc_status": data_a.get("qc_status"),
                "failure_type": data_a.get("failure_type"),
                "coordinator_decision": data_a.get("coordinator_decision"),
            },
            "run_b": {
                "tool_status": data_b.get("tool_status"),
                "qc_status": data_b.get("qc_status"),
                "failure_type": data_b.get("failure_type"),
                "coordinator_decision": data_b.get("coordinator_decision"),
            },
        },
        "candidate_trajectories": {
            "run_a": analysis_a.get("candidate_timeline", {}),
            "run_b": analysis_b.get("candidate_timeline", {}),
        },
        "iteration_deltas": {
            "run_a": analysis_a.get("iteration_deltas", []),
            "run_b": analysis_b.get("iteration_deltas", []),
        },
    }


def require_human_decision(
    candidates: list[Candidate],
    workspace: RunWorkspace,
    top_n: int = 3,
) -> CandidateSelection:
    """require_human_decision."""
    selection = select_candidates(candidates, top_n=top_n)
    _write_json(workspace.candidate_selection_path, selection_as_dict(selection))
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


def selection_as_dict(selection: CandidateSelection) -> dict[str, Any]:
    """selection_as_dict."""
    return {
        "scores": [score.__dict__ for score in selection.scores],
        "pareto_front": selection.pareto_front,
        "frozen_ids": selection.frozen_ids,
        "human_required": selection.human_required,
        "metadata": selection.metadata,
    }


def validate_human_decision(path: Path) -> tuple[bool, list[str], dict[str, Any]]:
    """validate_human_decision."""
    errors: list[str] = []
    if not path.exists():
        return False, ["missing_human_decision"], {}
    payload = json.loads(path.read_text())
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
    return len(errors) == 0, errors, payload


def _sign_payload(payload: dict[str, Any]) -> str:
    """_sign_payload."""
    normalized = {k: v for k, v in payload.items() if k != "signature"}
    blob = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return sha256_hex(blob)


def _load_run(path: Path) -> dict[str, Any]:
    """_load_run."""
    if path.is_file():
        target = path
    else:
        workspace = _workspace_for_dir(path)
        target = workspace.run_output_path if workspace else path / "run_output.json"
    return json.loads(target.read_text())


def _load_analysis(path: Path) -> dict[str, Any]:
    """_load_analysis."""
    if path.is_file():
        target = path
    else:
        workspace = _workspace_for_dir(path)
        target = workspace.analysis_path if workspace else path / "analysis.json"
    if not target.exists():
        return {}
    return json.loads(target.read_text())


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    """_write_json."""
    write_json_atomic(path, payload)


def _workspace_for_dir(path: Path) -> RunWorkspace | None:
    """_workspace_for_dir."""
    if path.is_dir() and path.parent.name == "artifacts":
        return RunWorkspace.for_run(path.parent.parent, path.name)
    return None
