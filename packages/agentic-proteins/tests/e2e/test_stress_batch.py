# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from agentic_proteins.runtime import RunManager


def test_stress_batch_runs_with_failure(tmp_path: Path) -> None:
    manager = RunManager(tmp_path)
    sequences = ["ACDEFGHIK", "ZZZ", "ACDE"]
    results = [manager.run(seq) for seq in sequences]
    statuses = [result["tool_status"] for result in results]
    assert "failure" in statuses
    assert len(results) == 3
    for result in results:
        run_dir = Path(tmp_path) / "artifacts" / result["run_id"]
        assert run_dir.exists()
        assert (run_dir / "run_summary.json").exists()
