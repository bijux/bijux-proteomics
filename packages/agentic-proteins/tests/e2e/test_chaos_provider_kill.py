# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from agentic_proteins.runtime import RunManager
from agentic_proteins.runtime.infra import RunConfig
from agentic_proteins.tools.base import Tool
from agentic_proteins.tools.schemas import InvocationInput, ToolResult


class CrashTool(Tool):
    name = "crash_tool"
    version = "v1"

    def run(self, invocation_id: str, inputs: list[InvocationInput]) -> ToolResult:
        raise RuntimeError("provider_killed")


def test_provider_kill_graceful_degradation(tmp_path: Path) -> None:
    config = RunConfig(
        predictors_enabled=["crash_tool"],
        resource_limits={"gpu_seconds": 0.0, "cpu_seconds": 0.0},
    )
    manager = RunManager(tmp_path, config)
    result = manager.run("ACDE", tool=CrashTool())
    run_dir = tmp_path / "artifacts" / result["run_id"]

    assert result["status"] == "failure"
    assert (run_dir / "error.json").exists()
    assert (run_dir / "state.json").exists()
    assert (run_dir / "run_summary.json").exists()
