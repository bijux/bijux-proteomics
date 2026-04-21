# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Memory schemas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from agentic_proteins.core.decisions import Decision
from agentic_proteins.core.tooling import ToolResult


class MemoryScope(Enum):
    """MemoryScope."""

    EPHEMERAL = "EPHEMERAL"
    SESSION = "SESSION"
    PERSISTENT = "PERSISTENT"


class DecisionPayload(BaseModel):
    """DecisionPayload."""

    model_config = ConfigDict(extra="forbid")

    schema_type: Literal["decision"] = "decision"
    decision: Decision = Field(..., description="Recorded decision.")


class PlanPayload(BaseModel):
    """PlanPayload."""

    model_config = ConfigDict(extra="forbid")

    schema_type: Literal["plan"] = "plan"
    plan_fingerprint: str = Field(
        ..., min_length=1, description="Plan fingerprint identifier."
    )


class StatePayload(BaseModel):
    """StatePayload."""

    model_config = ConfigDict(extra="forbid")

    schema_type: Literal["state"] = "state"
    state_id: str = Field(..., min_length=1, description="State snapshot identifier.")


class ToolResultPayload(BaseModel):
    """ToolResultPayload."""

    model_config = ConfigDict(extra="forbid")

    schema_type: Literal["tool_result"] = "tool_result"
    result: ToolResult = Field(..., description="Tool execution result.")


MemoryPayload = Annotated[
    DecisionPayload | PlanPayload | StatePayload | ToolResultPayload,
    Field(discriminator="schema_type"),
]


class MemoryRecord(BaseModel):
    """MemoryRecord."""

    model_config = ConfigDict(extra="forbid")

    record_id: str = Field(..., min_length=1, description="Record identifier.")
    scope: MemoryScope = Field(..., description="Memory scope.")
    producer: str = Field(..., min_length=1, description="Producing agent name.")
    payload: MemoryPayload = Field(..., description="Typed payload.")
    created_at: datetime = Field(..., description="Creation timestamp.")
    expires_at: datetime | None = Field(default=None, description="Expiry timestamp.")
