# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""State snapshot helpers."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from typing import Protocol

from agentic_proteins.core.decisions import Decision
from agentic_proteins.core.hashing import sha256_hex
from agentic_proteins.memory.schemas import MemoryRecord
from agentic_proteins.state.schemas import StateSnapshot


class _PlanLike(Protocol):
    """_PlanLike."""

    def fingerprint(self) -> str:
        """Return a stable fingerprint for the plan."""
        ...


def snapshot_state(
    plan: _PlanLike,
    decisions: list[Decision],
    memory: list[MemoryRecord],
    parent_state_id: str | None = None,
) -> StateSnapshot:
    """snapshot_state."""
    plan_fingerprint = plan.fingerprint()
    normalized = {
        "plan_fingerprint": plan_fingerprint,
        "decisions": [
            d.model_dump()
            for d in sorted(
                decisions,
                key=lambda item: (
                    item.agent_name,
                    item.rationale,
                    item.confidence,
                    [tool.model_dump() for tool in item.requested_tools],
                    item.next_tasks,
                ),
            )
        ],
        "memory": [
            {
                "record_id": m.record_id,
                "scope": m.scope.value,
                "producer": m.producer,
                "payload": m.payload.model_dump(),
            }
            for m in sorted(
                memory,
                key=lambda item: (item.record_id, item.producer, item.scope.value),
            )
        ],
    }
    payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    state_id = sha256_hex(payload)
    return StateSnapshot(
        state_id=state_id,
        parent_state_id=parent_state_id,
        plan_fingerprint=plan_fingerprint,
        timestamp=datetime.now(UTC),
        agent_decisions=list(decisions),
        artifacts=[],
        metrics=[],
        confidence_summary=[],
    )


def snapshot_replan(
    plan: _PlanLike,
    decisions: list[Decision],
    memory: list[MemoryRecord],
    parent_state_id: str,
) -> StateSnapshot:
    """snapshot_replan."""
    return snapshot_state(
        plan=plan,
        decisions=decisions,
        memory=memory,
        parent_state_id=parent_state_id,
    )
