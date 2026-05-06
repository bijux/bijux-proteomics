"""Compatibility agent-contract entrypoints."""

from bijux_proteomics_runtime.execution.agents.contracts import (
    ALLOWED_TOOL_NAMESPACE,
    _minimal_payload,
    _placeholder_for_type,
    validate_agent,
    validate_agents_and_tools,
    validate_critic_input,
    validate_agent_catalog,
)

__all__ = [
    "ALLOWED_TOOL_NAMESPACE",
    "_minimal_payload",
    "_placeholder_for_type",
    "validate_agent",
    "validate_agents_and_tools",
    "validate_critic_input",
    "validate_agent_catalog",
]

validate_registry_entries = validate_agent_catalog
