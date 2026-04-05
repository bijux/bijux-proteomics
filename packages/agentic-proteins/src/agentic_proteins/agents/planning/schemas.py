# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Planning schemas."""

from __future__ import annotations

import json

from pydantic import BaseModel, ConfigDict, Field

from agentic_proteins.core.decisions import DecisionExplanation
from agentic_proteins.core.hashing import sha256_hex


class TaskIO(BaseModel):
    """TaskIO."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, description="Input/output identifier.")
    schema_version: str = Field(
        ..., min_length=1, description="Schema version identifier."
    )
    source_task_id: str = Field(
        ..., min_length=1, description="Producer task identifier."
    )


class TaskConstraint(BaseModel):
    """TaskConstraint."""

    model_config = ConfigDict(extra="forbid")

    constraint_type: str = Field(
        ..., min_length=1, description="Constraint identifier."
    )
    value: str = Field(..., min_length=1, description="Constraint value.")


class TaskSpec(BaseModel):
    """TaskSpec."""

    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(..., min_length=1, description="Task identifier.")
    agent_name: str = Field(..., min_length=1, description="Assigned agent name.")
    objective: str = Field(
        ..., min_length=1, description="Machine-actionable objective code."
    )
    inputs: list[TaskIO] = Field(default_factory=list, description="Required inputs.")
    expected_outputs: list[TaskIO] = Field(
        default_factory=list,
        description="Expected output descriptors.",
    )
    constraints: list[TaskConstraint] = Field(
        default_factory=list,
        description="Task constraints.",
    )
    required_capabilities: list[str] = Field(
        default_factory=list,
        description="Capabilities required to perform the task.",
    )
    cost_estimate: float = Field(0.0, ge=0.0, description="Estimated cost.")
    latency_estimate_ms: int = Field(0, ge=0, description="Estimated latency in ms.")


class Plan(BaseModel):
    """Plan."""

    model_config = ConfigDict(extra="forbid")

    tasks: dict[str, TaskSpec] = Field(default_factory=dict, description="Task map.")
    dependencies: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Adjacency list of task dependencies.",
    )
    entry_tasks: list[str] = Field(default_factory=list, description="Entry task ids.")
    exit_conditions: list[str] = Field(
        default_factory=list,
        description="Structured exit conditions.",
    )

    def fingerprint(self) -> str:
        """fingerprint."""
        normalized = {
            "tasks": {
                task_id: self.tasks[task_id].model_dump()
                for task_id in sorted(self.tasks.keys())
            },
            "dependencies": {
                task_id: sorted(self.dependencies.get(task_id, []))
                for task_id in sorted(self.tasks.keys())
            },
            "entry_tasks": sorted(self.entry_tasks),
            "exit_conditions": sorted(self.exit_conditions),
        }
        payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
        return sha256_hex(payload)

    def explain(self) -> dict:
        """explain."""
        tasks_list = [
            {
                "task_id": task.task_id,
                "agent_name": task.agent_name,
                "objective": task.objective,
                "cost_estimate": task.cost_estimate,
                "latency_estimate_ms": task.latency_estimate_ms,
            }
            for task in self.tasks.values()
        ]
        agent_assignments: dict[str, list[str]] = {}
        for task in self.tasks.values():
            agent_assignments.setdefault(task.agent_name, []).append(task.task_id)
        total_cost = sum(task.cost_estimate for task in self.tasks.values())
        total_latency = sum(task.latency_estimate_ms for task in self.tasks.values())
        return {
            "tasks": tasks_list,
            "agent_assignments": agent_assignments,
            "dependency_graph": self.dependencies,
            "cost_total": total_cost,
            "latency_total_ms": total_latency,
        }


class PlanningHypothesis(BaseModel):
    """PlanningHypothesis."""

    model_config = ConfigDict(extra="forbid")

    hypothesis_id: str = Field(..., min_length=1, description="Hypothesis identifier.")
    statement: str = Field(
        ..., min_length=1, description="Biological hypothesis statement."
    )
    expected_effects: list[str] = Field(
        default_factory=list, description="Expected effects."
    )
    evidence: list[str] = Field(default_factory=list, description="Evidence tags.")


class MutationPlan(BaseModel):
    """MutationPlan."""

    model_config = ConfigDict(extra="forbid")

    mutation_id: str = Field(..., min_length=1, description="Mutation plan identifier.")
    mutation_type: str = Field(..., min_length=1, description="Mutation operator type.")
    parameters: dict[str, str] = Field(
        default_factory=dict, description="Mutation parameters."
    )
    intent: str = Field(
        ..., min_length=1, description="Biological intent for the mutation."
    )


class EvaluationCriterion(BaseModel):
    """EvaluationCriterion."""

    model_config = ConfigDict(extra="forbid")

    criterion_id: str = Field(..., min_length=1, description="Criterion identifier.")
    metric: str = Field(..., min_length=1, description="Metric name.")
    direction: str = Field(..., min_length=1, description="improve/maintain/avoid.")
    threshold: float | None = Field(default=None, description="Optional threshold.")
    rationale: str = Field(..., min_length=1, description="Rationale for criterion.")


class PlanDecision(BaseModel):
    """PlanDecision."""

    model_config = ConfigDict(extra="forbid")

    plan: Plan = Field(..., description="Plan DAG.")
    prior_plan_fingerprint: str | None = Field(
        default=None,
        description="Prior plan fingerprint when replanning.",
    )
    planning_rationale: list[str] = Field(
        default_factory=list,
        description="Structured rationale codes.",
    )
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence score.")
    assumptions: list[str] = Field(
        default_factory=list, description="Assumption codes."
    )
    hypotheses: list[PlanningHypothesis] = Field(
        default_factory=list,
        description="Biological hypotheses guiding the plan.",
    )
    mutation_plans: list[MutationPlan] = Field(
        default_factory=list,
        description="Mutation plans aligned with hypotheses.",
    )
    evaluation_criteria: list[EvaluationCriterion] = Field(
        default_factory=list,
        description="Evaluation criteria for candidate success.",
    )
    explanation: DecisionExplanation = Field(
        default_factory=DecisionExplanation,
        description="Decision explanation.",
    )
