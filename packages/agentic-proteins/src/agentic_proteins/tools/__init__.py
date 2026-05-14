"""Compatibility tool entrypoints."""

from __future__ import annotations

from bijux_proteomics_runtime.execution.tools.base import Tool
from bijux_proteomics_runtime.execution.tools.catalog import ToolCatalog
from bijux_proteomics_runtime.execution.tools.contracts import (
    validate_tool_contract,
    validate_tools_for_agents,
)
from bijux_proteomics_runtime.execution.tools.heuristic import HeuristicStructureTool

ToolRegistry = ToolCatalog

__all__ = [
    "HeuristicStructureTool",
    "Tool",
    "ToolCatalog",
    "ToolRegistry",
    "validate_tool_contract",
    "validate_tools_for_agents",
]
