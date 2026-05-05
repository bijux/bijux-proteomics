"""Compatibility forwarding module for canonical runtime registry ownership."""

from agentic_proteins.registry.agents import AgentRegistry
from agentic_proteins.registry.tools import ToolRegistry

__all__ = ["AgentRegistry", "ToolRegistry"]
