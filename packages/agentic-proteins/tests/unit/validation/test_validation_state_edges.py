# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from agentic_proteins.core.execution import ExecutionGraph, ExecutionTask
from agentic_proteins.core.tooling import ToolInvocationSpec
from agentic_proteins.validation import state as state_module


def _task(task_id: str) -> ExecutionTask:
    return ExecutionTask(
        task_id=task_id,
        tool_invocation=ToolInvocationSpec(
            invocation_id=f"inv-{task_id}",
            tool_name="heuristic_proxy",
            tool_version="1.0",
            inputs=[],
            expected_outputs=[],
            constraints=[],
            origin_task_id="origin",
        ),
        input_state_id="state-1",
        expected_output_schema="schema",
    )


def test_validate_execution_graph_rejects_empty() -> None:
    graph = ExecutionGraph(tasks={}, dependencies={}, entry_tasks=[])
    with pytest.raises(ValueError, match="at least one task"):
        state_module.validate_execution_graph(graph)


def test_validate_execution_graph_rejects_unknown_dependency() -> None:
    task = _task("t1")
    graph = ExecutionGraph(
        tasks={"t1": task},
        dependencies={"t1": ["missing"]},
        entry_tasks=["t1"],
    )
    with pytest.raises(ValueError, match="Unknown execution dependency"):
        state_module.validate_execution_graph(graph)
