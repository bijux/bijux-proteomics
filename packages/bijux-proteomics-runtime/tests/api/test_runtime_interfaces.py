from __future__ import annotations

from click.testing import CliRunner

from bijux_proteomics_foundation.testing.skip_policy import (
    SkipCategory,
    import_or_skip,
)
from bijux_proteomics_runtime.api.app import app
from bijux_proteomics_runtime.api.cli import cli

fastapi_testclient = import_or_skip(
    "fastapi.testclient",
    category=SkipCategory.OPTIONAL_DEPENDENCY,
    reason="httpx is required for the runtime fastapi interface surface",
)
TestClient = fastapi_testclient.TestClient


def test_runtime_cli_identity_command() -> None:
    result = CliRunner().invoke(cli, ["identity"])
    assert result.exit_code == 0
    assert "bijux-proteomics-runtime canonical runtime surface" in result.output


def test_runtime_api_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/health", headers={"x-request-id": "req-health-1"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["meta"]["request_id"] == "req-health-1"
    assert payload["meta"]["trace_id"]
    assert response.headers["x-request-id"] == "req-health-1"
    assert response.headers["x-trace-id"]
    assert (
        payload["data"]["runtime"]
        == "bijux-proteomics-runtime canonical runtime surface"
    )
