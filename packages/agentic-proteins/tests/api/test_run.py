# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from typing import Any

import pytest
from click.testing import CliRunner
from fastapi.testclient import TestClient

from agentic_proteins.api import AppConfig, create_app
from agentic_proteins.interfaces import cli as cli_module
from agentic_proteins.interfaces.cli import cli
from agentic_proteins.api.v1.endpoints import run as run_endpoint

pytestmark = pytest.mark.api


def _run_summary(workflow_state: str = "done") -> dict[str, Any]:
    return {
        "run_id": "run-123",
        "candidate_id": "run-123-c0",
        "command": "run",
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


def _strip_timestamps(payload: Any) -> Any:
    if isinstance(payload, dict):
        cleaned = {}
        for key, value in payload.items():
            if "timestamp" in key or key.endswith("_at"):
                continue
            cleaned[key] = _strip_timestamps(value)
        return cleaned
    if isinstance(payload, list):
        return [_strip_timestamps(item) for item in payload]
    return payload


def test_run_endpoint_returns_summary(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    summary = _run_summary()

    monkeypatch.setattr(run_endpoint, "_read_sequence", lambda *_: "ACDE")
    monkeypatch.setattr(run_endpoint, "_validate_sequence", lambda *_: None)
    monkeypatch.setattr(run_endpoint, "_build_run_config", lambda *_: object())
    monkeypatch.setattr(run_endpoint, "_run_sequence", lambda *_: {"run_id": "run-123"})
    monkeypatch.setattr(run_endpoint, "_load_run_summary", lambda *_: summary)

    client = TestClient(create_app(AppConfig(base_dir=tmp_path)))
    response = client.post("/api/v1/run", json={"sequence": "ACDE"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["data"] == summary
    assert payload["error"] is None


def test_run_endpoint_human_review(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    summary = _run_summary(workflow_state="awaiting_human_review")

    monkeypatch.setattr(run_endpoint, "_read_sequence", lambda *_: "ACDE")
    monkeypatch.setattr(run_endpoint, "_validate_sequence", lambda *_: None)
    monkeypatch.setattr(run_endpoint, "_build_run_config", lambda *_: object())
    monkeypatch.setattr(run_endpoint, "_run_sequence", lambda *_: {"run_id": "run-123"})
    monkeypatch.setattr(run_endpoint, "_load_run_summary", lambda *_: summary)

    client = TestClient(create_app(AppConfig(base_dir=tmp_path)))
    response = client.post("/api/v1/run", json={"sequence": "ACDE"})

    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["data"] == summary
    assert payload["error"] is None


def test_cli_api_parity(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    summary = _run_summary()

    class _RunOutput:
        def __init__(self, run_id: str) -> None:
            self.run_id = run_id

    monkeypatch.setattr(cli_module, "_read_sequence", lambda *_: "ACDE")
    monkeypatch.setattr(cli_module, "_validate_sequence", lambda *_: None)
    monkeypatch.setattr(cli_module, "_build_run_config", lambda *_: object())
    monkeypatch.setattr(cli_module, "_run_sequence", lambda *_: {"run_id": "run-123"})
    monkeypatch.setattr(cli_module, "_load_run_summary", lambda *_: summary)
    monkeypatch.setattr(
        cli_module.RunOutput, "model_validate", lambda *_: _RunOutput("run-123")
    )

    monkeypatch.setattr(run_endpoint, "_read_sequence", lambda *_: "ACDE")
    monkeypatch.setattr(run_endpoint, "_validate_sequence", lambda *_: None)
    monkeypatch.setattr(run_endpoint, "_build_run_config", lambda *_: object())
    monkeypatch.setattr(run_endpoint, "_run_sequence", lambda *_: {"run_id": "run-123"})
    monkeypatch.setattr(run_endpoint, "_load_run_summary", lambda *_: summary)

    client = TestClient(create_app(AppConfig(base_dir=tmp_path)))
    api_response = client.post("/api/v1/run", json={"sequence": "ACDE"})
    api_payload = api_response.json()["data"]

    runner = CliRunner()
    result = runner.invoke(cli, ["run", "--sequence", "ACDE", "--json"])
    assert result.exit_code == 0
    cli_payload = json.loads(result.output)

    assert _strip_timestamps(cli_payload) == _strip_timestamps(api_payload)
