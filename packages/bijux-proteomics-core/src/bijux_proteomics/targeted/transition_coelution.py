# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Validate PRM/SRM transitions using RT alignment and coelution."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.targeted.result_import import (
    TargetedResultImportReport,
    build_skyline_result_import_report,
    build_transition_table_result_import_report,
)
from bijux_proteomics_foundation import JsonModel


class TargetedTransitionCoelutionTier(StrEnum):
    """Quality tier for one targeted precursor coelution group."""

    RELIABLE = "reliable"
    PARTIAL = "partial"
    INSUFFICIENT = "insufficient"
    MISSING = "missing"


class TargetedTransitionTracePoint(JsonModel):
    """One raw PRM/SRM transition trace point."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    transition_id: str = Field(..., min_length=1)
    rt: float = Field(..., ge=0.0)
    intensity: float = Field(..., ge=0.0)


class TargetedTransitionCoelutionScore(JsonModel):
    """One sample-resolved raw targeted transition coelution score."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    transition_count: int = Field(..., ge=0)
    passing_transition_count: int = Field(..., ge=0)
    apex_rt_spread: float = Field(..., ge=0.0)
    coelution_tier: TargetedTransitionCoelutionTier


class TargetedTransitionCoelutionTransitionEntry(JsonModel):
    """One sample-resolved targeted transition coelution record."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    transition_id: str = Field(..., min_length=1)
    detected: bool
    retention_time_minutes: float | None = Field(default=None, ge=0.0)
    anchor_transition_id: str | None = None
    anchor_retention_time_minutes: float | None = Field(default=None, ge=0.0)
    reference_retention_time_minutes: float | None = Field(default=None, ge=0.0)
    coelution_delta_minutes: float | None = Field(default=None, ge=0.0)
    reference_delta_minutes: float | None = Field(default=None, ge=0.0)
    coeluting: bool
    failure_reasons: tuple[str, ...] = Field(default_factory=tuple)


class TargetedTransitionCoelutionTargetEntry(JsonModel):
    """One sample-resolved targeted precursor coelution summary."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    expected_transition_count: int = Field(..., ge=0)
    observed_transition_count: int = Field(..., ge=0)
    coeluting_transition_count: int = Field(..., ge=0)
    coeluting_transition_ids: tuple[str, ...] = Field(default_factory=tuple)
    noncoeluting_transition_ids: tuple[str, ...] = Field(default_factory=tuple)
    anchor_transition_id: str | None = None
    anchor_retention_time_minutes: float | None = Field(default=None, ge=0.0)
    mean_retention_time_minutes: float | None = Field(default=None, ge=0.0)
    reference_retention_time_minutes: float | None = Field(default=None, ge=0.0)
    absolute_alignment_delta_minutes: float | None = Field(default=None, ge=0.0)
    alignment_flagged: bool = False
    coelution_tier: TargetedTransitionCoelutionTier
    reliable_transition_support: bool
    reliability_reasons: tuple[str, ...] = Field(default_factory=tuple)


class TargetedTransitionCoelutionSummary(JsonModel):
    """Compact summary over targeted transition coelution review."""

    model_config = ConfigDict(extra="forbid")

    target_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    target_entry_count: int = Field(..., ge=0)
    flagged_target_entry_count: int = Field(..., ge=0)
    transition_entry_count: int = Field(..., ge=0)
    coeluting_transition_entry_count: int = Field(..., ge=0)


class TargetedTransitionCoelutionReport(JsonModel):
    """Transition coelution and alignment review over targeted observations."""

    model_config = ConfigDict(extra="forbid")

    source_name: str = Field(..., min_length=1)
    target_entries: tuple[TargetedTransitionCoelutionTargetEntry, ...] = Field(
        default_factory=tuple
    )
    transition_entries: tuple[TargetedTransitionCoelutionTransitionEntry, ...] = Field(
        default_factory=tuple
    )
    summary: TargetedTransitionCoelutionSummary
    note: str = Field(..., min_length=1)


def score_transition_coelution(
    transition_xics: tuple[TargetedTransitionTracePoint, ...],
    *,
    coelution_rt_delta_threshold_minutes: float = 0.2,
) -> tuple[TargetedTransitionCoelutionScore, ...]:
    """Score targeted transition coelution directly from raw trace points."""

    if not transition_xics:
        raise ValueError("transition_xics must not be empty")
    if coelution_rt_delta_threshold_minutes <= 0.0:
        raise ValueError(
            "coelution_rt_delta_threshold_minutes must be greater than zero"
        )

    traces_by_group: dict[tuple[str, str], dict[str, dict[float, float]]] = {}
    for point in transition_xics:
        traces_by_group.setdefault((point.target_id, point.sample_id), {}).setdefault(
            point.transition_id,
            {},
        )[point.rt] = point.intensity

    rows: list[TargetedTransitionCoelutionScore] = []
    for (target_id, sample_id), traces_by_transition in sorted(traces_by_group.items()):
        detected_traces = {
            transition_id: trace
            for transition_id, trace in traces_by_transition.items()
            if max(trace.values(), default=0.0) > 0.0
        }
        apexes = {
            transition_id: _trace_apex_minutes(trace)
            for transition_id, trace in detected_traces.items()
        }
        apex_values = tuple(apexes.values())
        apex_rt_spread = (
            0.0 if not apex_values else max(apex_values) - min(apex_values)
        )
        passing_transition_count = 0
        if detected_traces:
            reference_transition_id, reference_trace = max(
                detected_traces.items(),
                key=lambda item: (
                    sum(item[1].values()),
                    max(item[1].values(), default=0.0),
                    item[0],
                ),
            )
            reference_apex = apexes[reference_transition_id]
            for transition_id, trace in detected_traces.items():
                if transition_id == reference_transition_id:
                    passing_transition_count += 1
                    continue
                apex_shift = abs(apexes[transition_id] - reference_apex)
                if apex_shift <= coelution_rt_delta_threshold_minutes:
                    passing_transition_count += 1

        rows.append(
            TargetedTransitionCoelutionScore(
                target_id=target_id,
                sample_id=sample_id,
                transition_count=len(traces_by_transition),
                passing_transition_count=passing_transition_count,
                apex_rt_spread=round(apex_rt_spread, 4),
                coelution_tier=_coelution_tier(
                    transition_count=len(traces_by_transition),
                    passing_transition_count=passing_transition_count,
                ),
            )
        )
    return tuple(rows)


def build_targeted_transition_coelution_report(
    import_report: TargetedResultImportReport,
    *,
    coelution_rt_delta_threshold_minutes: float = 0.2,
    alignment_rt_delta_threshold_minutes: float = 0.75,
) -> TargetedTransitionCoelutionReport:
    """Build targeted transition coelution and RT-alignment review ledgers."""

    if coelution_rt_delta_threshold_minutes <= 0.0:
        raise ValueError(
            "coelution_rt_delta_threshold_minutes must be greater than zero"
        )
    if alignment_rt_delta_threshold_minutes <= 0.0:
        raise ValueError(
            "alignment_rt_delta_threshold_minutes must be greater than zero"
        )

    target_ids = sorted({item.precursor_id for item in import_report.observations})
    sample_ids = sorted({item.sample_id for item in import_report.observations})
    transition_ids_by_target = {
        target_id: sorted(
            {
                item.transition_id
                for item in import_report.observations
                if item.precursor_id == target_id
            }
        )
        for target_id in target_ids
    }
    reference_retention_time_by_target = {
        target_id: _median(
            [
                item.retention_time_minutes
                for item in import_report.observations
                if item.precursor_id == target_id and item.retention_time_minutes is not None
            ]
        )
        for target_id in target_ids
    }
    raw_scores_by_group = {
        (entry.target_id, entry.sample_id): entry
        for entry in score_transition_coelution(
            _transition_trace_points(import_report),
            coelution_rt_delta_threshold_minutes=coelution_rt_delta_threshold_minutes,
        )
    }

    target_entries: list[TargetedTransitionCoelutionTargetEntry] = []
    transition_entries: list[TargetedTransitionCoelutionTransitionEntry] = []

    for target_id in target_ids:
        expected_transition_ids = transition_ids_by_target[target_id]
        reference_retention_time = reference_retention_time_by_target[target_id]
        observations_by_sample = {
            sample_id: [
                item
                for item in import_report.observations
                if item.precursor_id == target_id and item.sample_id == sample_id
            ]
            for sample_id in sample_ids
        }
        for sample_id in sample_ids:
            sample_observations = observations_by_sample[sample_id]
            observations_by_transition_id = {
                item.transition_id: item for item in sample_observations
            }
            anchor_observation = _anchor_observation(sample_observations)
            anchor_transition_id = (
                None if anchor_observation is None else anchor_observation.transition_id
            )
            anchor_retention_time = (
                None
                if anchor_observation is None
                else anchor_observation.retention_time_minutes
            )
            sample_retention_times = [
                item.retention_time_minutes
                for item in sample_observations
                if item.retention_time_minutes is not None
            ]
            mean_retention_time = (
                None
                if not sample_retention_times
                else sum(sample_retention_times) / len(sample_retention_times)
            )
            absolute_alignment_delta = (
                None
                if mean_retention_time is None or reference_retention_time is None
                else abs(mean_retention_time - reference_retention_time)
            )
            alignment_flagged = (
                absolute_alignment_delta is not None
                and absolute_alignment_delta > alignment_rt_delta_threshold_minutes
            )

            coeluting_transition_ids: list[str] = []
            noncoeluting_transition_ids: list[str] = []
            for transition_id in expected_transition_ids:
                observation = observations_by_transition_id.get(transition_id)
                if observation is None:
                    transition_entries.append(
                        TargetedTransitionCoelutionTransitionEntry(
                            target_id=target_id,
                            sample_id=sample_id,
                            transition_id=transition_id,
                            detected=False,
                            anchor_transition_id=anchor_transition_id,
                            anchor_retention_time_minutes=anchor_retention_time,
                            reference_retention_time_minutes=reference_retention_time,
                            coeluting=False,
                            failure_reasons=("transition not observed",),
                        )
                    )
                    noncoeluting_transition_ids.append(transition_id)
                    continue

                failure_reasons: list[str] = []
                retention_time = observation.retention_time_minutes
                coelution_delta = (
                    None
                    if retention_time is None or anchor_retention_time is None
                    else abs(retention_time - anchor_retention_time)
                )
                reference_delta = (
                    None
                    if retention_time is None or reference_retention_time is None
                    else abs(retention_time - reference_retention_time)
                )
                coelution_reasons: list[str] = []
                if retention_time is None:
                    failure_reasons.append("transition retention time is missing")
                    coelution_reasons.append("transition retention time is missing")
                if anchor_retention_time is None and retention_time is not None:
                    failure_reasons.append("sample apex retention time is missing")
                    coelution_reasons.append("sample apex retention time is missing")
                if (
                    coelution_delta is not None
                    and coelution_delta > coelution_rt_delta_threshold_minutes
                ):
                    reason = (
                        "transition does not coelute with the sample apex"
                    )
                    failure_reasons.append(reason)
                    coelution_reasons.append(reason)
                if (
                    reference_delta is not None
                    and reference_delta > alignment_rt_delta_threshold_minutes
                ):
                    failure_reasons.append(
                        "transition is misaligned from the target reference window"
                    )
                coeluting = not coelution_reasons
                if coeluting:
                    coeluting_transition_ids.append(transition_id)
                else:
                    noncoeluting_transition_ids.append(transition_id)
                transition_entries.append(
                    TargetedTransitionCoelutionTransitionEntry(
                        target_id=target_id,
                        sample_id=sample_id,
                        transition_id=transition_id,
                        detected=True,
                        retention_time_minutes=retention_time,
                        anchor_transition_id=anchor_transition_id,
                        anchor_retention_time_minutes=anchor_retention_time,
                        reference_retention_time_minutes=reference_retention_time,
                        coelution_delta_minutes=coelution_delta,
                        reference_delta_minutes=reference_delta,
                        coeluting=coeluting,
                        failure_reasons=tuple(sorted(failure_reasons)),
                    )
                )

            reliability_reasons: list[str] = []
            raw_score = raw_scores_by_group.get(
                (target_id, sample_id),
                TargetedTransitionCoelutionScore(
                    target_id=target_id,
                    sample_id=sample_id,
                    transition_count=0,
                    passing_transition_count=0,
                    apex_rt_spread=0.0,
                    coelution_tier=TargetedTransitionCoelutionTier.MISSING,
                ),
            )
            target_coelution_tier = _coelution_tier(
                transition_count=len(expected_transition_ids),
                passing_transition_count=raw_score.passing_transition_count,
            )
            if raw_score.passing_transition_count < 2:
                reliability_reasons.append(
                    "fewer than two coeluting transitions support the target"
                )
            if alignment_flagged:
                reliability_reasons.append(
                    "retention time deviates from the target reference window"
                )
            target_entries.append(
                TargetedTransitionCoelutionTargetEntry(
                    target_id=target_id,
                    sample_id=sample_id,
                    expected_transition_count=len(expected_transition_ids),
                    observed_transition_count=len(sample_observations),
                    coeluting_transition_count=len(coeluting_transition_ids),
                    coeluting_transition_ids=tuple(sorted(coeluting_transition_ids)),
                    noncoeluting_transition_ids=tuple(sorted(noncoeluting_transition_ids)),
                    anchor_transition_id=anchor_transition_id,
                    anchor_retention_time_minutes=anchor_retention_time,
                    mean_retention_time_minutes=mean_retention_time,
                    reference_retention_time_minutes=reference_retention_time,
                    absolute_alignment_delta_minutes=absolute_alignment_delta,
                    alignment_flagged=alignment_flagged,
                    coelution_tier=target_coelution_tier,
                    reliable_transition_support=(
                        target_coelution_tier is TargetedTransitionCoelutionTier.RELIABLE
                        and not reliability_reasons
                    ),
                    reliability_reasons=tuple(sorted(reliability_reasons)),
                )
            )

    return TargetedTransitionCoelutionReport(
        source_name=import_report.source_name,
        target_entries=tuple(
            sorted(target_entries, key=lambda entry: (entry.target_id, entry.sample_id))
        ),
        transition_entries=tuple(
            sorted(
                transition_entries,
                key=lambda entry: (entry.target_id, entry.sample_id, entry.transition_id),
            )
        ),
        summary=TargetedTransitionCoelutionSummary(
            target_count=len(target_ids),
            sample_count=len(sample_ids),
            target_entry_count=len(target_entries),
            flagged_target_entry_count=sum(
                not entry.reliable_transition_support for entry in target_entries
            ),
            transition_entry_count=len(transition_entries),
            coeluting_transition_entry_count=sum(
                entry.coeluting for entry in transition_entries
            ),
        ),
        note=(
            "targeted transition coelution keeps sample apex alignment, transition-level coelution, and explicit failed transitions visible before any targeted precursor is trusted"
        ),
    )


def build_skyline_targeted_transition_coelution_report(
    path: Path,
    *,
    coelution_rt_delta_threshold_minutes: float = 0.2,
    alignment_rt_delta_threshold_minutes: float = 0.75,
) -> TargetedTransitionCoelutionReport:
    """Build targeted transition coelution directly from one Skyline export."""

    return build_targeted_transition_coelution_report(
        build_skyline_result_import_report(path),
        coelution_rt_delta_threshold_minutes=coelution_rt_delta_threshold_minutes,
        alignment_rt_delta_threshold_minutes=alignment_rt_delta_threshold_minutes,
    )


def build_transition_table_targeted_transition_coelution_report(
    path: Path,
    *,
    coelution_rt_delta_threshold_minutes: float = 0.2,
    alignment_rt_delta_threshold_minutes: float = 0.75,
) -> TargetedTransitionCoelutionReport:
    """Build targeted transition coelution directly from one transition table."""

    return build_targeted_transition_coelution_report(
        build_transition_table_result_import_report(path),
        coelution_rt_delta_threshold_minutes=coelution_rt_delta_threshold_minutes,
        alignment_rt_delta_threshold_minutes=alignment_rt_delta_threshold_minutes,
    )


def render_targeted_transition_coelution_target_tsv(
    report: TargetedTransitionCoelutionReport,
) -> str:
    """Render target-level transition coelution rows as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "target_id",
            "sample_id",
            "expected_transition_count",
            "observed_transition_count",
            "coeluting_transition_count",
            "coeluting_transition_ids",
            "noncoeluting_transition_ids",
            "anchor_transition_id",
            "anchor_retention_time_minutes",
            "mean_retention_time_minutes",
            "reference_retention_time_minutes",
            "absolute_alignment_delta_minutes",
            "alignment_flagged",
            "coelution_tier",
            "reliable_transition_support",
            "reliability_reasons",
        )
    )
    for entry in report.target_entries:
        writer.writerow(
            (
                entry.target_id,
                entry.sample_id,
                entry.expected_transition_count,
                entry.observed_transition_count,
                entry.coeluting_transition_count,
                ";".join(entry.coeluting_transition_ids),
                ";".join(entry.noncoeluting_transition_ids),
                "" if entry.anchor_transition_id is None else entry.anchor_transition_id,
                (
                    ""
                    if entry.anchor_retention_time_minutes is None
                    else f"{entry.anchor_retention_time_minutes:g}"
                ),
                (
                    ""
                    if entry.mean_retention_time_minutes is None
                    else f"{entry.mean_retention_time_minutes:g}"
                ),
                (
                    ""
                    if entry.reference_retention_time_minutes is None
                    else f"{entry.reference_retention_time_minutes:g}"
                ),
                (
                    ""
                    if entry.absolute_alignment_delta_minutes is None
                    else f"{entry.absolute_alignment_delta_minutes:g}"
                ),
                str(entry.alignment_flagged).lower(),
                entry.coelution_tier.value,
                str(entry.reliable_transition_support).lower(),
                "; ".join(entry.reliability_reasons),
            )
        )
    return buffer.getvalue()


def render_targeted_transition_coelution_transition_tsv(
    report: TargetedTransitionCoelutionReport,
) -> str:
    """Render transition-level coelution review rows as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "target_id",
            "sample_id",
            "transition_id",
            "detected",
            "retention_time_minutes",
            "anchor_transition_id",
            "anchor_retention_time_minutes",
            "reference_retention_time_minutes",
            "coelution_delta_minutes",
            "reference_delta_minutes",
            "coeluting",
            "failure_reasons",
        )
    )
    for entry in report.transition_entries:
        writer.writerow(
            (
                entry.target_id,
                entry.sample_id,
                entry.transition_id,
                str(entry.detected).lower(),
                (
                    ""
                    if entry.retention_time_minutes is None
                    else f"{entry.retention_time_minutes:g}"
                ),
                "" if entry.anchor_transition_id is None else entry.anchor_transition_id,
                (
                    ""
                    if entry.anchor_retention_time_minutes is None
                    else f"{entry.anchor_retention_time_minutes:g}"
                ),
                (
                    ""
                    if entry.reference_retention_time_minutes is None
                    else f"{entry.reference_retention_time_minutes:g}"
                ),
                (
                    ""
                    if entry.coelution_delta_minutes is None
                    else f"{entry.coelution_delta_minutes:g}"
                ),
                (
                    ""
                    if entry.reference_delta_minutes is None
                    else f"{entry.reference_delta_minutes:g}"
                ),
                str(entry.coeluting).lower(),
                "; ".join(entry.failure_reasons),
            )
        )
    return buffer.getvalue()


def render_transition_coelution_tsv(
    rows: tuple[TargetedTransitionCoelutionScore, ...],
) -> str:
    """Render raw targeted transition coelution scores as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "target_id",
            "sample_id",
            "transition_count",
            "passing_transition_count",
            "apex_rt_spread",
            "coelution_tier",
        )
    )
    for row in rows:
        writer.writerow(
            (
                row.target_id,
                row.sample_id,
                row.transition_count,
                row.passing_transition_count,
                f"{row.apex_rt_spread:g}",
                row.coelution_tier.value,
            )
        )
    return buffer.getvalue()


def _anchor_observation(observations: list[object]) -> object | None:
    candidates = [
        observation
        for observation in observations
        if observation.retention_time_minutes is not None
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda observation: observation.intensity)


def _transition_trace_points(
    import_report: TargetedResultImportReport,
) -> tuple[TargetedTransitionTracePoint, ...]:
    return tuple(
        TargetedTransitionTracePoint(
            target_id=observation.precursor_id,
            sample_id=observation.sample_id,
            transition_id=observation.transition_id,
            rt=observation.retention_time_minutes or 0.0,
            intensity=observation.intensity,
        )
        for observation in import_report.observations
    )


def _trace_apex_minutes(trace: dict[float, float]) -> float:
    apex_rt, _ = max(trace.items(), key=lambda item: (item[1], -item[0]))
    return apex_rt


def _coelution_tier(
    *,
    transition_count: int,
    passing_transition_count: int,
) -> TargetedTransitionCoelutionTier:
    if passing_transition_count == 0:
        return TargetedTransitionCoelutionTier.MISSING
    if passing_transition_count >= 2:
        return TargetedTransitionCoelutionTier.RELIABLE
    if transition_count >= 2:
        return TargetedTransitionCoelutionTier.INSUFFICIENT
    return TargetedTransitionCoelutionTier.PARTIAL


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2.0
