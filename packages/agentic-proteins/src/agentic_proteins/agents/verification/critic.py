# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Critic agent contract."""

from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel

from agentic_proteins.agents.base import AgentRole
from agentic_proteins.agents.schemas import (
    AgentMetadata,
    CriticAgentInput,
    CriticAgentOutput,
)
from agentic_proteins.core.decisions import DecisionExplanation
from agentic_proteins.memory.schemas import MemoryScope
from agentic_proteins.validation.agents import validate_critic_input


class CriticAgent(AgentRole):
    """CriticAgent."""

    name: ClassVar[str] = "critic"
    capabilities: ClassVar[set[str]] = {"validation", "anomaly detection"}
    allowed_tools: ClassVar[set[str]] = set()
    cost_budget: ClassVar[float] = 1.0
    latency_budget_ms: ClassVar[int] = 1
    input_model: ClassVar[type[BaseModel]] = CriticAgentInput
    output_model: ClassVar[type[BaseModel]] = CriticAgentOutput
    read_scopes: ClassVar[set[MemoryScope]] = {MemoryScope.SESSION}
    write_scopes: ClassVar[set[MemoryScope]] = {MemoryScope.EPHEMERAL}

    @classmethod
    def input_schema(cls) -> dict:
        """input_schema."""
        return CriticAgentInput.model_json_schema()

    @classmethod
    def output_schema(cls) -> dict:
        """output_schema."""
        return CriticAgentOutput.model_json_schema()

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

    def decide(self, payload: BaseModel) -> CriticAgentOutput:
        """decide."""
        critic_input = CriticAgentInput.model_validate(payload)
        validate_critic_input(critic_input)
        notes: list[str] = []
        if (
            critic_input.tool_reliability is not None
            and critic_input.tool_reliability.success_rate < 0.8
        ):
            notes.append("tool_reliability_low")
        input_refs = ["qc_output"]
        if critic_input.tool_reliability:
            input_refs.append("tool_reliability")
        if critic_input.qc_output.status in {"reject", "needs_human"}:
            return CriticAgentOutput(
                blocking=True,
                inconsistencies=["qc_blocking"],
                notes=notes,
                explanation=DecisionExplanation(
                    input_refs=input_refs,
                    rules_triggered=["qc_blocking"],
                    confidence_impact=["downweight_due_to_qc"],
                ),
            )
        return CriticAgentOutput(
            blocking=False,
            inconsistencies=[],
            notes=notes,
            explanation=DecisionExplanation(
                input_refs=input_refs,
                rules_triggered=notes or ["qc_clear"],
                confidence_impact=["no_block"],
            ),
        )


CriticAgent.decide.__annotations__["return"] = CriticAgentOutput
