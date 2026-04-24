# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Structure agent contract."""

from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel

from bijux_proteomics_runtime.agents.base import AgentRole
from bijux_proteomics_runtime.agents.schemas import (
    AgentMetadata,
    StructureAgentInput,
    StructureAgentOutput,
)
from bijux_proteomics_runtime.core.decisions import Decision
from bijux_proteomics_runtime.memory.schemas import MemoryScope


class StructureAgent(AgentRole):
    """StructureAgent."""

    name: ClassVar[str] = "structure"
    capabilities: ClassVar[set[str]] = {"structure request", "model selection"}
    allowed_tools: ClassVar[set[str]] = {
        "heuristic_proxy",
        "local_esmfold",
        "local_rosettafold",
        "api_openprotein_esmfold",
        "api_openprotein_alphafold",
        "api_colabfold",
    }
    cost_budget: ClassVar[float] = 1.0
    latency_budget_ms: ClassVar[int] = 1
    input_model: ClassVar[type[BaseModel]] = StructureAgentInput
    output_model: ClassVar[type[BaseModel]] = StructureAgentOutput
    read_scopes: ClassVar[set[MemoryScope]] = {MemoryScope.SESSION}
    write_scopes: ClassVar[set[MemoryScope]] = {MemoryScope.SESSION}

    @classmethod
    def input_schema(cls) -> dict[str, object]:
        """input_schema."""
        return StructureAgentInput.model_json_schema()

    @classmethod
    def output_schema(cls) -> dict[str, object]:
        """output_schema."""
        return StructureAgentOutput.model_json_schema()

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
        StructureAgentInput.model_validate(payload)
        return Decision(
            agent_name=self.name,
            rationale="noop_structure_selection",
            requested_tools=[],
            next_tasks=[],
            confidence=0.0,
            input_refs=[],
            memory_refs=[],
            rules_triggered=["noop"],
            confidence_impact=[],
        )


StructureAgent.decide.__annotations__["return"] = Decision
