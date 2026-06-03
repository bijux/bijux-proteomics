# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Feedback records and reconciliation analytics for observed lab outcomes."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Protocol

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel, ProgramId


class LabFeedbackRecord(JsonModel):
    """Structured bridge from lab outcomes back into program decisions."""

    model_config = ConfigDict(extra="forbid")

    feedback_id: str = Field(
        ..., min_length=1, description="Stable feedback identifier."
    )
    program_id: ProgramId = Field(..., description="Program identifier.")
    cycle_id: str = Field(
        ..., min_length=1, description="Planning or execution cycle identifier."
    )
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
    related_assay_id: str | None = Field(
        default=None, description="Optional assay filter."
    )
    related_evidence_id: str | None = Field(
        default=None, description="Optional evidence filter."
    )
    created_after: datetime | None = Field(
        default=None, description="Optional lower bound for created_at."
    )
    descending: bool = Field(
        default=False, description="Whether to sort results in descending time order."
    )


class LabFeedbackTrendReport(JsonModel):
    """Trend summary across feedback records for one program."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    cycle_ids: list[str] = Field(
        default_factory=list, description="Observed cycle IDs in chronological order."
    )
    feedback_count: int = Field(
        default=0, ge=0, description="Total feedback records included."
    )
    assay_coverage: dict[str, int] = Field(
        default_factory=dict, description="Frequency by related assay ID."
    )


class FeedbackCycleLatencyReport(JsonModel):
    """Latency profile for closed-loop feedback accumulation across cycles."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    cycle_to_first_feedback_days: dict[str, float] = Field(
        default_factory=dict,
        description="Days from earliest program feedback to first feedback in each cycle.",
    )
    median_latency_days: float = Field(
        default=0.0, ge=0.0, description="Median first-feedback latency across cycles."
    )


class FeedbackAnomalyReport(JsonModel):
    """Anomaly signals for feedback streams in one program."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    high_volume_cycles: list[str] = Field(
        default_factory=list,
        description="Cycle IDs with unusually high feedback count.",
    )
    dominant_assay_ids: list[str] = Field(
        default_factory=list, description="Assays that dominate feedback payloads."
    )
    notes: list[str] = Field(
        default_factory=list, description="Anomaly interpretation notes."
    )


class CycleWorkloadForecast(JsonModel):
    """Forecasted workload for the next cycle from historical queue and feedback signals."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    forecast_feedback_count: int = Field(
        default=0, ge=0, description="Forecasted number of feedback records."
    )
    forecast_review_entries: int = Field(
        default=0, ge=0, description="Forecasted review queue entries."
    )
    pressure_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Forecasted workload pressure score."
    )
    notes: list[str] = Field(
        default_factory=list, description="Forecast interpretation notes."
    )


class FeedbackLineageCoverageReport(JsonModel):
    """Coverage report for assay/evidence lineage in feedback records."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    records_with_assay_lineage: int = Field(
        default=0, ge=0, description="Records containing assay lineage."
    )
    records_with_evidence_lineage: int = Field(
        default=0, ge=0, description="Records containing evidence lineage."
    )
    full_lineage_count: int = Field(
        default=0,
        ge=0,
        description="Records containing both assay and evidence lineage.",
    )
    lineage_coverage_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Normalized lineage coverage score."
    )


class LabFeedbackRepository(Protocol):
    """Persistence contract for closed-loop feedback records."""

    def save_feedback_record(self, record: LabFeedbackRecord) -> None:
        """Persist one feedback record."""

    def list_feedback_records(self, program_id: str) -> list[LabFeedbackRecord]:
        """List feedback records for a program."""


class ReviewQueueEntryLike(Protocol):
    """Minimal queue-entry contract needed for workload forecasting."""

    program_id: str


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
        filtered = [
            record for record in filtered if record.created_at >= query.created_after
        ]
    return sorted(
        filtered, key=lambda record: record.created_at, reverse=query.descending
    )


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


def summarize_feedback_cycle_latency(
    records: list[LabFeedbackRecord],
    *,
    program_id: str,
) -> FeedbackCycleLatencyReport:
    """Summarize cycle feedback latency relative to the first program feedback timestamp."""
    filtered = sorted(
        [record for record in records if record.program_id == program_id],
        key=lambda record: record.created_at,
    )
    if not filtered:
        return FeedbackCycleLatencyReport(program_id=program_id)
    anchor = filtered[0].created_at
    first_by_cycle: dict[str, datetime] = {}
    for record in filtered:
        first_by_cycle.setdefault(record.cycle_id, record.created_at)
    latencies = {
        cycle_id: round((timestamp - anchor).total_seconds() / 86400.0, 4)
        for cycle_id, timestamp in sorted(first_by_cycle.items())
    }
    sorted_latency_values = sorted(latencies.values())
    midpoint = len(sorted_latency_values) // 2
    if len(sorted_latency_values) % 2 == 0:
        median_latency = (
            sorted_latency_values[midpoint - 1] + sorted_latency_values[midpoint]
        ) / 2
    else:
        median_latency = sorted_latency_values[midpoint]
    return FeedbackCycleLatencyReport(
        program_id=program_id,
        cycle_to_first_feedback_days=latencies,
        median_latency_days=round(median_latency, 4),
    )


def detect_feedback_anomalies(
    records: list[LabFeedbackRecord],
    *,
    program_id: str,
    cycle_volume_threshold: int = 5,
    assay_dominance_ratio: float = 0.6,
) -> FeedbackAnomalyReport:
    """Detect anomalous feedback patterns by cycle volume and assay concentration."""
    filtered = [record for record in records if record.program_id == program_id]
    cycle_counts: dict[str, int] = {}
    assay_counts: dict[str, int] = {}
    for record in filtered:
        cycle_counts[record.cycle_id] = cycle_counts.get(record.cycle_id, 0) + 1
        for assay_id in record.related_assay_ids:
            assay_counts[assay_id] = assay_counts.get(assay_id, 0) + 1
    high_volume = sorted(
        [
            cycle_id
            for cycle_id, count in cycle_counts.items()
            if count >= cycle_volume_threshold
        ]
    )
    total_assay_refs = sum(assay_counts.values())
    dominant_assays = sorted(
        [
            assay_id
            for assay_id, count in assay_counts.items()
            if total_assay_refs > 0
            and (count / total_assay_refs) >= assay_dominance_ratio
        ]
    )
    notes: list[str] = []
    if high_volume:
        notes.append(f"high feedback volume in cycles: {', '.join(high_volume)}")
    if dominant_assays:
        notes.append(
            f"feedback is concentrated in assays: {', '.join(dominant_assays)}"
        )
    if not notes:
        notes.append("no strong anomaly signal detected")
    return FeedbackAnomalyReport(
        program_id=program_id,
        high_volume_cycles=high_volume,
        dominant_assay_ids=dominant_assays,
        notes=notes,
    )


def forecast_cycle_workload(
    *,
    program_id: str,
    feedback_records: list[LabFeedbackRecord],
    review_entries: Sequence[ReviewQueueEntryLike],
) -> CycleWorkloadForecast:
    """Forecast next-cycle workload from recent cycle volumes."""
    feedback_filtered = [
        record for record in feedback_records if record.program_id == program_id
    ]
    review_filtered = [
        entry for entry in review_entries if entry.program_id == program_id
    ]
    feedback_by_cycle: dict[str, int] = {}
    for record in feedback_filtered:
        feedback_by_cycle[record.cycle_id] = (
            feedback_by_cycle.get(record.cycle_id, 0) + 1
        )
    feedback_values = sorted(feedback_by_cycle.values())
    if feedback_values:
        feedback_forecast = int(
            round(sum(feedback_values[-3:]) / min(3, len(feedback_values)))
        )
    else:
        feedback_forecast = 0
    review_forecast = len(review_filtered)
    pressure_score = round(
        max(0.0, min((feedback_forecast * 0.08) + (review_forecast * 0.06), 1.0)), 4
    )
    notes: list[str] = []
    if pressure_score >= 0.7:
        notes.append("forecast indicates high workload pressure")
    if feedback_forecast == 0 and review_forecast == 0:
        notes.append("limited workload signal in historical records")
    if not notes:
        notes.append("forecast is within normal operational range")
    return CycleWorkloadForecast(
        program_id=program_id,
        forecast_feedback_count=feedback_forecast,
        forecast_review_entries=review_forecast,
        pressure_score=pressure_score,
        notes=notes,
    )


def summarize_feedback_lineage_coverage(
    records: list[LabFeedbackRecord],
    *,
    program_id: str,
) -> FeedbackLineageCoverageReport:
    """Summarize how well feedback records preserve lineage context."""
    filtered = [record for record in records if record.program_id == program_id]
    assay_count = sum(1 for record in filtered if record.related_assay_ids)
    evidence_count = sum(1 for record in filtered if record.related_evidence_ids)
    full_count = sum(
        1
        for record in filtered
        if record.related_assay_ids and record.related_evidence_ids
    )
    total = len(filtered)
    score = round((full_count / total), 4) if total else 0.0
    return FeedbackLineageCoverageReport(
        program_id=program_id,
        records_with_assay_lineage=assay_count,
        records_with_evidence_lineage=evidence_count,
        full_lineage_count=full_count,
        lineage_coverage_score=score,
    )
