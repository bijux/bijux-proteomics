# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Review-queue contracts and queue-pressure analytics for lab planning."""

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
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the queue entry was created.",
    )


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


class ReviewQueueQuery(JsonModel):
    """Structured query for filtering review queue entries."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId | None = Field(
        default=None, description="Optional program identifier filter."
    )
    gate_id: GateId | None = Field(
        default=None, description="Optional review gate filter."
    )


class ReviewQueueTrendReport(JsonModel):
    """Summary report for review queue composition."""

    model_config = ConfigDict(extra="forbid")

    total_entries: int = Field(
        default=0, ge=0, description="Total queue entries evaluated."
    )
    by_gate: dict[str, int] = Field(
        default_factory=dict, description="Queue counts by gate identifier."
    )


class ReviewQueueWorkloadReport(JsonModel):
    """Queue pressure report with age-aware workload signals."""

    model_config = ConfigDict(extra="forbid")

    total_entries: int = Field(
        default=0, ge=0, description="Total queue entries evaluated."
    )
    by_program: dict[str, int] = Field(
        default_factory=dict, description="Queue counts by program identifier."
    )
    stale_entry_count: int = Field(
        default=0, ge=0, description="Count of entries older than the stale threshold."
    )
    pressure_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Normalized queue pressure score."
    )


class ReviewQueueSlaReport(JsonModel):
    """SLA breach report for review queue entries."""

    model_config = ConfigDict(extra="forbid")

    total_entries: int = Field(
        default=0, ge=0, description="Total queue entries evaluated."
    )
    breached_entries: int = Field(
        default=0, ge=0, description="Entries breaching SLA threshold."
    )
    breaches_by_gate: dict[str, int] = Field(
        default_factory=dict, description="Breach counts by gate ID."
    )
    breach_ratio: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Share of entries breaching SLA."
    )


def query_review_queue(
    entries: list[ReviewQueueEntry],
    query: ReviewQueueQuery,
) -> list[ReviewQueueEntry]:
    """Filter review queue entries using structured query fields."""
    filtered = list(entries)
    if query.program_id is not None:
        filtered = [entry for entry in filtered if entry.program_id == query.program_id]
    if query.gate_id is not None:
        filtered = [entry for entry in filtered if entry.gate_id == query.gate_id]
    return filtered


def summarize_review_queue(entries: list[ReviewQueueEntry]) -> ReviewQueueTrendReport:
    """Summarize review queue volume by gate identifier."""
    by_gate: dict[str, int] = {}
    for entry in entries:
        by_gate[entry.gate_id] = by_gate.get(entry.gate_id, 0) + 1
    return ReviewQueueTrendReport(
        total_entries=len(entries),
        by_gate=by_gate,
    )


def summarize_review_queue_workload(
    entries: list[ReviewQueueEntry],
    *,
    now: datetime | None = None,
    stale_after_days: int = 14,
) -> ReviewQueueWorkloadReport:
    """Summarize queue workload with stale-entry pressure scoring."""
    now = now or datetime.now(UTC)
    by_program: dict[str, int] = {}
    stale_count = 0
    for entry in entries:
        by_program[entry.program_id] = by_program.get(entry.program_id, 0) + 1
        age_days = (now - entry.created_at).days
        if age_days >= stale_after_days:
            stale_count += 1
    total = len(entries)
    stale_ratio = (stale_count / total) if total else 0.0
    concentration = (max(by_program.values()) / total) if total and by_program else 0.0
    pressure_score = round(
        max(0.0, min((0.6 * stale_ratio) + (0.4 * concentration), 1.0)), 4
    )
    return ReviewQueueWorkloadReport(
        total_entries=total,
        by_program=by_program,
        stale_entry_count=stale_count,
        pressure_score=pressure_score,
    )


def summarize_review_queue_sla(
    entries: list[ReviewQueueEntry],
    *,
    now: datetime | None = None,
    sla_days: int = 7,
) -> ReviewQueueSlaReport:
    """Summarize SLA breach state across review queue entries."""
    now = now or datetime.now(UTC)
    breaches_by_gate: dict[str, int] = {}
    breached = 0
    for entry in entries:
        age_days = (now - entry.created_at).days
        if age_days > sla_days:
            breached += 1
            breaches_by_gate[entry.gate_id] = breaches_by_gate.get(entry.gate_id, 0) + 1
    total = len(entries)
    ratio = round((breached / total), 4) if total else 0.0
    return ReviewQueueSlaReport(
        total_entries=total,
        breached_entries=breached,
        breaches_by_gate=breaches_by_gate,
        breach_ratio=ratio,
    )
