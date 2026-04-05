# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Coordinator agent contract."""

from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel

from agentic_proteins.agents.base import AgentRole
from agentic_proteins.agents.schemas import (
    AgentMetadata,
    CoordinatorAgentInput,
    CoordinatorAgentOutput,
    CoordinatorDecisionType,
)
from agentic_proteins.core.decisions import DecisionExplanation
from agentic_proteins.core.observations import (
    ReplanningTrigger,
    ReplanningTriggerType,
)
from agentic_proteins.memory.schemas import MemoryScope
from agentic_proteins.validation.agents import validate_agent


class CoordinatorAgent(AgentRole):
    """CoordinatorAgent."""

    name: ClassVar[str] = "coordinator"
    capabilities: ClassVar[set[str]] = {"orchestration decisions"}
    allowed_tools: ClassVar[set[str]] = set()
    cost_budget: ClassVar[float] = 1.0
    latency_budget_ms: ClassVar[int] = 1
    input_model: ClassVar[type[BaseModel]] = CoordinatorAgentInput
    output_model: ClassVar[type[BaseModel]] = CoordinatorAgentOutput
    read_scopes: ClassVar[set[MemoryScope]] = {MemoryScope.SESSION}
    write_scopes: ClassVar[set[MemoryScope]] = {MemoryScope.EPHEMERAL}

    @classmethod
    def input_schema(cls) -> dict:
        """input_schema."""
        return CoordinatorAgentInput.model_json_schema()

    @classmethod
    def output_schema(cls) -> dict:
        """output_schema."""
        return CoordinatorAgentOutput.model_json_schema()

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

    def decide(self, payload: BaseModel) -> CoordinatorAgentOutput:
        """decide."""
        coordinator_input = CoordinatorAgentInput.model_validate(payload)
        validate_agent(type(self))
        for decision in coordinator_input.decisions:
            if not decision.input_refs or not decision.memory_refs:
                return CoordinatorAgentOutput(
                    decision=CoordinatorDecisionType.TERMINATE,
                    reason_codes=["opaque_decision"],
                    replanning_trigger=None,
                    stop_reason="opaque_decision",
                    thresholds_hit=["opaque_decision"],
                    confidence_plateau=False,
                    explanation=DecisionExplanation(
                        input_refs=["decisions"],
                        rules_triggered=["opaque_decision"],
                        confidence_impact=["terminate_run"],
                    ),
                )
        if (
            coordinator_input.loop_state.replans
            > coordinator_input.loop_limits.max_replans
        ):
            return CoordinatorAgentOutput(
                decision=CoordinatorDecisionType.TERMINATE,
                reason_codes=["max_replans_exceeded"],
                replanning_trigger=None,
                stop_reason="max_replans_exceeded",
                thresholds_hit=["max_replans_exceeded"],
                confidence_plateau=False,
                explanation=DecisionExplanation(
                    input_refs=["loop_state"],
                    rules_triggered=["max_replans_exceeded"],
                    confidence_impact=["terminate_run"],
                ),
            )
        if (
            coordinator_input.loop_state.executions
            > coordinator_input.loop_limits.max_executions_per_plan
        ):
            return CoordinatorAgentOutput(
                decision=CoordinatorDecisionType.TERMINATE,
                reason_codes=["max_executions_exceeded"],
                replanning_trigger=None,
                stop_reason="max_executions_exceeded",
                thresholds_hit=["max_executions_exceeded"],
                confidence_plateau=False,
                explanation=DecisionExplanation(
                    input_refs=["loop_state"],
                    rules_triggered=["max_executions_exceeded"],
                    confidence_impact=["terminate_run"],
                ),
            )
        if (
            coordinator_input.loop_state.uncertainty
            > coordinator_input.loop_limits.max_uncertainty
        ):
            return CoordinatorAgentOutput(
                decision=CoordinatorDecisionType.TERMINATE,
                reason_codes=["max_uncertainty_exceeded"],
                replanning_trigger=None,
                stop_reason="max_uncertainty_exceeded",
                thresholds_hit=["max_uncertainty_exceeded"],
                confidence_plateau=False,
                explanation=DecisionExplanation(
                    input_refs=["loop_state"],
                    rules_triggered=["max_uncertainty_exceeded"],
                    confidence_impact=["terminate_run"],
                ),
            )
        if coordinator_input.critic_output.blocking:
            return CoordinatorAgentOutput(
                decision=CoordinatorDecisionType.REPLAN,
                reason_codes=["critic_blocking"],
                replanning_trigger=coordinator_input.replanning_trigger
                or ReplanningTrigger(
                    trigger_type=ReplanningTriggerType.FAILURE,
                    source_agent=self.name,
                    severity=1,
                    evidence_ids=["critic_blocking"],
                ),
                stop_reason="critic_blocking",
                thresholds_hit=["critic_blocking"],
                confidence_plateau=False,
                explanation=DecisionExplanation(
                    input_refs=["critic_output"],
                    rules_triggered=["critic_blocking"],
                    confidence_impact=["request_replan"],
                ),
            )
        if coordinator_input.qc_output.status == "reject":
            return CoordinatorAgentOutput(
                decision=CoordinatorDecisionType.TERMINATE,
                reason_codes=["qc_reject"],
                replanning_trigger=None,
                stop_reason="qc_reject",
                thresholds_hit=["qc_reject"],
                confidence_plateau=False,
                explanation=DecisionExplanation(
                    input_refs=["qc_output"],
                    rules_triggered=["qc_reject"],
                    confidence_impact=["terminate_run"],
                ),
            )
        if coordinator_input.qc_output.status == "needs_human":
            return CoordinatorAgentOutput(
                decision=CoordinatorDecisionType.TERMINATE,
                reason_codes=["qc_needs_human"],
                replanning_trigger=None,
                stop_reason="qc_needs_human",
                thresholds_hit=["qc_needs_human"],
                confidence_plateau=False,
                explanation=DecisionExplanation(
                    input_refs=["qc_output"],
                    rules_triggered=["qc_needs_human"],
                    confidence_impact=["terminate_run"],
                ),
            )
        return CoordinatorAgentOutput(
            decision=CoordinatorDecisionType.CONTINUE,
            reason_codes=["qc_pass"],
            replanning_trigger=None,
            stop_reason="continue",
            thresholds_hit=[],
            confidence_plateau="stagnation"
            in coordinator_input.loop_state.stopping_criteria,
            explanation=DecisionExplanation(
                input_refs=["qc_output", "critic_output"],
                rules_triggered=["qc_pass"],
                confidence_impact=["continue_execution"],
            ),
        )


CoordinatorAgent.decide.__annotations__["return"] = CoordinatorAgentOutput
