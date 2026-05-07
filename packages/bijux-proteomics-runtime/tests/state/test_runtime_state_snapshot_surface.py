from __future__ import annotations

from datetime import UTC, datetime

import pytest

from bijux_proteomics_runtime.state.memory_records import (
    DecisionPayload,
    MemoryRecord,
    MemoryScope,
    ToolResultPayload,
)
from bijux_proteomics_runtime.state.snapshot import snapshot_replan, snapshot_state
from bijux_proteomics_runtime.support.primitives.decisions import Decision
from bijux_proteomics_runtime.support.primitives.tooling import ToolResult


class _Plan:
    def __init__(self, fingerprint: str) -> None:
        self._fingerprint = fingerprint

    def fingerprint(self) -> str:
        return self._fingerprint


def _decision(agent_name: str, rationale: str) -> Decision:
    return Decision(
        agent_name=agent_name,
        rationale=rationale,
        requested_tools=[],
        next_tasks=[],
        confidence=0.5,
    )


def _memory_record(record_id: str, agent_name: str) -> MemoryRecord:
    return MemoryRecord(
        record_id=record_id,
        scope=MemoryScope.SESSION,
        producer=agent_name,
        payload=DecisionPayload(decision=_decision(agent_name, f"{agent_name}-reason")),
        created_at=datetime(2026, 5, 7, tzinfo=UTC),
    )


def test_snapshot_state_keeps_fingerprint_stable_across_input_order() -> None:
    plan = _Plan("plan-alpha")
    decision_a = _decision("agent-a", "inspect")
    decision_b = _decision("agent-b", "review")
    memory_a = _memory_record("record-a", "agent-a")
    memory_b = _memory_record("record-b", "agent-b")

    first = snapshot_state(
        plan=plan,
        decisions=[decision_b, decision_a],
        memory=[memory_b, memory_a],
    )
    second = snapshot_state(
        plan=plan,
        decisions=[decision_a, decision_b],
        memory=[memory_a, memory_b],
    )

    assert first.state_id == second.state_id
    assert first.plan_fingerprint == "plan-alpha"


def test_state_snapshot_is_immutable_after_creation() -> None:
    snapshot = snapshot_state(plan=_Plan("plan-beta"), decisions=[], memory=[])

    with pytest.raises(TypeError, match="immutable"):
        snapshot.state_id = "changed"


def test_runtime_state_payloads_accept_typed_tool_results_and_replans() -> None:
    record = MemoryRecord(
        record_id="tool-record",
        scope=MemoryScope.PERSISTENT,
        producer="agent-c",
        payload=ToolResultPayload(
            result=ToolResult(
                invocation_id="invoke-1",
                tool_name="msfragger-import",
                status="success",
                outputs=[],
                metrics=[],
            )
        ),
        created_at=datetime(2026, 5, 7, tzinfo=UTC),
    )

    snapshot = snapshot_replan(
        plan=_Plan("plan-gamma"),
        decisions=[],
        memory=[record],
        parent_state_id="parent-state",
    )

    assert record.payload.schema_type == "tool_result"
    assert snapshot.parent_state_id == "parent-state"

