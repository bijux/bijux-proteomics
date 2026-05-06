# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Failure analysis agent."""

from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel

from bijux_proteomics_runtime.execution.agents.base import AgentRole
from bijux_proteomics_runtime.execution.agents.schemas import (
    AgentMetadata,
    FailureAnalysisAgentInput,
    FailureAnalysisAgentOutput,
)
from bijux_proteomics_runtime.support.primitives.failures import FailureType
from bijux_proteomics_runtime.state.memory_records import MemoryScope
from bijux_proteomics_runtime.execution.agents.contracts import validate_agent


class FailureAnalysisAgent(AgentRole):
    """FailureAnalysisAgent."""

    name: ClassVar[str] = "failure_analysis"
    capabilities: ClassVar[set[str]] = {"failure classification"}
    allowed_tools: ClassVar[set[str]] = set()
    cost_budget: ClassVar[float] = 1.0
    latency_budget_ms: ClassVar[int] = 1
    input_model: ClassVar[type[BaseModel]] = FailureAnalysisAgentInput
    output_model: ClassVar[type[BaseModel]] = FailureAnalysisAgentOutput
    read_scopes: ClassVar[set[MemoryScope]] = {MemoryScope.SESSION}
    write_scopes: ClassVar[set[MemoryScope]] = {MemoryScope.SESSION}

    @classmethod
    def input_schema(cls) -> dict[str, object]:
        """input_schema."""
        return FailureAnalysisAgentInput.model_json_schema()

    @classmethod
    def output_schema(cls) -> dict[str, object]:
        """output_schema."""
        return FailureAnalysisAgentOutput.model_json_schema()

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

    def decide(self, payload: BaseModel) -> FailureAnalysisAgentOutput:
        """decide."""
        failure_input = FailureAnalysisAgentInput.model_validate(payload)
        validate_agent(type(self))
        metadata: list[str] = []
        failure_type = FailureType.UNKNOWN.value
        if failure_input.status != "success":
            failure_type = FailureType.TOOL_FAILURE.value
            if failure_input.error_type:
                metadata.append(f"error_type:{failure_input.error_type}")
            if failure_input.error_message:
                metadata.append("has_error_message")
        return FailureAnalysisAgentOutput(
            failure_type=failure_type,
            metadata=metadata,
            replan_recommended=failure_type != FailureType.UNKNOWN.value,
        )


FailureAnalysisAgent.decide.__annotations__["return"] = FailureAnalysisAgentOutput
