"""Compatibility tool-catalog entrypoints."""

from bijux_proteomics_runtime.execution.tools.catalog import ToolCatalog

ToolRegistry = ToolCatalog

__all__ = ["ToolCatalog", "ToolRegistry"]
