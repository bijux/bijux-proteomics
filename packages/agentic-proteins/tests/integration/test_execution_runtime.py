from __future__ import annotations

import time
from typing import Iterator

import pytest

from agentic_proteins.core.tooling import InvocationInput, ToolInvocationSpec, ToolResult
from agentic_proteins.core.execution import ExecutionTask
from agentic_proteins.execution.compiler.boundary import ToolBoundary, evaluate_failure
from agentic_proteins.execution.runtime.executor import LocalExecutor
from agentic_proteins.tools.base import Tool


class _DummyTool(Tool):
    name = "dummy"
    version = "v1"

    def run(self, invocation_id: str, inputs: list[InvocationInput]) -> ToolResult:
        return ToolResult(
            invocation_id=invocation_id,
            tool_name=self.name,
            status="success",
            outputs=[],
            metrics=[],
            error=None,
        )


def _task(timeout_ms: int = 0) -> ExecutionTask:
    invocation = ToolInvocationSpec(
        invocation_id="inv-1",
        tool_name="dummy",
        tool_version="v1",
        inputs=[],
        expected_outputs=[],
        constraints=[],
        origin_task_id="task-1",
    )
    return ExecutionTask(
        task_id="task-1",
        tool_invocation=invocation,
        input_state_id="state-1",
        expected_output_schema="schema-1",
        timeout_ms=timeout_ms,
    )


def _time_sequence(values: list[float]) -> Iterator[float]:
    for value in values:
        yield value
    while True:
        yield values[-1]


def test_local_executor_timeout_before_start(monkeypatch: pytest.MonkeyPatch) -> None:
    seq = _time_sequence([0.0, 2.0, 2.1])
    monkeypatch.setattr(time, "time", lambda: next(seq))
    executor = LocalExecutor()
    result = executor.run(_task(timeout_ms=1000), context=None)  # type: ignore[arg-type]
    assert result.error
    assert result.error.error_type == "timeout"


def test_local_executor_no_boundary() -> None:
    executor = LocalExecutor()
    result = executor.run(_task(), context=None)  # type: ignore[arg-type]
    assert result.error
    assert result.error.error_type == "no_boundary"


def test_local_executor_timeout_after_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    seq = _time_sequence([0.0, 0.0, 2.0, 2.1])
    monkeypatch.setattr(time, "time", lambda: next(seq))
    boundary = ToolBoundary({("dummy", "v1"): _DummyTool()})
    executor = LocalExecutor(boundary=boundary)
    result = executor.run(_task(timeout_ms=1000), context=None)  # type: ignore[arg-type]
    assert result.error
    assert result.error.error_type == "timeout"


def test_tool_boundary_and_failure_evaluation() -> None:
    boundary = ToolBoundary({("dummy", "v1"): _DummyTool()})
    result = boundary.execute(
        ToolInvocationSpec(
            invocation_id="inv-2",
            tool_name="dummy",
            tool_version="v1",
            inputs=[],
            expected_outputs=[],
            constraints=[],
            origin_task_id="task-2",
        )
    )
    assert result.status == "success"
    decision = evaluate_failure(result, fatal_errors={"fatal"}, replan_errors={"retry"})
    assert decision == "continue"

    missing = boundary.execute(
        ToolInvocationSpec(
            invocation_id="inv-3",
            tool_name="missing",
            tool_version="v1",
            inputs=[],
            expected_outputs=[],
            constraints=[],
            origin_task_id="task-3",
        )
    )
    assert missing.status == "failure"
    assert missing.error
    assert missing.error.error_type == "missing_tool"
