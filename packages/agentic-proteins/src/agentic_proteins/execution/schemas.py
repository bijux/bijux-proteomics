# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Execution schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from agentic_proteins.core.execution import (
    ExecutionContext,
    ExecutionGraph,
    ExecutionTask,
    RetryPolicy,
)
from agentic_proteins.core.tooling import ToolResult


class ExecutionTrace(BaseModel):
    """ExecutionTrace."""

    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(..., min_length=1, description="Execution task id.")
    tool_name: str = Field(..., min_length=1, description="Tool name.")
    status: str = Field(..., min_length=1, description="success or failure.")
    started_at: str = Field(..., min_length=1, description="Start timestamp.")
    finished_at: str = Field(..., min_length=1, description="End timestamp.")
    observed_cost: float = Field(0.0, ge=0.0, description="Observed cost.")
    observed_latency_ms: int = Field(0, ge=0, description="Observed latency.")
    result: ToolResult | None = Field(default=None, description="Tool result.")


__all__ = [
    "ExecutionContext",
    "ExecutionGraph",
    "ExecutionTask",
    "ExecutionTrace",
    "RetryPolicy",
]
