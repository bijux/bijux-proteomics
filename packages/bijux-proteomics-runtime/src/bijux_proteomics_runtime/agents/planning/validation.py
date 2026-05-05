# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Planning validation."""

from __future__ import annotations

from bijux_proteomics_intelligence.domain.candidates.schema import Candidate

from bijux_proteomics.domain.sequence.validation import validate_sequence
from bijux_proteomics_runtime.agents.planning.schemas import Plan
from bijux_proteomics_runtime.agents.catalog import AgentCatalog


class PlanningValidator:
    """PlanningValidator."""

    def validate_candidate(self, candidate: Candidate) -> list[str]:
        """validate_candidate."""
        return validate_sequence(candidate.sequence)

    def validate_tool_enabled(
        self, tool_name: str, config: dict[str, object]
    ) -> list[str]:
        """validate_tool_enabled."""
        enabled_obj = config.get("predictors_enabled", [])
        enabled = set(enabled_obj) if isinstance(enabled_obj, list) else set()
        if enabled and tool_name not in enabled:
            return ["tool_disabled"]
        return []

    def validate_tool_compatibility(
        self, tool_name: str, config: dict[str, object]
    ) -> list[str]:
        """validate_tool_compatibility."""
        return _validate_compatibility(tool_name, config)


def validate_plan(plan: Plan) -> None:
    """validate_plan."""
    if not plan.tasks:
        raise ValueError("Plan must contain at least one task.")
    task_ids = set(plan.tasks.keys())
    for task_id, task in plan.tasks.items():
        if task_id != task.task_id:
            raise ValueError(f"Task id mismatch for {task_id}.")
        try:
            agent_cls = AgentCatalog.get(task.agent_name)
        except KeyError as exc:
            raise ValueError(f"Unknown agent: {task.agent_name}") from exc
        if task.required_capabilities:
            missing = set(task.required_capabilities) - set(agent_cls.capabilities)
            if missing:
                raise ValueError(
                    f"Agent {task.agent_name} lacks capabilities: {sorted(missing)}"
                )
    for task_id, deps in plan.dependencies.items():
        if task_id not in task_ids:
            raise ValueError(f"Unknown dependency task: {task_id}")
        for dep in deps:
            if dep not in task_ids:
                raise ValueError(f"Unknown dependency target: {dep}")
    for entry in plan.entry_tasks:
        if entry not in task_ids:
            raise ValueError(f"Unknown entry task: {entry}")
    _assert_acyclic(plan, task_ids)


def _assert_acyclic(plan: Plan, task_ids: set[str]) -> None:
    """_assert_acyclic."""
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        """visit."""
        if node in visited:
            return
        if node in visiting:
            raise ValueError("Plan contains a cycle.")
        visiting.add(node)
        for dep in plan.dependencies.get(node, []):
            visit(dep)
        visiting.remove(node)
        visited.add(node)

    for node in task_ids:
        visit(node)


def _validate_compatibility(tool_name: str, config: dict[str, object]) -> list[str]:
    """_validate_compatibility."""
    matrix = {
        "heuristic_proxy": {
            "requires_gpu": False,
            "min_gpu_seconds": 0.0,
            "supports_cpu": True,
        },
        "local_esmfold": {
            "requires_gpu": True,
            "min_gpu_seconds": 1.0,
            "supports_cpu": True,
        },
        "local_rosettafold": {
            "requires_gpu": True,
            "min_gpu_seconds": 1.0,
            "supports_cpu": False,
        },
        "api_colabfold": {"requires_gpu": False, "min_gpu_seconds": 0.0},
        "api_openprotein_esmfold": {"requires_gpu": False, "min_gpu_seconds": 0.0},
        "api_openprotein_alphafold": {"requires_gpu": False, "min_gpu_seconds": 0.0},
    }
    requirements = matrix.get(
        tool_name, {"requires_gpu": False, "min_gpu_seconds": 0.0, "supports_cpu": True}
    )
    execution_mode = config.get("execution_mode", "auto")
    limits_obj = config.get("resource_limits", {})
    limits = limits_obj if isinstance(limits_obj, dict) else {}
    gpu_seconds = float(limits.get("gpu_seconds", 0.0))
    errors: list[str] = []
    if requirements.get("supports_cpu", False):
        if execution_mode == "cpu":
            return errors
        if execution_mode == "auto" and gpu_seconds > 0.0:
            return errors
    if requirements["requires_gpu"] and gpu_seconds <= 0.0:
        errors.append("gpu_required")
    if gpu_seconds < float(requirements.get("min_gpu_seconds", 0.0)):
        errors.append("gpu_budget_too_low")
    return errors
