# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Repository contracts for lab planning outputs."""

from __future__ import annotations

from typing import Protocol

from pydantic import ConfigDict, Field

from bijux_proteomics_lab.serialization import JsonModel


class ReviewQueueEntry(JsonModel):
    """Queued review work produced by lab planning."""

    model_config = ConfigDict(extra="forbid")

    program_id: str = Field(..., min_length=1, description="Program identifier.")
    gate_id: str = Field(..., min_length=1, description="Review gate identifier.")
    summary: str = Field(..., min_length=1, description="Why the entry exists.")


class ExperimentPlanRepository(Protocol):
    """Persistence contract for experiment plans."""

    def save_experiment_plan(self, program_id: str, payload: str) -> None:
        """Persist an experiment plan payload."""

    def load_experiment_plan(self, program_id: str) -> str:
        """Load an experiment plan payload."""


class ReviewQueueRepository(Protocol):
    """Persistence contract for queued review work."""

    def save_review_queue(self, entries: list[ReviewQueueEntry]) -> None:
        """Persist review queue entries."""

    def list_review_queue(self, program_id: str) -> list[ReviewQueueEntry]:
        """List queued review entries for a program."""
