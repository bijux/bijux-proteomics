from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentic_proteins.runtime.infra.telemetry import TelemetryClient


def test_telemetry_client_records_and_flushes(tmp_path: Path) -> None:
    path = tmp_path / "telemetry.json"
    telemetry = TelemetryClient(run_id="run-1", metrics_path=path)
    telemetry.record_event("run_start")
    telemetry.observe("run_total_ms", 1.0)
    telemetry.add_cost("tool_units", 0.0)
    telemetry.add_cost("cpu_seconds", 0.0)
    telemetry.add_cost("gpu_seconds", 0.0)
    telemetry.increment("counter", 2.0)
    telemetry.set_gauge("gauge", 3.0)
    telemetry.flush()

    payload = json.loads(path.read_text())
    assert payload["run_id"] == "run-1"
    assert payload["event_count"] == 1


def test_telemetry_client_requires_fields(tmp_path: Path) -> None:
    telemetry = TelemetryClient(run_id="run-1", metrics_path=tmp_path / "x.json")
    with pytest.raises(ValueError, match="Missing telemetry fields"):
        telemetry.flush()
