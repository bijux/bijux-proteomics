# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Execution result integration."""

from __future__ import annotations

from datetime import UTC, datetime

from bijux_proteomics_runtime.execution.agents.planning.schemas import Plan
from bijux_proteomics_runtime.support.primitives.decisions import Decision
from bijux_proteomics_runtime.execution.tools.schemas import ToolResult
from bijux_proteomics_runtime.state import MemoryStore
from bijux_proteomics_runtime.state.memory_records import (
    MemoryRecord,
    MemoryScope,
    ToolResultPayload,
)
from bijux_proteomics_runtime.state import snapshot_state
from bijux_proteomics_runtime.state.schemas import StateSnapshot


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
