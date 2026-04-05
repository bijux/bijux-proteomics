# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from agentic_proteins.api import AppConfig, create_app
from agentic_proteins.api.v1.endpoints import resume as resume_endpoint

pytestmark = pytest.mark.api


def _run_summary(workflow_state: str = "paused") -> dict[str, Any]:
    return {
        "run_id": "run-123",
        "candidate_id": "run-123-c0",
        "command": "resume",
        "execution_status": "completed",
        "workflow_state": workflow_state,
        "outcome": "accepted",
        "provider": "heuristic_proxy",
        "tool_status": "success",
        "qc_status": "acceptable",
        "artifacts_dir": "artifacts/run-123",
        "warnings": [],
        "failure": None,
        "version": {
            "app": "0.1.0",
            "git_commit": "abc123",
            "tool_versions": {},
        },
    }


def test_resume_by_run_id(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    summary = _run_summary()
    summaries = [summary, summary]

    monkeypatch.setattr(resume_endpoint, "_resume_candidate", lambda *_: {"run_id": "run-123"})
    monkeypatch.setattr(resume_endpoint, "_load_run_summary", lambda *_: summaries.pop(0))

    client = TestClient(create_app(AppConfig(base_dir=tmp_path)))
    response = client.post("/api/v1/resume", json={"run_id": "run-123"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["data"] == summary
    assert payload["error"] is None


def test_resume_done_conflict(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    summary = _run_summary(workflow_state="done")

    monkeypatch.setattr(resume_endpoint, "_load_run_summary", lambda *_: summary)

    client = TestClient(create_app(AppConfig(base_dir=tmp_path)))
    response = client.post("/api/v1/resume", json={"run_id": "run-123"})

    assert response.status_code == 409
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error"]["title"] == "Conflict"
    assert payload["error"]["status"] == 409
