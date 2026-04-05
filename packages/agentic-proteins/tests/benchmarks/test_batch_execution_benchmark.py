# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter

from agentic_proteins.runtime import RunManager
from agentic_proteins.runtime.infra import RunConfig


def test_batch_execution_regression(tmp_path: Path) -> None:
    baseline_path = Path(__file__).parent / "baseline.json"
    baseline = json.loads(baseline_path.read_text())
    baseline_seconds = float(baseline["batch_execution_seconds"])

    sequence = "ACDEFGHIK"
    manager = RunManager(tmp_path, RunConfig(seed=11))
    start = perf_counter()
    manager.run(sequence)
    duration = perf_counter() - start

    assert duration <= baseline_seconds * 1.15
