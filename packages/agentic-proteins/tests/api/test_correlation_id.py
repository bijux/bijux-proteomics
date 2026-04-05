# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from agentic_proteins.api import AppConfig, create_app


def test_correlation_id_in_logs(tmp_path: Path) -> None:
    app = create_app(AppConfig(base_dir=tmp_path, docs_enabled=False))
    client = TestClient(app)
    request_id = "corr-test-123"
    response = client.get("/api/v1/health", headers={"x-request-id": request_id})
    assert response.status_code == 200

    log_path = tmp_path / "artifacts" / "api" / "requests.jsonl"
    assert log_path.exists()
    lines = [json.loads(line) for line in log_path.read_text().splitlines() if line]
    assert lines
    assert all(line.get("correlation_id") == request_id for line in lines)
