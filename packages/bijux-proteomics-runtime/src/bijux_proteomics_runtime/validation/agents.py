# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Agent validation helpers."""

from __future__ import annotations

from enum import Enum
from typing import Any, Protocol, cast, get_args, get_origin

from pydantic import BaseModel

from bijux_proteomics_runtime.memory.schemas import MemoryScope
from bijux_proteomics_runtime.registry.agents import AgentRegistry
from bijux_proteomics_runtime.validation.tools import validate_tools_for_agents

__all__ = [
    "ALLOWED_TOOL_NAMESPACE",
    "_minimal_payload",
    "_placeholder_for_type",
    "validate_agent",
    "validate_agents_and_tools",
    "validate_critic_input",
    "validate_registry_entries",
]

ALLOWED_TOOL_NAMESPACE: set[str] = {
    "motif_scan",
    "sequence_validator",
    "heuristic_proxy",
    "local_esmfold",
    "local_rosettafold",
    "api_openprotein_esmfold",
    "api_openprotein_alphafold",
    "api_colabfold",
    "metric_aggregator",
    "confidence_estimator",
}


class _AgentRoleLike(Protocol):
    """_AgentRoleLike."""

    name: str
    capabilities: list[str]
    allowed_tools: set[str]
    cost_budget: float
    latency_budget_ms: int
    read_scopes: set[MemoryScope]
    write_scopes: set[MemoryScope]
    input_model: type[BaseModel]


class _CriticInputLike(Protocol):
    """_CriticInputLike."""

    critic_name: str
    target_agent_name: str


def validate_agent(agent: type[Any]) -> None:
    """validate_agent."""
    role = cast(type[_AgentRoleLike], agent)
    if not role.capabilities:
        raise ValueError("Agent capabilities must not be empty.")
    if not role.allowed_tools.issubset(ALLOWED_TOOL_NAMESPACE):
        invalid = role.allowed_tools - ALLOWED_TOOL_NAMESPACE
        raise ValueError(
            f"Agent uses tools outside registry namespace: {sorted(invalid)}"
        )
    if role.cost_budget <= 0:
        raise ValueError("Agent cost budget must be > 0.")
    if role.latency_budget_ms <= 0:
        raise ValueError("Agent latency budget must be > 0.")
    if not role.read_scopes.issubset(set(MemoryScope)):
        raise ValueError("Agent read scopes must be valid MemoryScope values.")
    if not role.write_scopes.issubset(set(MemoryScope)):
        raise ValueError("Agent write scopes must be valid MemoryScope values.")
    if role.name == "critic" and MemoryScope.PERSISTENT in role.write_scopes:
        raise ValueError("Critic agents may not write persistent memory.")
    payload = _minimal_payload(role.input_model)
    role.input_model.model_validate(payload)


def _minimal_payload(model: type[BaseModel]) -> dict[str, object]:
    """_minimal_payload."""
    payload: dict[str, object] = {}
    for name, field in model.model_fields.items():
        if not field.is_required():
            continue
        annotation = field.annotation
        payload[name] = _placeholder_for_type(annotation)
    return payload


def _placeholder_for_type(annotation: object) -> object:
    """_placeholder_for_type."""
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin is None and isinstance(annotation, type):
        if issubclass(annotation, BaseModel):
            return _minimal_payload(annotation)
        if issubclass(annotation, Enum):
            members = list(annotation)
            return members[0] if members else "placeholder"
        if issubclass(annotation, str):
            return "placeholder"
        if issubclass(annotation, bool):
            return False
        if issubclass(annotation, int):
            return 1
        if issubclass(annotation, float):
            return 1.0
    if origin is list:
        return []
    if origin is dict:
        return {}
    if args:
        if type(None) in args:
            return None
        return _placeholder_for_type(args[0])
    return "placeholder"


def validate_agents_and_tools(agents: list[type[_AgentRoleLike]]) -> None:
    """validate_agents_and_tools."""
    for agent in agents:
        validate_agent(agent)
    agent_tools = {agent.name: set(agent.allowed_tools) for agent in agents}
    validate_tools_for_agents(agent_tools)


def validate_critic_input(payload: _CriticInputLike) -> None:
    """validate_critic_input."""
    if payload.critic_name and payload.critic_name == payload.target_agent_name:
        raise ValueError("Critic may not evaluate its own outputs.")


def validate_registry_entries() -> None:
    """validate_registry_entries."""
    for agent in AgentRegistry.list():
        validate_agent(agent)
