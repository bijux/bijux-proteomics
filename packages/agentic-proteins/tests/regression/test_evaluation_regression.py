# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter

import pytest

from agentic_proteins.agents.execution.coordinator import CoordinatorAgent
from agentic_proteins.agents.verification.critic import CriticAgent
from agentic_proteins.agents.analysis.failure_analysis import FailureAnalysisAgent
from agentic_proteins.agents.verification.input_validation import InputValidationAgent
from agentic_proteins.agents.planning.planner import PlannerAgent
from agentic_proteins.agents.verification.quality_control import QualityControlAgent
from agentic_proteins.agents.reporting.reporting import ReportingAgent
from agentic_proteins.execution.evaluation.evaluation import (
    EvaluationRunner,
    HeuristicBoundary,
)
from agentic_proteins.registry.agents import AgentRegistry
from agentic_proteins.registry.tools import ToolRegistry
from agentic_proteins.execution.evaluation.schemas import EvaluationCase
from agentic_proteins.tools.schemas import SchemaDefinition, ToolContract, ToolDeterminism
from agentic_proteins.tools.heuristic import HeuristicStructureTool


def register_agents() -> None:
    AgentRegistry._registry.clear()
    AgentRegistry._locked = False
    AgentRegistry.register(InputValidationAgent)
    AgentRegistry.register(PlannerAgent)
    AgentRegistry.register(QualityControlAgent)
    AgentRegistry.register(CriticAgent)
    AgentRegistry.register(FailureAnalysisAgent)
    AgentRegistry.register(ReportingAgent)
    AgentRegistry.register(CoordinatorAgent)
    AgentRegistry.lock()


def register_tools() -> None:
    ToolRegistry._registry.clear()
    ToolRegistry._locked = False
    ToolRegistry.register(
        ToolContract(
            tool_name=HeuristicStructureTool.name,
            version=HeuristicStructureTool.version,
            input_schema=SchemaDefinition(schema_name="dummy_input", json_schema="{}"),
            output_schema=SchemaDefinition(schema_name="dummy_output", json_schema="{}"),
            failure_modes=[],
            cost_estimate=1.0,
            latency_estimate_ms=1,
            determinism=ToolDeterminism.DETERMINISTIC,
        )
    )
    ToolRegistry.lock()


def load_cases() -> list[EvaluationCase]:
    path = Path(__file__).resolve().parent / "benchmarks" / "cases.json"
    payload = json.loads(path.read_text())
    return [EvaluationCase.model_validate(item) for item in payload]

def _load_time_budget() -> float:
    path = Path(__file__).resolve().parent / "time_budget.json"
    payload = json.loads(path.read_text())
    return float(payload["evaluation_guardrails_seconds"])


@pytest.mark.evaluation
def test_evaluation_regression_guardrails() -> None:
    start = perf_counter()
    register_agents()
    register_tools()
    runner = EvaluationRunner(HeuristicBoundary())
    report = runner.run(load_cases())
    assert [result.pass_fail for result in report.results] == [True, True, False]
    assert all(0.0 <= result.confidence <= 1.0 for result in report.results)
    assert report.results[0].violations == []
    assert report.results[1].violations == []
    assert report.results[2].violations

    scorecards = {card.agent_name: card for card in report.scorecards}
    assert scorecards["quality_control"].failure_rate == pytest.approx(1.0 / 3.0)
    assert scorecards["critic"].failure_rate == pytest.approx(1.0 / 3.0)
    assert scorecards["coordinator"].failure_rate == pytest.approx(1.0 / 3.0)
    duration = perf_counter() - start
    assert duration <= _load_time_budget() * 1.2


@pytest.mark.evaluation
def test_evaluation_is_deterministic() -> None:
    register_agents()
    register_tools()
    runner = EvaluationRunner(HeuristicBoundary())
    cases = load_cases()
    first = runner.run(cases)
    second = runner.run(cases)
    assert first.model_dump() == second.model_dump()
