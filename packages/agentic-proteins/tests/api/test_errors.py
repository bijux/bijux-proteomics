# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from agentic_proteins.api import AppConfig, create_app
from agentic_proteins.api.errors import HumanReviewRequiredError
from agentic_proteins.api.v1.endpoints import inspect as inspect_endpoint
from agentic_proteins.api.v1.endpoints import run as run_endpoint

pytestmark = pytest.mark.api


def test_invalid_input_maps_to_422(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setattr(run_endpoint, "_read_sequence", lambda *_: (_ for _ in ()).throw(ValueError("bad seq")))

    client = TestClient(create_app(AppConfig(base_dir=tmp_path)))
    response = client.post("/api/v1/run", json={"sequence": "ACDE"})

    assert response.status_code == 422
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error"]["title"] == "Validation error"
    assert payload["error"]["status"] == 422


def test_not_found_maps_to_404(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setattr(
        inspect_endpoint,
        "_inspect_candidate",
        lambda *_: (_ for _ in ()).throw(FileNotFoundError("missing")),
    )

    client = TestClient(create_app(AppConfig(base_dir=tmp_path)))
    response = client.get("/api/v1/inspect/missing")

    assert response.status_code == 404
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error"]["title"] == "Not found"
    assert payload["error"]["status"] == 404


def test_human_review_required_maps_to_202(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setattr(
        run_endpoint,
        "_run_sequence",
        lambda *_: (_ for _ in ()).throw(HumanReviewRequiredError("review required")),
    )
    monkeypatch.setattr(run_endpoint, "_read_sequence", lambda *_: "ACDE")
    monkeypatch.setattr(run_endpoint, "_validate_sequence", lambda *_: None)
    monkeypatch.setattr(run_endpoint, "_build_run_config", lambda *_: object())

    client = TestClient(create_app(AppConfig(base_dir=tmp_path)))
    response = client.post("/api/v1/run", json={"sequence": "ACDE"})

    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error"]["title"] == "Human review required"
    assert payload["error"]["status"] == 202
