"""Compatibility forwarding module for canonical runtime registry ownership."""

from bijux_proteomics_runtime.execution.agents.catalog import AgentCatalog as AgentRegistry
from bijux_proteomics_runtime.execution.tools.catalog import ToolCatalog as ToolRegistry

__all__ = ["AgentRegistry", "ToolRegistry"]
