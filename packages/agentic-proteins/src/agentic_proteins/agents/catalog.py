"""Compatibility agent-catalog entrypoints."""

from bijux_proteomics_runtime.execution.agents.catalog import AgentCatalog

AgentRegistry = AgentCatalog

__all__ = ["AgentCatalog", "AgentRegistry"]
