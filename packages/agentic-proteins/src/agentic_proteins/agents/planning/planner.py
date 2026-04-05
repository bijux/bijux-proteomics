# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Planner agent contract."""

from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel

from agentic_proteins.agents.base import AgentRole
from agentic_proteins.agents.planning.schemas import (
    EvaluationCriterion,
    MutationPlan,
    PlanningHypothesis,
)
from agentic_proteins.agents.schemas import (
    AgentMetadata,
    PlannerAgentInput,
    PlannerAgentOutput,
)
from agentic_proteins.core.decisions import DecisionExplanation
from agentic_proteins.memory.schemas import MemoryScope


class PlannerAgent(AgentRole):
    """PlannerAgent."""

    name: ClassVar[str] = "planner"
    capabilities: ClassVar[set[str]] = {"task_decomposition", "planning"}
    allowed_tools: ClassVar[set[str]] = set()
    cost_budget: ClassVar[float] = 1.0
    latency_budget_ms: ClassVar[int] = 1
    input_model: ClassVar[type[BaseModel]] = PlannerAgentInput
    output_model: ClassVar[type[BaseModel]] = PlannerAgentOutput
    read_scopes: ClassVar[set[MemoryScope]] = {MemoryScope.SESSION}
    write_scopes: ClassVar[set[MemoryScope]] = {MemoryScope.SESSION}

    @classmethod
    def input_schema(cls) -> dict:
        """input_schema."""
        return PlannerAgentInput.model_json_schema()

    @classmethod
    def output_schema(cls) -> dict:
        """output_schema."""
        return PlannerAgentOutput.model_json_schema()

    @classmethod
    def metadata(cls) -> AgentMetadata:
        """metadata."""
        return AgentMetadata(
            agent_name=cls.name,
            version="1.0",
            capabilities=sorted(cls.capabilities),
            allowed_tools=sorted(cls.allowed_tools),
            cost_budget=cls.cost_budget,
            latency_budget_ms=cls.latency_budget_ms,
            read_scopes=sorted(cls.read_scopes, key=lambda item: item.value),
            write_scopes=sorted(cls.write_scopes, key=lambda item: item.value),
        )

    def decide(self, payload: BaseModel) -> PlannerAgentOutput:
        """decide."""
        planner_input = PlannerAgentInput.model_validate(payload)
        task_id = "plan_task_1"
        plan = {
            "tasks": {
                task_id: {
                    "task_id": task_id,
                    "agent_name": self.name,
                    "objective": "design_candidate",
                    "inputs": [],
                    "expected_outputs": [],
                    "constraints": [],
                    "required_capabilities": ["planning"],
                    "cost_estimate": self.cost_budget,
                    "latency_estimate_ms": self.latency_budget_ms,
                }
            },
            "dependencies": {task_id: []},
            "entry_tasks": [task_id],
            "exit_conditions": ["plan_ready"],
        }
        hypotheses = [
            PlanningHypothesis(
                hypothesis_id="hyp-1",
                statement="Improve structural confidence without disrupting core folds.",
                expected_effects=["increase_mean_plddt", "maintain_secondary_balance"],
                evidence=["planner_default"],
            )
        ]
        mutation_plans = [
            MutationPlan(
                mutation_id="mut-1",
                mutation_type="point_mutation",
                parameters={"position": "auto", "new_residue": "auto"},
                intent="Stabilize local secondary structure.",
            )
        ]
        evaluation_criteria = [
            EvaluationCriterion(
                criterion_id="crit-1",
                metric="mean_plddt",
                direction="improve",
                threshold=70.0,
                rationale="Ensure confidence meets minimum acceptance.",
            )
        ]
        return PlannerAgentOutput(
            plan=plan,
            planning_rationale=["default_plan"],
            confidence=0.1,
            assumptions=["goal_provided" if planner_input.goal else "goal_unspecified"],
            hypotheses=hypotheses,
            mutation_plans=mutation_plans,
            evaluation_criteria=evaluation_criteria,
            explanation=DecisionExplanation(
                input_refs=["goal"] if planner_input.goal else ["goal_unspecified"],
                rules_triggered=["default_plan"],
                confidence_impact=["baseline_low_confidence"],
            ),
        )


PlannerAgent.decide.__annotations__["return"] = PlannerAgentOutput
