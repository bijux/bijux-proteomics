# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Plan generation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Protocol

from pydantic import BaseModel

from bijux_proteomics_runtime.agents.planning.schemas import Plan
from bijux_proteomics_runtime.agents.schemas import PlannerAgentInput


@dataclass(frozen=True)
class PlanOutput:
    """PlanOutput."""

    plan: Plan
    plan_duration_ms: float


class PlannerProtocol(Protocol):
    """PlannerProtocol."""

    def decide(self, payload: BaseModel) -> PlanningDecisionLike:
        """Return a planning decision object."""
        ...


class PlanningDecisionLike(Protocol):
    """PlanningDecisionLike."""

    plan: Plan


def generate_plan(planner: PlannerProtocol, goal: str) -> PlanOutput:
    """generate_plan."""
    plan_start = perf_counter()
    plan_decision = planner.decide(PlannerAgentInput(goal=goal))
    plan_duration = (perf_counter() - plan_start) * 1000.0
    return PlanOutput(plan=plan_decision.plan, plan_duration_ms=plan_duration)
