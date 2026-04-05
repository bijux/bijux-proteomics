# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from agentic_proteins.core.failures import FailureType
from agentic_proteins.runtime import RunManager
from agentic_proteins.runtime.infra import RunConfig


def test_strict_mode_blocks_defaults(tmp_path: Path) -> None:
    config = RunConfig(strict_mode=True)
    manager = RunManager(tmp_path, config)
    result = manager.run("ACDE")
    assert result["status"] == "failure"


def test_incompatible_tool_combo(tmp_path: Path) -> None:
    config = RunConfig(predictors_enabled=["local_esmfold"], resource_limits={"gpu_seconds": 0.0})
    manager = RunManager(tmp_path, config)
    result = manager.run("ACDE")
    assert result["failure_type"] == FailureType.CAPABILITY_MISSING.value
