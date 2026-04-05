# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from datetime import UTC, datetime

from agentic_proteins.agents.execution.coordinator import CoordinatorAgent
from agentic_proteins.agents.verification.critic import CriticAgent
from agentic_proteins.agents.verification.quality_control import QualityControlAgent
from agentic_proteins.agents.schemas import (
    CoordinatorAgentInput,
    CoordinatorDecisionType,
    CriticAgentInput,
    QualityControlAgentInput,
    QualityControlAgentOutput,
    OutputReference,
)
from agentic_proteins.core.execution import LoopLimits, LoopState
from agentic_proteins.core.observations import EvaluationInput, Observation, ObservationSource, PlanMetadata
from agentic_proteins.state.schemas import StateSnapshot
from agentic_proteins.domain.candidates.schema import Candidate


def sample_state() -> StateSnapshot:
    return StateSnapshot(
        state_id="s1",
        parent_state_id=None,
        plan_fingerprint="p1",
        timestamp=datetime.now(UTC),
        agent_decisions=[],
        artifacts=[],
        metrics=[],
        confidence_summary=[],
    )


def sample_eval_input() -> EvaluationInput:
    return EvaluationInput(
        observations=[
            Observation(
                observation_id="o1",
                source=ObservationSource.TOOL,
                related_task_id="t1",
                tool_result_fingerprint="f1",
                metrics=[],
                confidence=0.1,
                timestamp=datetime.now(UTC),
            )
        ],
        prior_state=sample_state(),
        plan_metadata=PlanMetadata(plan_fingerprint="p1", plan_id="plan1"),
        constraints=[],
    )


def test_quality_control_decide() -> None:
    qc = QualityControlAgent()
    candidate = Candidate(
        candidate_id="cand-1",
        sequence="ACDE",
        metrics={"mean_plddt": 80.0, "helix_pct": 40.0, "sheet_pct": 30.0},
    )
    output = qc.decide(
        QualityControlAgentInput(evaluation=sample_eval_input(), candidate=candidate)
    )
    assert output.status == "acceptable"


def test_critic_decide() -> None:
    critic = CriticAgent()
    qc_output = QualityControlAgentOutput(status="acceptable", confidence_deltas=[], constraint_violations=[])
    output = critic.decide(
        CriticAgentInput(
            critic_name="critic",
            target_agent_name="quality_control",
            target_output=OutputReference(agent_name="qc", output_id="o1", schema_version="1.0"),
            prior_decisions=[],
            qc_output=qc_output,
            observations=[],
        )
    )
    assert output.blocking is False


def test_coordinator_decide_limits() -> None:
    coordinator = CoordinatorAgent()
    qc_output = QualityControlAgentOutput(status="acceptable", confidence_deltas=[], constraint_violations=[])
    critic = CriticAgent()
    critic_output = critic.decide(
        CriticAgentInput(
            critic_name="critic",
            target_agent_name="quality_control",
            target_output=OutputReference(agent_name="qc", output_id="o1", schema_version="1.0"),
            prior_decisions=[],
            qc_output=qc_output,
            observations=[],
        )
    )
    output = coordinator.decide(
        CoordinatorAgentInput(
            decisions=[],
            observations=[],
            qc_output=qc_output,
            critic_output=critic_output,
            replanning_trigger=None,
            loop_limits=LoopLimits(max_replans=0, max_executions_per_plan=0, max_uncertainty=0.0),
            loop_state=LoopState(replans=1, executions=0, uncertainty=0.0),
        )
    )
    assert output.decision == CoordinatorDecisionType.TERMINATE
