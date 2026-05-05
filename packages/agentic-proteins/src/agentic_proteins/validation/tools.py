"""Compatibility forwarding module for canonical runtime validation ownership."""

from bijux_proteomics_runtime.execution.tools.contracts import (
    validate_tool_contract,
    validate_tools_for_agents,
)

__all__ = ["validate_tool_contract", "validate_tools_for_agents"]
