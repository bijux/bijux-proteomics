# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""State and execution validation helpers."""

from __future__ import annotations

from agentic_proteins.core.execution import ExecutionGraph
from agentic_proteins.state.schemas import StateSnapshot


def validate_state_snapshot(snapshot: StateSnapshot) -> None:
    """validate_state_snapshot."""
    if not snapshot.state_id:
        raise ValueError("State snapshot must include a state_id.")
    if not snapshot.plan_fingerprint:
        raise ValueError("State snapshot must include a plan fingerprint.")


def validate_execution_graph(graph: ExecutionGraph) -> None:
    """validate_execution_graph."""
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
    """_assert_acyclic."""
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        """visit."""
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
