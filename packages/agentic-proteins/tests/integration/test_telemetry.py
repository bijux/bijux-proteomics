# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from agentic_proteins.runtime import RunManager
from agentic_proteins.runtime.infra import RunConfig


def test_telemetry_is_complete(tmp_path: Path) -> None:
    manager = RunManager(tmp_path, RunConfig(dry_run=True, logging_enabled=False))
    result = manager.run("ACDE")
    run_id = result["run_id"]
    telemetry_path = tmp_path / "artifacts" / run_id / "telemetry.json"
    payload = json.loads(telemetry_path.read_text())
    assert "run_start" in payload["events"]
    assert "run_total_ms" in payload["timers"]
    for name in ("tool_units", "cpu_seconds", "gpu_seconds"):
        assert name in payload["cost"]
