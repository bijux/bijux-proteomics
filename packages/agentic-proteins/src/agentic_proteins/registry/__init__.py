"""Compatibility forwarding module for canonical runtime registry ownership."""

from bijux_proteomics_runtime.agents.catalog import AgentCatalog as AgentRegistry
from bijux_proteomics_runtime.tools.catalog import ToolCatalog as ToolRegistry

__all__ = ["AgentRegistry", "ToolRegistry"]
