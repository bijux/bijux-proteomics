# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Planning compiler."""

from __future__ import annotations

from bijux_proteomics_runtime.agents.planning.schemas import Plan
from bijux_proteomics_runtime.agents.planning.validation import validate_plan
from bijux_proteomics_runtime.core.decisions import Decision
from bijux_proteomics_runtime.core.execution import (
    ExecutionGraph,
    ExecutionTask,
    RetryPolicy,
)
from bijux_proteomics_runtime.core.tooling import ToolInvocationSpec
from bijux_proteomics_runtime.execution.graph_validation import validate_execution_graph


def compile_plan_to_execution(plan: Plan, decisions: list[Decision]) -> ExecutionGraph:
    """compile_plan_to_execution."""
    validate_plan(plan)
    invocation_map: dict[str, ToolInvocationSpec] = {}
    for decision in decisions:
        for requested_invocation in decision.requested_tools:
            if requested_invocation.origin_task_id not in plan.tasks:
                raise ValueError(
                    f"Tool invocation references unknown task {requested_invocation.origin_task_id}."
                )
            existing = invocation_map.get(requested_invocation.origin_task_id)
            if (
                existing is None
                or requested_invocation.invocation_id < existing.invocation_id
            ):
                invocation_map[requested_invocation.origin_task_id] = (
                    requested_invocation
                )

    tasks: dict[str, ExecutionTask] = {}
    for task_id in sorted(plan.tasks.keys()):
        invocation: ToolInvocationSpec | None = invocation_map.get(task_id)
        if invocation is None:
            raise ValueError(f"Missing tool invocation for task {task_id}.")
        tasks[task_id] = ExecutionTask(
            task_id=task_id,
            tool_invocation=invocation,
            input_state_id="state-0",
            expected_output_schema="tool_output",
            retry_policy=RetryPolicy(),
            timeout_ms=0,
        )

    graph = ExecutionGraph(
        tasks=tasks,
        dependencies={k: plan.dependencies.get(k, []) for k in tasks},
        entry_tasks=[t for t in plan.entry_tasks if t in tasks],
        exit_conditions=list(plan.exit_conditions),
    )
    validate_execution_graph(graph)
    return graph
