# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from agentic_proteins.interfaces.http import AppConfig, create_app
from bijux_proteomics_foundation.testing.skip_policy import (
    SkipCategory,
    import_or_skip,
)
from bijux_proteomics_runtime.api import AppConfig as RuntimeAppConfig
from bijux_proteomics_runtime.api import create_app as runtime_create_app

fastapi_testclient = import_or_skip(
    "fastapi.testclient",
    category=SkipCategory.OPTIONAL_DEPENDENCY,
    reason="httpx is required for the compatibility http interface surface",
)
TestClient = fastapi_testclient.TestClient


def test_http_app_factory_matches_runtime_routes(tmp_path: Path) -> None:
    compat_app = create_app(AppConfig(base_dir=tmp_path, docs_enabled=False))
    runtime_app = runtime_create_app(
        RuntimeAppConfig(base_dir=tmp_path, docs_enabled=False)
    )
    compat_paths = sorted(getattr(route, "path", "") for route in compat_app.routes)
    runtime_paths = sorted(getattr(route, "path", "") for route in runtime_app.routes)
    assert compat_paths == runtime_paths


def test_http_health_surface_stays_available(tmp_path: Path) -> None:
    client = TestClient(create_app(AppConfig(base_dir=tmp_path, docs_enabled=False)))
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["data"]["status"] == "ok"
