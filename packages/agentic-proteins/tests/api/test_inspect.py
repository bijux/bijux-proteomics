# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from agentic_proteins.api import AppConfig, create_app
from agentic_proteins.api.v1.endpoints import inspect as inspect_endpoint
from agentic_proteins.domain.candidates.schema import Candidate

pytestmark = pytest.mark.api


def test_inspect_candidate(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    candidate = Candidate(candidate_id="run-123-c0", sequence="ACDE")

    monkeypatch.setattr(inspect_endpoint, "_inspect_candidate", lambda *_: candidate)

    run_dir = tmp_path / "artifacts" / "run-123"
    run_dir.mkdir(parents=True)
    (run_dir / "run_summary.json").write_text(
        json.dumps({"qc_status": "acceptable"})
    )
    monkeypatch.setattr(
        inspect_endpoint,
        "_load_run_summary",
        lambda *_: {"qc_status": "acceptable"},
    )

    client = TestClient(create_app(AppConfig(base_dir=tmp_path)))
    response = client.get("/api/v1/inspect/run-123-c0")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["data"]["candidate"]["candidate_id"] == "run-123-c0"
    assert payload["data"]["qc_status"] == "acceptable"
    assert payload["data"]["artifacts"]["run_dir"].endswith("artifacts/run-123")
