# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Input validation agent."""

from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel

from agentic_proteins.agents.base import AgentRole
from agentic_proteins.agents.schemas import (
    AgentMetadata,
    InputValidationAgentInput,
    InputValidationAgentOutput,
)
from agentic_proteins.memory.schemas import MemoryScope
from agentic_proteins.validation.agents import validate_agent


class InputValidationAgent(AgentRole):
    """InputValidationAgent."""

    name: ClassVar[str] = "input_validation"
    capabilities: ClassVar[set[str]] = {"input validation"}
    allowed_tools: ClassVar[set[str]] = set()
    cost_budget: ClassVar[float] = 1.0
    latency_budget_ms: ClassVar[int] = 1
    input_model: ClassVar[type[BaseModel]] = InputValidationAgentInput
    output_model: ClassVar[type[BaseModel]] = InputValidationAgentOutput
    read_scopes: ClassVar[set[MemoryScope]] = {MemoryScope.SESSION}
    write_scopes: ClassVar[set[MemoryScope]] = {MemoryScope.SESSION}

    @classmethod
    def input_schema(cls) -> dict:
        """input_schema."""
        return InputValidationAgentInput.model_json_schema()

    @classmethod
    def output_schema(cls) -> dict:
        """output_schema."""
        return InputValidationAgentOutput.model_json_schema()

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

    def decide(self, payload: BaseModel) -> InputValidationAgentOutput:
        """decide."""
        validation_input = InputValidationAgentInput.model_validate(payload)
        validate_agent(type(self))
        warnings: list[str] = []
        errors: list[str] = []
        sequence = validation_input.sequence.strip().upper()
        if not sequence:
            errors.append("empty_sequence")
        allowed = set("ACDEFGHIKLMNPQRSTVWY")
        invalid = sorted({aa for aa in sequence if aa not in allowed})
        if invalid:
            errors.append("invalid_residues")
            warnings.append(f"invalid:{','.join(invalid)}")
        return InputValidationAgentOutput(
            valid=not errors,
            warnings=warnings,
            errors=errors,
        )


InputValidationAgent.decide.__annotations__["return"] = InputValidationAgentOutput
