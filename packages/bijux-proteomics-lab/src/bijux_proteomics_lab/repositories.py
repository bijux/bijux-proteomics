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
    related_evidence_id: str | None = Field(default=None, description="Optional evidence filter.")
    created_after: datetime | None = Field(default=None, description="Optional lower bound for created_at.")
    descending: bool = Field(default=False, description="Whether to sort results in descending time order.")


class LabFeedbackTrendReport(JsonModel):
    """Trend summary across feedback records for one program."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    cycle_ids: list[str] = Field(default_factory=list, description="Observed cycle IDs in chronological order.")
    feedback_count: int = Field(default=0, ge=0, description="Total feedback records included.")
    assay_coverage: dict[str, int] = Field(default_factory=dict, description="Frequency by related assay ID.")


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
    if query.related_evidence_id is not None:
        filtered = [
            record
            for record in filtered
            if query.related_evidence_id in record.related_evidence_ids
        ]
    if query.created_after is not None:
        filtered = [record for record in filtered if record.created_at >= query.created_after]
    return sorted(filtered, key=lambda record: record.created_at, reverse=query.descending)


def summarize_feedback_trend(
    records: list[LabFeedbackRecord],
    *,
    program_id: str,
) -> LabFeedbackTrendReport:
    """Summarize feedback trends by cycle and assay coverage."""
    filtered = sorted(
        [record for record in records if record.program_id == program_id],
        key=lambda record: record.created_at,
    )
    coverage: dict[str, int] = {}
    for record in filtered:
        for assay_id in record.related_assay_ids:
            coverage[assay_id] = coverage.get(assay_id, 0) + 1
    return LabFeedbackTrendReport(
        program_id=program_id,
        cycle_ids=[record.cycle_id for record in filtered],
        feedback_count=len(filtered),
        assay_coverage=coverage,
    )
