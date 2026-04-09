# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Execution backend protocols for program execution."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from bijux_proteomics_foundation import JsonModel
from pydantic import ConfigDict, Field


class ExecutionRequest(JsonModel):
    """Backend-agnostic execution request."""

    model_config = ConfigDict(extra="forbid")

    candidate_sequence: str = Field(
        ..., min_length=1, description="Sequence to evaluate."
    )
    base_dir: Path = Field(..., description="Workspace root.")
    rounds: int = Field(default=1, ge=1, description="Loop iterations.")
    provider: str | None = Field(
        default=None, description="Optional provider override."
    )
    execution_mode: str = Field(default="auto", description="Execution mode.")
    artifacts_dir: Path | None = Field(
        default=None, description="Artifact root override."
    )
    require_human_decision: bool = Field(
        default=False,
        description="Whether the backend should enforce human review support.",
    )


class ExecutionBackend(Protocol):
    """Backend interface that decouples core from runtime implementations."""

    def execute(self, request: ExecutionRequest) -> dict[str, Any]:
        """Execute a candidate sequence against a concrete backend."""
