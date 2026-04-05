# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from agentic_proteins.agents.planning.compiler import compile_plan_to_execution
from agentic_proteins.execution.compiler.boundary import evaluate_failure
from agentic_proteins.execution.runtime.integration import integrate_execution_result
from agentic_proteins.core.decisions import Decision
from agentic_proteins.execution.schemas import ExecutionGraph, ExecutionTask, RetryPolicy
from agentic_proteins.memory.schemas import MemoryRecord, MemoryScope, ToolResultPayload
from agentic_proteins.agents.planning.schemas import Plan, TaskSpec
from agentic_proteins.tools.schemas import InvocationInput, ToolInvocationSpec, ToolResult
from agentic_proteins.validation.state import validate_execution_graph
from agentic_proteins.registry.agents import AgentRegistry


def register_planner() -> None:
    AgentRegistry._registry.clear()
    AgentRegistry._locked = False
    from agentic_proteins.agents.planning.planner import PlannerAgent

    AgentRegistry.register(PlannerAgent)


def test_execution_graph_validation() -> None:
    task = ExecutionTask(
        task_id="t1",
        tool_invocation=ToolInvocationSpec(
            invocation_id="inv1",
            tool_name="sequence_validator",
            tool_version="1.0",
            inputs=[InvocationInput(name="seq", value="ACD")],
            expected_outputs=[],
            constraints=[],
            origin_task_id="t1",
        ),
        input_state_id="s1",
        expected_output_schema="schema",
        retry_policy=RetryPolicy(),
        timeout_ms=10,
    )
    graph = ExecutionGraph(
        tasks={"t1": task},
        dependencies={"t1": []},
        entry_tasks=["t1"],
        exit_conditions=["done"],
    )
    validate_execution_graph(graph)


def test_compile_plan_to_execution_requires_invocations() -> None:
    register_planner()
    plan = Plan(
        tasks={
            "t1": TaskSpec(
                task_id="t1",
                agent_name="planner",
                objective="planning",
                required_capabilities=["planning"],
            )
        },
        dependencies={"t1": []},
        entry_tasks=["t1"],
        exit_conditions=["done"],
    )
    with pytest.raises(ValueError):
        compile_plan_to_execution(plan, decisions=[])


def test_compile_plan_to_execution_success() -> None:
    register_planner()
    plan = Plan(
        tasks={
            "t1": TaskSpec(
                task_id="t1",
                agent_name="planner",
                objective="planning",
                required_capabilities=["planning"],
            )
        },
        dependencies={"t1": []},
        entry_tasks=["t1"],
        exit_conditions=["done"],
    )
    invocation = ToolInvocationSpec(
        invocation_id="inv1",
        tool_name="sequence_validator",
        tool_version="1.0",
        inputs=[InvocationInput(name="seq", value="ACD")],
        expected_outputs=[],
        constraints=[],
        origin_task_id="t1",
    )
    decision = Decision(
        agent_name="planner",
        rationale="r",
        requested_tools=[invocation],
        confidence=0.5,
        input_refs=["sequence:ACD"],
        memory_refs=["memory:session"],
        rules_triggered=["test_execution"],
        confidence_impact=["baseline_assumed"],
    )
    graph = compile_plan_to_execution(plan, [decision])
    assert "t1" in graph.tasks


def test_failure_policy() -> None:
    result = ToolResult(
        invocation_id="inv1",
        tool_name="sequence_validator",
        status="failure",
        outputs=[],
        metrics=[],
        error=None,
    )
    assert evaluate_failure(result, fatal_errors=set(), replan_errors=set()) == "continue"


def test_integrate_execution_result_appends_to_store() -> None:
    register_planner()
    plan = Plan(
        tasks={
            "t1": TaskSpec(
                task_id="t1",
                agent_name="planner",
                objective="planning",
                required_capabilities=["planning"],
            )
        },
        dependencies={"t1": []},
        entry_tasks=["t1"],
        exit_conditions=["done"],
    )

    class FakeStore:
        def __init__(self) -> None:
            self.records: list[MemoryRecord] = []

        def write(self, record: MemoryRecord) -> None:
            self.records.append(record)

        def query(self, scope: MemoryScope, _filters: list[str]) -> list[MemoryRecord]:
            return [r for r in self.records if r.scope == scope]

        def snapshot(self) -> list[MemoryRecord]:
            return list(self.records)

    store = FakeStore()
    decision = Decision(
        agent_name="planner",
        rationale="r",
        confidence=0.1,
        input_refs=["sequence:ACD"],
        memory_refs=["memory:session"],
        rules_triggered=["test_execution"],
        confidence_impact=["baseline_assumed"],
    )
    result = ToolResult(
        invocation_id="inv1",
        tool_name="sequence_validator",
        status="failure",
        outputs=[],
        metrics=[],
        error=None,
    )
    snapshot = integrate_execution_result(plan, [decision], store, result, "local")
    assert snapshot.plan_fingerprint == plan.fingerprint()
    assert isinstance(store.records[0].payload, ToolResultPayload)
