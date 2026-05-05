# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Tool contract validation for runtime execution catalogs."""

from __future__ import annotations

from bijux_proteomics_runtime.core.tooling import SchemaDefinition, ToolContract
from bijux_proteomics_runtime.execution.tools.catalog import ToolCatalog

__all__ = [
    "validate_tool_contract",
    "validate_tools_for_agents",
]


def validate_tool_contract(contract: ToolContract) -> None:
    """Validate one runtime tool contract."""
    if not isinstance(contract.input_schema, SchemaDefinition):
        raise ValueError("Input schema must be a SchemaDefinition.")
    if not isinstance(contract.output_schema, SchemaDefinition):
        raise ValueError("Output schema must be a SchemaDefinition.")
    if not contract.input_schema.json_schema or not contract.output_schema.json_schema:
        raise ValueError("Tool schemas must be non-empty.")
    if contract.cost_estimate <= 0:
        raise ValueError("Tool cost estimate must be > 0.")
    if contract.latency_estimate_ms <= 0:
        raise ValueError("Tool latency estimate must be > 0.")


def validate_tools_for_agents(agent_names: dict[str, set[str]]) -> None:
    """Validate that each agent references known runtime tools."""
    tools = {name for name, _version in ToolCatalog._registry}
    for agent_name, required_tools in agent_names.items():
        missing = required_tools - tools
        if missing:
            raise ValueError(
                f"Agent {agent_name} references unknown tools: {sorted(missing)}"
            )
    for contract in ToolCatalog.list():
        validate_tool_contract(contract)
