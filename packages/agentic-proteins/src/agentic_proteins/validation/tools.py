# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Tool validation helpers."""

from __future__ import annotations

from agentic_proteins.core.tooling import SchemaDefinition, ToolContract
from agentic_proteins.registry.tools import ToolRegistry


def validate_tool_contract(contract: ToolContract) -> None:
    """validate_tool_contract."""
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
    """validate_tools_for_agents."""
    tools = {name for name, _version in ToolRegistry._registry}
    for agent_name, required_tools in agent_names.items():
        missing = required_tools - tools
        if missing:
            raise ValueError(
                f"Agent {agent_name} references unknown tools: {sorted(missing)}"
            )
    for contract in ToolRegistry.list():
        validate_tool_contract(contract)
