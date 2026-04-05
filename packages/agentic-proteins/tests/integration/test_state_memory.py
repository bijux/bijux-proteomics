# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from agentic_proteins.registry.agents import AgentRegistry
from agentic_proteins.core.decisions import Decision
from agentic_proteins.memory.schemas import DecisionPayload, MemoryRecord, MemoryScope
from agentic_proteins.agents.planning.schemas import Plan, TaskSpec
from agentic_proteins.state.schemas import StateSnapshot
from agentic_proteins.state import snapshot_state
from agentic_proteins.memory import MemoryStore


def sample_plan() -> Plan:
    AgentRegistry._registry.clear()
    AgentRegistry._locked = False
    from agentic_proteins.agents.planning.planner import PlannerAgent

    AgentRegistry.register(PlannerAgent)
    task = TaskSpec(
        task_id="t1",
        agent_name="planner",
        objective="planning",
        required_capabilities=["planning"],
    )
    return Plan(
        tasks={"t1": task},
        dependencies={"t1": []},
        entry_tasks=["t1"],
        exit_conditions=["done"],
    )


def test_state_snapshot_immutable() -> None:
    plan = sample_plan()
    decision = Decision(
        agent_name="planner",
        rationale="r",
        confidence=0.5,
        input_refs=["sequence:ACD"],
        memory_refs=["memory:session"],
        rules_triggered=["test_state"],
        confidence_impact=["baseline_assumed"],
    )
    record = MemoryRecord(
        record_id="r1",
        scope=MemoryScope.SESSION,
        producer="planner",
        payload=DecisionPayload(decision=decision),
        created_at=datetime.now(UTC),
        expires_at=None,
    )
    snapshot = snapshot_state(plan, [decision], [record])
    with pytest.raises(TypeError):
        snapshot.state_id = "mutate"


def test_snapshot_does_not_mutate_inputs() -> None:
    plan = sample_plan()
    decision = Decision(
        agent_name="planner",
        rationale="r",
        confidence=0.5,
        input_refs=["sequence:ACD"],
        memory_refs=["memory:session"],
        rules_triggered=["test_state"],
        confidence_impact=["baseline_assumed"],
    )
    record = MemoryRecord(
        record_id="r1",
        scope=MemoryScope.SESSION,
        producer="planner",
        payload=DecisionPayload(decision=decision),
        created_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )
    decisions = [decision]
    memory = [record]
    snapshot_state(plan, decisions, memory)
    assert decisions == [decision]
    assert memory == [record]


def test_memory_store_interface_is_abstract() -> None:
    with pytest.raises(TypeError):
        MemoryStore()


def test_state_snapshot_fields() -> None:
    plan = sample_plan()
    decision = Decision(
        agent_name="planner",
        rationale="r",
        confidence=0.5,
        input_refs=["sequence:ACD"],
        memory_refs=["memory:session"],
        rules_triggered=["test_state"],
        confidence_impact=["baseline_assumed"],
    )
    snapshot = snapshot_state(plan, [decision], [])
    assert isinstance(snapshot, StateSnapshot)
    assert snapshot.plan_fingerprint == plan.fingerprint()
