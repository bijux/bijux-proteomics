# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Run request validation."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RunRequest(BaseModel):
    """RunRequest."""

    model_config = ConfigDict(extra="forbid")

    sequence: str = Field(..., min_length=1, description="Protein sequence.")
    tool_name: str | None = Field(default=None, description="Requested tool name.")
