# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import importlib

from agentic_proteins.core.failures import FailureType
from agentic_proteins.runtime import RunManager
from agentic_proteins.runtime.context import RunStatus
from agentic_proteins.runtime.infra import RunConfig
from agentic_proteins.tools.base import Tool
from agentic_proteins.tools.schemas import InvocationInput, ToolError, ToolResult


class TimeoutTool(Tool):
    name = "timeout_tool"
    version = "v1"

    def run(self, invocation_id: str, inputs: list[InvocationInput]) -> ToolResult:
        return ToolResult(
            invocation_id=invocation_id,
            tool_name=self.name,
            status="failure",
            outputs=[],
            metrics=[],
            error=ToolError(error_type="timeout", message="timeout"),
        )


class CorruptOutputTool(Tool):
    name = "corrupt_tool"
    version = "v1"

    def run(self, invocation_id: str, inputs: list[InvocationInput]) -> ToolResult:
        return ToolResult(
            invocation_id=invocation_id,
            tool_name=self.name,
            status="success",
            outputs=[InvocationInput(name="sequence_length", value="4")],
            metrics=[],
            error=None,
        )


def test_invalid_sequence_rejected(tmp_path: Path) -> None:
    manager = RunManager(tmp_path)
    result = manager.run("ZZZ")
    assert result["failure_type"] == FailureType.INPUT_INVALID.value
    run_dir = tmp_path / "artifacts" / result["run_id"]
    assert (run_dir / "error.json").exists()


def test_tool_timeout_maps_failure(tmp_path: Path) -> None:
    config = RunConfig(predictors_enabled=["timeout_tool"], resource_limits={"gpu_seconds": 0.0, "cpu_seconds": 0.0})
    manager = RunManager(tmp_path, config)
    result = manager.run("ACDE", tool=TimeoutTool())
    assert result["failure_type"] == FailureType.TOOL_TIMEOUT.value
    run_dir = tmp_path / "artifacts" / result["run_id"]
    assert (run_dir / "error.json").exists()


def test_corrupt_output_maps_failure(tmp_path: Path) -> None:
    config = RunConfig(predictors_enabled=["corrupt_tool"], resource_limits={"gpu_seconds": 0.0, "cpu_seconds": 0.0})
    manager = RunManager(tmp_path, config)
    result = manager.run("ACDE", tool=CorruptOutputTool())
    assert result["failure_type"] == FailureType.INVALID_OUTPUT.value
    run_dir = tmp_path / "artifacts" / result["run_id"]
    assert (run_dir / "error.json").exists()


def test_invalid_plan_maps_failure(tmp_path: Path, monkeypatch) -> None:
    class _InvalidPlan:
        tasks: dict = {}
        dependencies: dict = {}
        entry_tasks: list = []
        exit_conditions: list = []

        def model_dump(self, mode: str | None = None) -> dict:
            return {
                "tasks": {},
                "dependencies": {},
                "entry_tasks": [],
                "exit_conditions": [],
            }

    class _PlannerOutput:
        def __init__(self) -> None:
            self.plan = _InvalidPlan()

    def _bad_plan(_self, _payload):
        return _PlannerOutput()

    planner_mod = importlib.import_module("agentic_proteins.agents.planning.planner")
    monkeypatch.setattr(planner_mod.PlannerAgent, "decide", _bad_plan)
    manager = RunManager(tmp_path)
    result = manager.run("ACDE")
    assert result["failure_type"] == FailureType.INVALID_PLAN.value
    run_dir = tmp_path / "artifacts" / result["run_id"]
    assert (run_dir / "error.json").exists()


def test_human_decision_missing_maps_failure(tmp_path: Path) -> None:
    config = RunConfig(require_human_decision=True)
    manager = RunManager(tmp_path, config)
    result = manager.run("ACDE")
    assert result["failure_type"] == FailureType.NONE.value
    assert result["status"] == RunStatus.PARTIAL.value
    run_dir = tmp_path / "artifacts" / result["run_id"]
    assert (run_dir / "human_decision.json").exists()
