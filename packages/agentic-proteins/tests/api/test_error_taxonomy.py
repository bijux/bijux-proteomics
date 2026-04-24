# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient
import pytest

from agentic_proteins.api import AppConfig, create_app
from agentic_proteins.api import errors as api_errors


def _write_summary(base_dir: Path, run_id: str, workflow_state: str) -> None:
    run_dir = base_dir / "artifacts" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    summary: dict[str, Any] = {
        "run_id": run_id,
        "candidate_id": f"{run_id}-c0",
        "command": "run",
        "execution_status": "completed",
        "workflow_state": workflow_state,
        "outcome": "accepted",
        "provider": "heuristic_proxy",
        "tool_status": "success",
        "qc_status": "acceptable",
        "artifacts_dir": str(run_dir),
        "warnings": [],
        "failure": None,
        "version": {"app": "0.1.0", "git_commit": "unknown", "tool_versions": {}},
    }
    (run_dir / "run_summary.json").write_text(json.dumps(summary))


@pytest.mark.parametrize(
    ("method", "path", "payload", "expected_status"),
    [
        ("post", "/api/v1/run", {}, 422),
        ("get", "/api/v1/inspect/missing", None, 404),
        ("post", "/api/v1/resume", {"run_id": "run-123"}, 409),
        ("get", "/api/v1/run", None, 405),
        ("post", "/api/v1/run", {"sequence": "ACDE"}, 500),
    ],
)
def test_api_error_taxonomy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    method: str,
    path: str,
    payload: dict[str, Any] | None,
    expected_status: int,
) -> None:
    app = create_app(AppConfig(base_dir=tmp_path, docs_enabled=False))
    if expected_status == 409:
        _write_summary(tmp_path, "run-123", "done")
    if expected_status == 500:
        from agentic_proteins.api.v1.endpoints import run as run_endpoint

        def _boom(*_args: object, **_kwargs: object) -> object:
            raise KeyError("boom")

        monkeypatch.setattr(run_endpoint, "_run_sequence", _boom)
    client = TestClient(app)
    func = getattr(client, method)
    response = func(path, json=payload) if payload is not None else func(path)
    assert response.status_code == expected_status
    payload_json = response.json()
    assert payload_json["status"] == "error"
    error = payload_json["error"]
    allowed = {
        *api_errors._ERROR_TYPES.values(),
        api_errors._METHOD_NOT_ALLOWED_TYPE,
        api_errors._BAD_REQUEST_TYPE,
    }
    assert error["type"] in allowed
    assert "Traceback" not in error["detail"]
