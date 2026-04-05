# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentic_proteins.core.failures import FailureType
from agentic_proteins.core.tooling import ToolError
from agentic_proteins.domain.candidates.model import Candidate
from agentic_proteins.runtime.context import create_run_context
from agentic_proteins.runtime.control import artifacts as artifacts_module
from agentic_proteins.runtime.workspace import RunWorkspace


def _candidate(candidate_id: str, score: float) -> Candidate:
    return Candidate(
        candidate_id=candidate_id,
        sequence="ACDE",
        metrics={"mean_plddt": score, "novelty": 0.2},
    )


def test_map_failure_type_variants() -> None:
    err = ToolError(error_type="timeout", message="boom")
    assert (
        artifacts_module.map_failure_type("failure", err)
        == FailureType.TOOL_TIMEOUT.value
    )
    err = ToolError(error_type="oom", message="boom")
    assert (
        artifacts_module.map_failure_type("failure", err) == FailureType.OOM.value
    )
    err = ToolError(error_type="invalid_output", message="boom")
    assert (
        artifacts_module.map_failure_type("failure", err)
        == FailureType.INVALID_OUTPUT.value
    )
    err = ToolError(error_type="tool_error", message="boom")
    assert (
        artifacts_module.map_failure_type("failure", err) == FailureType.TOOL_CRASH.value
    )
    assert artifacts_module.map_failure_type("success", None) == ""


def test_write_and_load_artifact(tmp_path: Path) -> None:
    workspace = RunWorkspace.for_run(tmp_path, "run-1")
    workspace.ensure_layout({})
    metadata = artifacts_module.write_artifact(
        workspace, kind="analysis", payload={"a": 1}
    )
    payload = artifacts_module.load_artifact(workspace, metadata.artifact_id)
    assert payload == {"a": 1}


def test_write_failure_artifacts(tmp_path: Path) -> None:
    run_context, _warnings = create_run_context(tmp_path)
    artifacts_module.write_failure_artifacts(
        run_context,
        FailureType.INVALID_OUTPUT,
        {"detail": "bad"},
    )
    payload = json.loads(run_context.workspace.error_path.read_text())
    assert payload["failure_type"] == FailureType.INVALID_OUTPUT.value
    assert payload["details"]["detail"] == "bad"


def test_execution_and_telemetry_snapshots(tmp_path: Path) -> None:
    run_context, _warnings = create_run_context(tmp_path)
    snapshots = artifacts_module.ExecutionSnapshots(
        run_context.workspace.execution_snapshots_path
    )
    snapshots.record(0, state={"ok": True}, decisions=[], tool_outputs=[])
    snapshots.write()
    data = json.loads(run_context.workspace.execution_snapshots_path.read_text())
    assert data[0]["iteration_index"] == 0
    hooks = artifacts_module.TelemetryHooks(run_context)
    hooks.record_snapshot("agent", 1, {"signal": "x"})
    hooks.record_execution_snapshot(1, state={}, decisions=[], tool_outputs=[])
    hooks.finalize()
    telemetry = json.loads(run_context.workspace.telemetry_snapshots_path.read_text())
    assert telemetry[0]["agent"] == "agent"


def test_compare_runs_and_analysis(tmp_path: Path) -> None:
    run_a = RunWorkspace.for_run(tmp_path, "run-a")
    run_b = RunWorkspace.for_run(tmp_path, "run-b")
    run_a.run_dir.mkdir(parents=True)
    run_b.run_dir.mkdir(parents=True)
    run_a.run_output_path.write_text(json.dumps({"run_id": "run-a"}))
    run_b.run_output_path.write_text(json.dumps({"run_id": "run-b"}))
    run_a.analysis_path.write_text(json.dumps({"candidate_timeline": {"a": []}}))
    run_b.analysis_path.write_text(json.dumps({"candidate_timeline": {"b": []}}))
    result = artifacts_module.compare_runs(run_a.run_dir, run_b.run_dir)
    assert result["run_ids"]["run_a"] == "run-a"
    assert result["candidate_trajectories"]["run_b"] == {"b": []}


def test_human_decision_flow(tmp_path: Path) -> None:
    workspace = RunWorkspace.for_run(tmp_path, "run-1")
    workspace.ensure_layout({})
    selection = artifacts_module.require_human_decision(
        [_candidate("c1", 60.0), _candidate("c2", 80.0)],
        workspace,
        top_n=1,
    )
    payload = json.loads(workspace.candidate_selection_path.read_text())
    assert payload["metadata"]["top_n"] == 1
    assert selection.frozen_ids
    ok, errors, _ = artifacts_module.validate_human_decision(
        workspace.human_decision_path
    )
    assert ok is False
    assert "decision_not_finalized" in errors


def test_validate_human_decision_edge_cases(tmp_path: Path) -> None:
    path = tmp_path / "missing.json"
    ok, errors, _payload = artifacts_module.validate_human_decision(path)
    assert ok is False
    assert "missing_human_decision" in errors
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"status": "pending"}))
    ok, errors, _payload = artifacts_module.validate_human_decision(bad)
    assert ok is False
    assert any(item.startswith("missing_fields") for item in errors)
    payload = {
        "status": "approved",
        "approved_ids": ["c1"],
        "rejected_ids": [],
        "notes": "",
        "signature": "",
    }
    payload["signature"] = artifacts_module._sign_payload(payload)
    good = tmp_path / "good.json"
    good.write_text(json.dumps(payload))
    ok, errors, _payload = artifacts_module.validate_human_decision(good)
    assert ok is True
    assert errors == []
