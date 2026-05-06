# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime.support.primitives.failures import FailureType
from agentic_proteins.orchestration.manager import RunManager
from agentic_proteins.orchestration.run_config import RunConfig


def test_tool_disabled_behaves_like_removal(tmp_path: Path) -> None:
    config = RunConfig(
        predictors_enabled=["nonexistent_tool"],
        resource_limits={"gpu_seconds": 0.0, "cpu_seconds": 0.0},
    )
    manager = RunManager(tmp_path, config)
    result = manager.run("ACDE")
    assert result["failure_type"] == FailureType.CAPABILITY_MISSING.value
