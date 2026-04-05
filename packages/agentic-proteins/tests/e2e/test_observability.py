# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from agentic_proteins.runtime import RunManager


def test_observability_artifacts_exist(tmp_path: Path) -> None:
    sequence = "ACDEFGHIK"
    manager = RunManager(tmp_path)
    result = manager.run(sequence)

    run_dir = Path(tmp_path) / "artifacts" / result["run_id"]
    log_path = run_dir / "logs" / "run.jsonl"
    metrics_path = run_dir / "telemetry.json"

    assert log_path.exists()
    assert metrics_path.exists()

    metrics = json.loads(metrics_path.read_text())
    assert metrics["event_count"] >= 2
