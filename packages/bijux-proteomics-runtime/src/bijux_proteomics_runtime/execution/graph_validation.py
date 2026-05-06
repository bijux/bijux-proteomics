# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Execution-graph validation for runtime planning."""

from __future__ import annotations

from bijux_proteomics_runtime.support.primitives.execution import ExecutionGraph
from bijux_proteomics_runtime.state.schemas import StateSnapshot

__all__ = ["validate_execution_graph", "validate_state_snapshot"]


def validate_state_snapshot(snapshot: StateSnapshot) -> None:
    """Validate the minimum contract for one state snapshot."""
    if not snapshot.state_id:
        raise ValueError("State snapshot must include a state_id.")
    if not snapshot.plan_fingerprint:
        raise ValueError("State snapshot must include a plan fingerprint.")


def validate_execution_graph(graph: ExecutionGraph) -> None:
    """Validate one execution graph before runtime planning uses it."""
    if not graph.tasks:
        raise ValueError("ExecutionGraph must contain at least one task.")
    task_ids = set(graph.tasks.keys())
    for task_id, deps in graph.dependencies.items():
        if task_id not in task_ids:
            raise ValueError(f"Unknown execution task: {task_id}")
        for dep in deps:
            if dep not in task_ids:
                raise ValueError(f"Unknown execution dependency: {dep}")
    for entry in graph.entry_tasks:
        if entry not in task_ids:
            raise ValueError(f"Unknown execution entry task: {entry}")
    _assert_acyclic(graph, task_ids)


def _assert_acyclic(graph: ExecutionGraph, task_ids: set[str]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visited:
            return
        if node in visiting:
            raise ValueError("ExecutionGraph contains a cycle.")
        visiting.add(node)
        for dep in graph.dependencies.get(node, []):
            visit(dep)
        visiting.remove(node)
        visited.add(node)

    for node in task_ids:
        visit(node)
