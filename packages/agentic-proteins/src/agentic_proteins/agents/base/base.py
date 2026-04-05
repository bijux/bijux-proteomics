# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Agent contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from pydantic import BaseModel

from agentic_proteins.agents.schemas import AgentMetadata
from agentic_proteins.core.decisions import Decision
from agentic_proteins.memory.schemas import MemoryScope


class AgentRole(ABC):
    """AgentRole."""

    name: ClassVar[str]
    capabilities: ClassVar[set[str]]
    allowed_tools: ClassVar[set[str]]
    cost_budget: ClassVar[float]
    latency_budget_ms: ClassVar[int]
    read_scopes: ClassVar[set[MemoryScope]]
    write_scopes: ClassVar[set[MemoryScope]]
    input_model: ClassVar[type[BaseModel]]
    output_model: ClassVar[type[BaseModel]]

    def validate_requested_tools(self, tools: set[str]) -> None:
        """validate_requested_tools."""
        unauthorized = tools - self.allowed_tools
        if unauthorized:
            raise ValueError(f"Requested tools not allowed: {sorted(unauthorized)}")

    def validate_memory_write(self, scopes: set[MemoryScope]) -> None:
        """validate_memory_write."""
        unauthorized = scopes - self.write_scopes
        if unauthorized:
            raise ValueError(f"Write scopes not allowed: {sorted(unauthorized)}")

    @classmethod
    @abstractmethod
    def input_schema(cls) -> dict:
        """Return a strict JSON schema for agent inputs."""

    @classmethod
    @abstractmethod
    def output_schema(cls) -> dict:
        """Return a strict JSON schema for agent outputs."""

    @classmethod
    @abstractmethod
    def metadata(cls) -> AgentMetadata:
        """Return agent metadata for registry and planning."""

    @abstractmethod
    def decide(self, payload: BaseModel) -> BaseModel:
        """Return a decision model without performing actions."""


DecisionModel = Decision
