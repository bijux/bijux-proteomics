# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Repository contracts for lab planning outputs."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import GateId, JsonModel, ProgramId


class ReviewQueueEntry(JsonModel):
    """Queued review work produced by lab planning."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    gate_id: GateId = Field(..., description="Review gate identifier.")
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


class LabFeedbackRecord(JsonModel):
    """Structured bridge from lab outcomes back into program decisions."""

    model_config = ConfigDict(extra="forbid")

    feedback_id: str = Field(..., min_length=1, description="Stable feedback identifier.")
    program_id: ProgramId = Field(..., description="Program identifier.")
    cycle_id: str = Field(..., min_length=1, description="Planning or execution cycle identifier.")
    summary: str = Field(..., min_length=1, description="Feedback summary.")
    related_assay_ids: list[str] = Field(
        default_factory=list,
        description="Assays that produced this feedback.",
    )
    related_evidence_ids: list[str] = Field(
        default_factory=list,
        description="Evidence records promoted from this feedback.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the feedback record was created.",
    )


class LabFeedbackQuery(JsonModel):
    """Structured query for filtering feedback records."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    cycle_id: str | None = Field(default=None, description="Optional cycle filter.")
    related_assay_id: str | None = Field(default=None, description="Optional assay filter.")


class LabFeedbackRepository(Protocol):
    """Persistence contract for closed-loop feedback records."""

    def save_feedback_record(self, record: LabFeedbackRecord) -> None:
        """Persist one feedback record."""

    def list_feedback_records(self, program_id: str) -> list[LabFeedbackRecord]:
        """List feedback records for a program."""


def query_feedback_records(
    records: list[LabFeedbackRecord],
    query: LabFeedbackQuery,
) -> list[LabFeedbackRecord]:
    """Filter feedback records using structured query fields."""
    filtered = [record for record in records if record.program_id == query.program_id]
    if query.cycle_id is not None:
        filtered = [record for record in filtered if record.cycle_id == query.cycle_id]
    if query.related_assay_id is not None:
        filtered = [
            record
            for record in filtered
            if query.related_assay_id in record.related_assay_ids
        ]
    return sorted(filtered, key=lambda record: record.created_at)
