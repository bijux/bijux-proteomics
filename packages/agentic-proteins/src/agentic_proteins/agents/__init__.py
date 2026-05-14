"""Compatibility agent entrypoints."""

from __future__ import annotations

from bijux_proteomics_runtime.execution.agents.catalog import AgentCatalog
from bijux_proteomics_runtime.execution.agents.contracts import (
    validate_agent,
    validate_agents_and_tools,
)

AgentRegistry = AgentCatalog

__all__ = [
    "AgentCatalog",
    "AgentRegistry",
    "validate_agent",
    "validate_agents_and_tools",
]
