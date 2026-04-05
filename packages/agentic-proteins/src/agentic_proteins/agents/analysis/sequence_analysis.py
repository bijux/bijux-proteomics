# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Sequence analysis agent contract."""

from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel

from agentic_proteins.agents.base import AgentRole
from agentic_proteins.agents.schemas import (
    AgentMetadata,
    SequenceAnalysisAgentInput,
    SequenceAnalysisAgentOutput,
)
from agentic_proteins.core.decisions import Decision
from agentic_proteins.memory.schemas import MemoryScope


class SequenceAnalysisAgent(AgentRole):
    """SequenceAnalysisAgent."""

    name: ClassVar[str] = "sequence_analysis"
    capabilities: ClassVar[set[str]] = {"sequence validation", "motif detection"}
    allowed_tools: ClassVar[set[str]] = {"motif_scan", "sequence_validator"}
    cost_budget: ClassVar[float] = 1.0
    latency_budget_ms: ClassVar[int] = 1
    input_model: ClassVar[type[BaseModel]] = SequenceAnalysisAgentInput
    output_model: ClassVar[type[BaseModel]] = SequenceAnalysisAgentOutput
    read_scopes: ClassVar[set[MemoryScope]] = {MemoryScope.SESSION}
    write_scopes: ClassVar[set[MemoryScope]] = {MemoryScope.SESSION}

    @classmethod
    def input_schema(cls) -> dict:
        """input_schema."""
        return SequenceAnalysisAgentInput.model_json_schema()

    @classmethod
    def output_schema(cls) -> dict:
        """output_schema."""
        return SequenceAnalysisAgentOutput.model_json_schema()

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

    def decide(self, payload: BaseModel) -> Decision:
        """decide."""
        SequenceAnalysisAgentInput.model_validate(payload)
        return Decision(
            agent_name=self.name,
            rationale="noop_analysis",
            requested_tools=[],
            next_tasks=[],
            confidence=0.0,
            input_refs=[],
            memory_refs=[],
            rules_triggered=["noop"],
            confidence_impact=[],
        )


SequenceAnalysisAgent.decide.__annotations__["return"] = Decision
