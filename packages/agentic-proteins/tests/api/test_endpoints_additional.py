# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from agentic_proteins.api.app import AppConfig, create_app
from agentic_proteins.api.v1.endpoints import compare as compare_module
from agentic_proteins.api.v1.endpoints import run as run_module
from agentic_proteins.api.v1.endpoints import resume as resume_module


def _client(tmp_path: Path) -> TestClient:
    app = create_app(AppConfig(base_dir=tmp_path))
    return TestClient(app)


def test_compare_endpoint_success(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        compare_module,
        "_compare_runs_payload",
        lambda *_: {
            "run_ids": {"run_a": "a", "run_b": "b"},
            "final_outcome": {"run_a": {}, "run_b": {}},
            "candidate_trajectories": {"run_a": {}, "run_b": {}},
            "iteration_deltas": {"run_a": [], "run_b": []},
        },
    )
    client = _client(tmp_path)
    response = client.post("/api/v1/compare", json={"run_id_a": "a", "run_id_b": "b"})
    assert response.status_code == 200
    assert response.json()["data"]["run_ids"]["run_a"] == "a"


def test_run_endpoint_success_and_review(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(run_module, "_read_sequence", lambda *_: "ACDE")
    monkeypatch.setattr(run_module, "_validate_sequence", lambda *_: None)
    monkeypatch.setattr(run_module, "_build_run_config", lambda *_: object())
    monkeypatch.setattr(run_module, "_run_sequence", lambda *_: {"run_id": "run-1"})
    monkeypatch.setattr(
        run_module,
        "_load_run_summary",
        lambda *_: {
            "run_id": "run-1",
            "candidate_id": "cand-1",
            "command": "run",
            "execution_status": "completed",
            "workflow_state": "running",
            "outcome": "accepted",
            "provider": "heuristic_proxy",
            "tool_status": "success",
            "qc_status": "accept",
            "artifacts_dir": "/tmp/run-1",
            "warnings": [],
            "failure": None,
            "version": {"app": "0.1", "git_commit": "dev", "tool_versions": {}},
        },
    )
    client = _client(tmp_path)
    response = client.post("/api/v1/run", json={"sequence": "ACDE"})
    assert response.status_code == 200
    monkeypatch.setattr(
        run_module,
        "_load_run_summary",
        lambda *_: {
            "run_id": "run-2",
            "candidate_id": "cand-2",
            "command": "run",
            "execution_status": "completed",
            "workflow_state": "awaiting_human_review",
            "outcome": "needs_review",
            "provider": "heuristic_proxy",
            "tool_status": "success",
            "qc_status": "accept",
            "artifacts_dir": "/tmp/run-2",
            "warnings": [],
            "failure": None,
            "version": {"app": "0.1", "git_commit": "dev", "tool_versions": {}},
        },
    )
    response = client.post("/api/v1/run", json={"sequence": "ACDE"})
    assert response.status_code == 202


def test_resume_endpoint_success(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(resume_module, "_resume_candidate", lambda *_: {"run_id": "run-3"})
    monkeypatch.setattr(
        resume_module,
        "_load_run_summary",
        lambda *_: {
            "run_id": "run-3",
            "candidate_id": "cand-3",
            "command": "resume",
            "execution_status": "completed",
            "workflow_state": "running",
            "outcome": "accepted",
            "provider": "heuristic_proxy",
            "tool_status": "success",
            "qc_status": "accept",
            "artifacts_dir": "/tmp/run-3",
            "warnings": [],
            "failure": None,
            "version": {"app": "0.1", "git_commit": "dev", "tool_versions": {}},
        },
    )
    client = _client(tmp_path)
    response = client.post("/api/v1/resume", json={"candidate_id": "cand-3"})
    assert response.status_code == 200
