# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Execution result integration."""

from __future__ import annotations

from datetime import UTC, datetime

from agentic_proteins.agents.planning.schemas import Plan
from agentic_proteins.core.decisions import Decision
from agentic_proteins.memory import MemoryStore
from agentic_proteins.memory.schemas import MemoryRecord, MemoryScope, ToolResultPayload
from agentic_proteins.state import snapshot_state
from agentic_proteins.state.schemas import StateSnapshot
from agentic_proteins.tools.schemas import ToolResult


def tool_result_to_memory(
    result: ToolResult,
    scope: MemoryScope,
    producer: str,
) -> MemoryRecord:
    """tool_result_to_memory."""
    return MemoryRecord(
        record_id=result.invocation_id,
        scope=scope,
        producer=producer,
        payload=ToolResultPayload(result=result),
        created_at=datetime.now(UTC),
        expires_at=None,
    )


def integrate_execution_result(
    plan: Plan,
    decisions: list[Decision],
    memory_store: MemoryStore,
    result: ToolResult,
    producer: str,
) -> StateSnapshot:
    """integrate_execution_result."""
    memory_record = tool_result_to_memory(
        result,
        scope=MemoryScope.SESSION,
        producer=producer,
    )
    memory_store.write(memory_record)
    return snapshot_state(plan, decisions, memory_store.snapshot())
