# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Plan generation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Protocol

from agentic_proteins.agents.planning.schemas import Plan


@dataclass(frozen=True)
class PlanOutput:
    """PlanOutput."""

    plan: Plan
    plan_duration_ms: float


class PlannerProtocol(Protocol):
    """PlannerProtocol."""

    def decide(self, payload: object) -> object:
        """Return a planning decision object."""
        ...


def generate_plan(planner: PlannerProtocol, goal: str) -> PlanOutput:
    """generate_plan."""
    plan_start = perf_counter()
    plan_decision = planner.decide({"goal": goal})
    plan_duration = (perf_counter() - plan_start) * 1000.0
    return PlanOutput(plan=plan_decision.plan, plan_duration_ms=plan_duration)
