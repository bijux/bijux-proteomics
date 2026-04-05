# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Reporting agent."""

from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel

from agentic_proteins.agents.base import AgentRole
from agentic_proteins.agents.schemas import (
    AgentMetadata,
    ReportingAgentInput,
    ReportingAgentOutput,
)
from agentic_proteins.memory.schemas import MemoryScope
from agentic_proteins.validation.agents import validate_agent


class ReportingAgent(AgentRole):
    """ReportingAgent."""

    name: ClassVar[str] = "reporting"
    capabilities: ClassVar[set[str]] = {"report generation"}
    allowed_tools: ClassVar[set[str]] = set()
    cost_budget: ClassVar[float] = 1.0
    latency_budget_ms: ClassVar[int] = 1
    input_model: ClassVar[type[BaseModel]] = ReportingAgentInput
    output_model: ClassVar[type[BaseModel]] = ReportingAgentOutput
    read_scopes: ClassVar[set[MemoryScope]] = {MemoryScope.SESSION}
    write_scopes: ClassVar[set[MemoryScope]] = {MemoryScope.SESSION}

    @classmethod
    def input_schema(cls) -> dict:
        """input_schema."""
        return ReportingAgentInput.model_json_schema()

    @classmethod
    def output_schema(cls) -> dict:
        """output_schema."""
        return ReportingAgentOutput.model_json_schema()

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

    def decide(self, payload: BaseModel) -> ReportingAgentOutput:
        """decide."""
        report_input = ReportingAgentInput.model_validate(payload)
        validate_agent(type(self))
        summary = {
            "qc_status": report_input.qc_status,
            "decision": report_input.decision,
            "outputs": {item.name: item.value for item in report_input.tool_outputs},
        }
        confidence_statement = f"qc:{report_input.qc_status}"
        return ReportingAgentOutput(
            summary=summary,
            confidence_statement=confidence_statement,
            artifact_refs=[],
        )


ReportingAgent.decide.__annotations__["return"] = ReportingAgentOutput
