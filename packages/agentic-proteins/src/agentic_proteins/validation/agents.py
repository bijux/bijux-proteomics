"""Compatibility forwarding module for canonical runtime validation ownership."""

from bijux_proteomics_runtime.agents.contracts import (
    ALLOWED_TOOL_NAMESPACE,
    _minimal_payload,
    _placeholder_for_type,
    validate_agent,
    validate_agents_and_tools,
    validate_critic_input,
    validate_agent_catalog as validate_registry_entries,
)

__all__ = [
    "ALLOWED_TOOL_NAMESPACE",
    "_minimal_payload",
    "_placeholder_for_type",
    "validate_agent",
    "validate_agents_and_tools",
    "validate_critic_input",
    "validate_registry_entries",
]
