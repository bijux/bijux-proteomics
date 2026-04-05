# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from datetime import datetime
from enum import Enum

import pytest
from pydantic import BaseModel

from agentic_proteins.core.execution import ExecutionGraph, ExecutionTask
from agentic_proteins.core.tooling import SchemaDefinition, ToolContract, ToolInvocationSpec
from agentic_proteins.memory.schemas import MemoryScope
from agentic_proteins.registry.agents import AgentRegistry
from agentic_proteins.registry.tools import ToolRegistry
from agentic_proteins.state.schemas import StateSnapshot
from agentic_proteins.validation import agents as agents_module
from agentic_proteins.validation import state as state_module
from agentic_proteins.validation import tools as tools_module


class ExampleEnum(Enum):
    ONE = "one"
    TWO = "two"


class NestedModel(BaseModel):
    nested: str


class InputModel(BaseModel):
    required_text: str
    required_enum: ExampleEnum
    required_nested: NestedModel
    optional_list: list[str] | None = None
    optional_dict: dict[str, str] | None = None


def _agent_class(**overrides: object) -> type:
    class Agent:
        name = "planner"
        capabilities = ["plan"]
        allowed_tools = {"heuristic_proxy"}
        cost_budget = 1.0
        latency_budget_ms = 10
        read_scopes = {MemoryScope.SESSION}
        write_scopes = {MemoryScope.SESSION}
        input_model = InputModel

    for key, value in overrides.items():
        setattr(Agent, key, value)
    return Agent


def _register_tool() -> None:
    ToolRegistry.clear()
    ToolRegistry.register(
        ToolContract(
            tool_name="heuristic_proxy",
            version="1.0",
            input_schema=SchemaDefinition(schema_name="in", json_schema="{}"),
            output_schema=SchemaDefinition(schema_name="out", json_schema="{}"),
            cost_estimate=1.0,
            latency_estimate_ms=1,
        )
    )


def test_validate_tool_contracts() -> None:
    schema = SchemaDefinition(schema_name="in", json_schema="{}")
    contract = ToolContract(
        tool_name="tool",
        version="1.0",
        input_schema=schema,
        output_schema=schema,
        cost_estimate=1.0,
        latency_estimate_ms=1,
    )
    tools_module.validate_tool_contract(contract)
    with pytest.raises(ValueError, match="Input schema"):
        tools_module.validate_tool_contract(contract.model_copy(update={"input_schema": "bad"}))
    with pytest.raises(ValueError, match="Output schema"):
        tools_module.validate_tool_contract(contract.model_copy(update={"output_schema": "bad"}))
    with pytest.raises(ValueError, match="non-empty"):
        empty = SchemaDefinition.model_construct(schema_name="in", json_schema="")
        tools_module.validate_tool_contract(
            contract.model_copy(update={"input_schema": empty})
        )
    with pytest.raises(ValueError, match="cost estimate"):
        tools_module.validate_tool_contract(contract.model_copy(update={"cost_estimate": 0.0}))
    with pytest.raises(ValueError, match="latency estimate"):
        tools_module.validate_tool_contract(contract.model_copy(update={"latency_estimate_ms": 0}))


def test_validate_tools_for_agents() -> None:
    _register_tool()
    tools_module.validate_tools_for_agents({"planner": {"heuristic_proxy"}})
    with pytest.raises(ValueError, match="unknown tools"):
        tools_module.validate_tools_for_agents({"planner": {"missing"}})
    ToolRegistry.clear()


def test_validate_agent_and_registry() -> None:
    _register_tool()
    agents_module.validate_agent(_agent_class())
    with pytest.raises(ValueError, match="must not be empty"):
        agents_module.validate_agent(_agent_class(capabilities=[]))
    with pytest.raises(ValueError, match="outside registry"):
        agents_module.validate_agent(_agent_class(allowed_tools={"bad"}))
    with pytest.raises(ValueError, match="cost budget"):
        agents_module.validate_agent(_agent_class(cost_budget=0))
    with pytest.raises(ValueError, match="latency budget"):
        agents_module.validate_agent(_agent_class(latency_budget_ms=0))
    with pytest.raises(ValueError, match="read scopes"):
        agents_module.validate_agent(_agent_class(read_scopes={"bad"}))
    with pytest.raises(ValueError, match="Critic agents may not write"):
        agents_module.validate_agent(
            _agent_class(name="critic", write_scopes={MemoryScope.PERSISTENT})
        )
    AgentRegistry.clear()
    AgentRegistry.register(_agent_class())
    agents_module.validate_registry_entries()
    AgentRegistry.clear()
    ToolRegistry.clear()


def test_validate_agents_and_critic_input() -> None:
    _register_tool()
    agents_module.validate_agents_and_tools([_agent_class()])
    class CriticPayload:
        critic_name = "critic"
        target_agent_name = "critic"
    with pytest.raises(ValueError, match="may not evaluate"):
        agents_module.validate_critic_input(CriticPayload())
    ToolRegistry.clear()


def test_validate_state_and_execution_graph() -> None:
    snapshot = StateSnapshot(
        state_id="s1",
        plan_fingerprint="p1",
        timestamp=datetime.utcnow(),
    )
    state_module.validate_state_snapshot(snapshot)
    with pytest.raises(ValueError, match="state_id"):
        bad = snapshot.model_copy(update={"state_id": ""})
        state_module.validate_state_snapshot(bad)
    task = ExecutionTask(
        task_id="t1",
        tool_invocation=ToolInvocationSpec(
            invocation_id="inv",
            tool_name="heuristic_proxy",
            tool_version="1.0",
            inputs=[],
            expected_outputs=[],
            constraints=[],
            origin_task_id="origin",
        ),
        input_state_id="s1",
        expected_output_schema="schema",
    )
    graph = ExecutionGraph(tasks={"t1": task}, dependencies={}, entry_tasks=["t1"])
    state_module.validate_execution_graph(graph)
    with pytest.raises(ValueError, match="Unknown execution entry task"):
        state_module.validate_execution_graph(graph.model_copy(update={"entry_tasks": ["missing"]}))
    cyclic = ExecutionGraph(tasks={"t1": task}, dependencies={"t1": ["t1"]}, entry_tasks=["t1"])
    with pytest.raises(ValueError, match="cycle"):
        state_module.validate_execution_graph(cyclic)


def test_placeholder_helpers() -> None:
    class ComplexInput(BaseModel):
        items: list[int]
        mapping: dict[str, str]
        optional_value: int | None

    payload = agents_module._minimal_payload(ComplexInput)
    assert payload["items"] == []
    assert payload["mapping"] == {}
    assert payload["optional_value"] is None
    assert agents_module._placeholder_for_type(ExampleEnum) == ExampleEnum.ONE
