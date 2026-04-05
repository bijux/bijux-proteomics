from __future__ import annotations

from agentic_proteins.agents.execution.coordinator import CoordinatorAgent
from agentic_proteins.agents.schemas import (
    CoordinatorAgentInput,
    CoordinatorDecisionType,
    CriticAgentOutput,
    QualityControlAgentOutput,
)
from agentic_proteins.core.decisions import Decision
from agentic_proteins.core.execution import LoopLimits, LoopState


def test_coordinator_rejects_opaque_decision() -> None:
    agent = CoordinatorAgent()
    opaque = Decision(
        agent_name="x",
        rationale="test",
        requested_tools=[],
        next_tasks=[],
        confidence=0.0,
        input_refs=[],
        memory_refs=["m1"],
        rules_triggered=[],
        confidence_impact=[],
    )
    payload = CoordinatorAgentInput(decisions=[opaque])
    result = agent.decide(payload)
    assert result.decision == CoordinatorDecisionType.TERMINATE
    assert result.stop_reason == "opaque_decision"


def test_coordinator_enforces_loop_limits() -> None:
    agent = CoordinatorAgent()
    payload = CoordinatorAgentInput(
        loop_limits=LoopLimits(max_replans=0),
        loop_state=LoopState(replans=1),
    )
    result = agent.decide(payload)
    assert result.stop_reason == "max_replans_exceeded"

    payload = CoordinatorAgentInput(
        loop_limits=LoopLimits(max_executions_per_plan=0),
        loop_state=LoopState(executions=1),
    )
    result = agent.decide(payload)
    assert result.stop_reason == "max_executions_exceeded"

    payload = CoordinatorAgentInput(
        loop_limits=LoopLimits(max_uncertainty=0.0),
        loop_state=LoopState(uncertainty=1.0),
    )
    result = agent.decide(payload)
    assert result.stop_reason == "max_uncertainty_exceeded"


def test_coordinator_handles_critic_and_qc_outputs() -> None:
    agent = CoordinatorAgent()
    payload = CoordinatorAgentInput(
        critic_output=CriticAgentOutput(blocking=True),
    )
    result = agent.decide(payload)
    assert result.decision == CoordinatorDecisionType.REPLAN

    payload = CoordinatorAgentInput(
        qc_output=QualityControlAgentOutput(status="reject"),
    )
    result = agent.decide(payload)
    assert result.decision == CoordinatorDecisionType.TERMINATE

    payload = CoordinatorAgentInput(
        qc_output=QualityControlAgentOutput(status="needs_human"),
    )
    result = agent.decide(payload)
    assert result.decision == CoordinatorDecisionType.TERMINATE
