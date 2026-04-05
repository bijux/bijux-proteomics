# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import importlib
import re

import pytest

from agentic_proteins.registry.agents import AgentRegistry
from agentic_proteins.agents.schemas import PlannerAgentInput
from agentic_proteins.agents.planning.schemas import Plan, PlanDecision, TaskSpec
from agentic_proteins.agents.planning.validation import validate_plan


AGENT_MODULES = [
    "agentic_proteins.agents.planning.planner",
    "agentic_proteins.agents.verification.input_validation",
    "agentic_proteins.agents.analysis.sequence_analysis",
    "agentic_proteins.agents.analysis.structure",
    "agentic_proteins.agents.verification.quality_control",
    "agentic_proteins.agents.verification.critic",
    "agentic_proteins.agents.analysis.failure_analysis",
    "agentic_proteins.agents.reporting.reporting",
    "agentic_proteins.agents.execution.coordinator",
]


AGENT_CLASSES = [
    "PlannerAgent",
    "InputValidationAgent",
    "SequenceAnalysisAgent",
    "StructureAgent",
    "QualityControlAgent",
    "CriticAgent",
    "FailureAnalysisAgent",
    "ReportingAgent",
    "CoordinatorAgent",
]


def register_agents() -> None:
    AgentRegistry._registry.clear()
    AgentRegistry._locked = False
    for module_name, class_name in zip(AGENT_MODULES, AGENT_CLASSES, strict=True):
        module = importlib.import_module(module_name)
        AgentRegistry.register(getattr(module, class_name))


def test_planner_decide_emits_plan_decision() -> None:
    register_agents()
    module = importlib.import_module("agentic_proteins.agents.planning.planner")
    planner = module.PlannerAgent()
    decision = planner.decide(PlannerAgentInput())
    assert isinstance(decision, PlanDecision)
    decision.model_validate(decision.model_dump())


def test_plan_validation_cycles_and_unknown_agents() -> None:
    register_agents()
    task = TaskSpec(
        task_id="t1",
        agent_name="planner",
        objective="planning",
        required_capabilities=["planning"],
    )
    with pytest.raises(ValueError):
        validate_plan(Plan(tasks={}, dependencies={}, entry_tasks=[], exit_conditions=[]))

    with pytest.raises(ValueError):
        validate_plan(
            Plan(
                tasks={"t1": task},
                dependencies={"t1": ["t1"]},
                entry_tasks=["t1"],
                exit_conditions=["done"],
            )
        )

    bad_task = task.model_copy(update={"agent_name": "unknown_agent"})
    with pytest.raises(ValueError):
        validate_plan(
            Plan(
                tasks={"t1": bad_task},
                dependencies={"t1": []},
                entry_tasks=["t1"],
                exit_conditions=["done"],
            )
        )


def test_plan_validation_missing_dependency() -> None:
    register_agents()
    task = TaskSpec(
        task_id="t1",
        agent_name="planner",
        objective="planning",
        required_capabilities=["planning"],
    )
    with pytest.raises(ValueError):
        validate_plan(
            Plan(
                tasks={"t1": task},
                dependencies={"t1": ["missing"]},
                entry_tasks=["t1"],
                exit_conditions=["done"],
            )
        )


def test_plan_capability_mismatch() -> None:
    register_agents()
    task = TaskSpec(
        task_id="t1",
        agent_name="planner",
        objective="planning",
        required_capabilities=["structure request"],
    )
    with pytest.raises(ValueError):
        validate_plan(
            Plan(
                tasks={"t1": task},
                dependencies={"t1": []},
                entry_tasks=["t1"],
                exit_conditions=["done"],
            )
        )


def test_plan_fingerprint_stability() -> None:
    register_agents()
    task = TaskSpec(
        task_id="t1",
        agent_name="planner",
        objective="planning",
        required_capabilities=["planning"],
        cost_estimate=1.0,
        latency_estimate_ms=1,
    )
    plan_a = Plan(
        tasks={"t1": task},
        dependencies={"t1": []},
        entry_tasks=["t1"],
        exit_conditions=["done"],
    )
    plan_b = Plan(
        tasks={"t1": task},
        dependencies={"t1": []},
        entry_tasks=["t1"],
        exit_conditions=["done"],
    )
    assert plan_a.fingerprint() == plan_b.fingerprint()


def test_plan_explain_is_data_only() -> None:
    register_agents()
    task = TaskSpec(
        task_id="t1",
        agent_name="planner",
        objective="planning",
        required_capabilities=["planning"],
        cost_estimate=1.0,
        latency_estimate_ms=2,
    )
    plan = Plan(
        tasks={"t1": task},
        dependencies={"t1": []},
        entry_tasks=["t1"],
        exit_conditions=["done"],
    )
    explanation = plan.explain()
    assert "tasks" in explanation
    assert "dependency_graph" in explanation
    assert explanation["cost_total"] == 1.0
    assert explanation["latency_total_ms"] == 2


def test_plan_contains_no_execution_artifacts() -> None:
    register_agents()
    module = importlib.import_module("agentic_proteins.agents.planning.planner")
    planner = module.PlannerAgent()
    decision = planner.decide(PlannerAgentInput())
    plan = decision.plan
    text = repr(plan.model_dump())
    banned = re.compile(r"(\bpython\b|\bbash\b|\bsh\b|/|\\|\$\w+)")
    assert not banned.search(text)
