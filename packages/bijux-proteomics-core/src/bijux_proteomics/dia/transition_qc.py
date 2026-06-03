# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned transition-level QC surfaces over canonical transition tables."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.io import parse_transition_table
from bijux_proteomics.io.transition_table import TransitionTableEntry
from bijux_proteomics_foundation import JsonModel


class DiaTransitionSampleValue(JsonModel):
    """One sample-specific transition intensity cell."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    run_ids: tuple[str, ...] = Field(default_factory=tuple)
    intensity: float | None = Field(default=None, ge=0.0)
    retention_time_minutes: float | None = Field(default=None, ge=0.0)
    q_value: float | None = Field(default=None, ge=0.0, le=1.0)
    precursor_total_intensity: float | None = Field(default=None, ge=0.0)
    relative_share: float | None = Field(default=None, ge=0.0, le=1.0)
    source_observation_count: int = Field(..., ge=0)
    detected: bool


class DiaTransitionQcEntry(JsonModel):
    """One transition-level row linked to its precursor and sample intensities."""

    model_config = ConfigDict(extra="forbid")

    transition_id: str = Field(..., min_length=1)
    precursor_id: str = Field(..., min_length=1)
    precursor_charge: int | None = Field(default=None, ge=1)
    peptide_sequence: str | None = None
    protein_ref: str | None = None
    fragment_label: str | None = None
    precursor_mz: float | None = Field(default=None, gt=0.0)
    fragment_mz: float | None = Field(default=None, gt=0.0)
    values: tuple[DiaTransitionSampleValue, ...] = Field(default_factory=tuple)
    detected_sample_count: int = Field(..., ge=0)
    missing_sample_count: int = Field(..., ge=0)
    total_intensity: float = Field(..., ge=0.0)
    mean_intensity: float = Field(..., ge=0.0)
    median_intensity: float = Field(..., ge=0.0)
    median_retention_time_minutes: float | None = Field(default=None, ge=0.0)
    median_relative_share: float = Field(..., ge=0.0, le=1.0)
    min_q_value: float | None = Field(default=None, ge=0.0, le=1.0)
    weak: bool = False
    weak_reasons: tuple[str, ...] = Field(default_factory=tuple)


class DiaWeakTransitionEntry(JsonModel):
    """One explicitly flagged weak transition with stable detection reasons."""

    model_config = ConfigDict(extra="forbid")

    transition_id: str = Field(..., min_length=1)
    precursor_id: str = Field(..., min_length=1)
    detected_sample_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    detection_fraction: float = Field(..., ge=0.0, le=1.0)
    median_relative_share: float = Field(..., ge=0.0, le=1.0)
    weak_reasons: tuple[str, ...] = Field(default_factory=tuple)


class DiaTransitionQcSummary(JsonModel):
    """Compact summary over one transition-level QC review packet."""

    model_config = ConfigDict(extra="forbid")

    precursor_count: int = Field(..., ge=0)
    transition_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    observed_cell_count: int = Field(..., ge=0)
    missing_cell_count: int = Field(..., ge=0)
    weak_transition_count: int = Field(..., ge=0)


class DiaTransitionQcReport(JsonModel):
    """Owned transition-level QC report over one canonical transition table."""

    model_config = ConfigDict(extra="forbid")

    source_name: str = Field(default="transition table", min_length=1)
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    entries: tuple[DiaTransitionQcEntry, ...] = Field(default_factory=tuple)
    weak_transitions: tuple[DiaWeakTransitionEntry, ...] = Field(default_factory=tuple)
    summary: DiaTransitionQcSummary
    note: str = Field(..., min_length=1)


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return int(str(value))


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(str(value))


def build_transition_qc_report(
    entries: tuple[TransitionTableEntry, ...],
    *,
    weak_detection_fraction_threshold: float = 0.5,
    weak_relative_share_threshold: float = 0.1,
) -> DiaTransitionQcReport:
    """Build transition-level sample summaries from canonical transition observations."""

    if not 0.0 <= weak_detection_fraction_threshold <= 1.0:
        raise ValueError(
            "weak_detection_fraction_threshold must be between 0.0 and 1.0"
        )
    if not 0.0 <= weak_relative_share_threshold <= 1.0:
        raise ValueError("weak_relative_share_threshold must be between 0.0 and 1.0")

    sample_ids = tuple(sorted({entry.sample_id for entry in entries}))
    precursor_sample_totals: dict[tuple[str, str], float] = {}
    grouped: dict[tuple[str, str], dict[str, object]] = {}
    for entry in entries:
        precursor_sample_totals[(entry.precursor_id, entry.sample_id)] = (
            precursor_sample_totals.get((entry.precursor_id, entry.sample_id), 0.0)
            + entry.intensity
        )
        group = grouped.setdefault(
            (entry.precursor_id, entry.transition_id),
            {
                "transition_id": entry.transition_id,
                "precursor_id": entry.precursor_id,
                "precursor_charge": entry.precursor_charge,
                "peptide_sequence": entry.peptide_sequence,
                "protein_ref": entry.protein_ref,
                "fragment_label": entry.fragment_label,
                "precursor_mz": entry.precursor_mz,
                "fragment_mz": entry.fragment_mz,
                "sample_entries": {},
            },
        )
        sample_entries = group["sample_entries"]
        if not isinstance(sample_entries, dict):
            raise TypeError(
                "transition QC grouping must preserve sample entries as a mapping"
            )
        sample_entries.setdefault(entry.sample_id, []).append(entry)

    report_entries: list[DiaTransitionQcEntry] = []
    weak_transitions: list[DiaWeakTransitionEntry] = []
    observed_cell_count = 0
    missing_cell_count = 0
    precursor_ids: set[str] = set()
    for _, group in sorted(
        grouped.items(),
        key=lambda item: (str(item[1]["precursor_id"]), str(item[1]["transition_id"])),
    ):
        transition_id = str(group["transition_id"])
        precursor_id = str(group["precursor_id"])
        precursor_ids.add(precursor_id)
        sample_entries = group["sample_entries"]
        if not isinstance(sample_entries, dict):
            raise TypeError(
                "transition QC grouping must preserve sample entries as a mapping"
            )
        values: list[DiaTransitionSampleValue] = []
        detected_intensities: list[float] = []
        detected_retention_times: list[float] = []
        detected_shares: list[float] = []
        min_q_value: float | None = None
        for sample_id in sample_ids:
            observations = sample_entries.get(sample_id, [])
            if not observations:
                missing_cell_count += 1
                values.append(
                    DiaTransitionSampleValue(
                        sample_id=sample_id,
                        source_observation_count=0,
                        detected=False,
                    )
                )
                continue
            observed_cell_count += 1
            intensity = sum(observation.intensity for observation in observations)
            precursor_total_intensity = precursor_sample_totals[
                (precursor_id, sample_id)
            ]
            relative_share = (
                intensity / precursor_total_intensity
                if precursor_total_intensity > 0.0
                else None
            )
            q_values = [
                observation.q_value
                for observation in observations
                if observation.q_value is not None
            ]
            retention_times = [
                observation.retention_time_minutes
                for observation in observations
                if observation.retention_time_minutes is not None
            ]
            detected_intensities.append(intensity)
            detected_retention_times.extend(retention_times)
            if relative_share is not None:
                detected_shares.append(relative_share)
            if q_values:
                local_min_q = min(q_values)
                min_q_value = (
                    local_min_q
                    if min_q_value is None
                    else min(min_q_value, local_min_q)
                )
            values.append(
                DiaTransitionSampleValue(
                    sample_id=sample_id,
                    run_ids=tuple(
                        sorted(
                            {
                                observation.run_id
                                for observation in observations
                                if observation.run_id is not None
                            }
                        )
                    ),
                    intensity=intensity,
                    retention_time_minutes=_median(retention_times)
                    if retention_times
                    else None,
                    q_value=min(q_values) if q_values else None,
                    precursor_total_intensity=precursor_total_intensity,
                    relative_share=relative_share,
                    source_observation_count=len(observations),
                    detected=True,
                )
            )
        detection_fraction = (
            len(detected_intensities) / len(sample_ids) if sample_ids else 0.0
        )
        median_relative_share = _median(detected_shares)
        weak_reasons: list[str] = []
        if detection_fraction < weak_detection_fraction_threshold:
            weak_reasons.append("low sample detection fraction")
        if median_relative_share < weak_relative_share_threshold:
            weak_reasons.append("low median precursor-relative share")
        weak = bool(weak_reasons)
        report_entries.append(
            DiaTransitionQcEntry(
                transition_id=transition_id,
                precursor_id=precursor_id,
                precursor_charge=_optional_int(group["precursor_charge"]),
                peptide_sequence=(
                    None
                    if group["peptide_sequence"] is None
                    else str(group["peptide_sequence"])
                ),
                protein_ref=(
                    None if group["protein_ref"] is None else str(group["protein_ref"])
                ),
                fragment_label=(
                    None
                    if group["fragment_label"] is None
                    else str(group["fragment_label"])
                ),
                precursor_mz=_optional_float(group["precursor_mz"]),
                fragment_mz=_optional_float(group["fragment_mz"]),
                values=tuple(values),
                detected_sample_count=len(detected_intensities),
                missing_sample_count=len(sample_ids) - len(detected_intensities),
                total_intensity=sum(detected_intensities),
                mean_intensity=(
                    sum(detected_intensities) / len(detected_intensities)
                    if detected_intensities
                    else 0.0
                ),
                median_intensity=_median(detected_intensities),
                median_retention_time_minutes=(
                    _median(detected_retention_times)
                    if detected_retention_times
                    else None
                ),
                median_relative_share=median_relative_share,
                min_q_value=min_q_value,
                weak=weak,
                weak_reasons=tuple(weak_reasons),
            )
        )
        if weak:
            weak_transitions.append(
                DiaWeakTransitionEntry(
                    transition_id=transition_id,
                    precursor_id=precursor_id,
                    detected_sample_count=len(detected_intensities),
                    sample_count=len(sample_ids),
                    detection_fraction=detection_fraction,
                    median_relative_share=median_relative_share,
                    weak_reasons=tuple(weak_reasons),
                )
            )
    return DiaTransitionQcReport(
        sample_ids=sample_ids,
        entries=tuple(report_entries),
        weak_transitions=tuple(weak_transitions),
        summary=DiaTransitionQcSummary(
            precursor_count=len(precursor_ids),
            transition_count=len(report_entries),
            sample_count=len(sample_ids),
            observed_cell_count=observed_cell_count,
            missing_cell_count=missing_cell_count,
            weak_transition_count=len(weak_transitions),
        ),
        note=(
            "transition qc keeps fragment-level evidence linked to canonical precursor ids, sample-resolved intensities, and explicit weak-transition calls so users can inspect quantitative support below precursor rollups"
        ),
    )


def build_transition_qc_report_from_table(
    path: Path,
    *,
    weak_detection_fraction_threshold: float = 0.5,
    weak_relative_share_threshold: float = 0.1,
) -> DiaTransitionQcReport:
    """Build one transition QC report directly from a canonical transition table."""

    report = parse_transition_table(path)
    return build_transition_qc_report(
        report.accepted_entries,
        weak_detection_fraction_threshold=weak_detection_fraction_threshold,
        weak_relative_share_threshold=weak_relative_share_threshold,
    )


def _median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2.0


def render_transition_qc_summary_tsv(report: DiaTransitionQcReport) -> str:
    """Render the compact summary for one transition QC report."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "source_name",
            "precursor_count",
            "transition_count",
            "sample_count",
            "observed_cell_count",
            "missing_cell_count",
            "weak_transition_count",
            "note",
        ]
    )
    writer.writerow(
        [
            report.source_name,
            report.summary.precursor_count,
            report.summary.transition_count,
            report.summary.sample_count,
            report.summary.observed_cell_count,
            report.summary.missing_cell_count,
            report.summary.weak_transition_count,
            report.note,
        ]
    )
    return buffer.getvalue()


def render_transition_qc_transition_tsv(report: DiaTransitionQcReport) -> str:
    """Render the transition-level QC ledger as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "transition_id",
            "precursor_id",
            "precursor_charge",
            "peptide_sequence",
            "protein_ref",
            "fragment_label",
            "precursor_mz",
            "fragment_mz",
            "detected_sample_count",
            "missing_sample_count",
            "total_intensity",
            "mean_intensity",
            "median_intensity",
            "median_retention_time_minutes",
            "median_relative_share",
            "min_q_value",
            "weak",
            "weak_reasons",
        ]
    )
    for entry in report.entries:
        writer.writerow(
            [
                entry.transition_id,
                entry.precursor_id,
                "" if entry.precursor_charge is None else entry.precursor_charge,
                "" if entry.peptide_sequence is None else entry.peptide_sequence,
                "" if entry.protein_ref is None else entry.protein_ref,
                "" if entry.fragment_label is None else entry.fragment_label,
                "" if entry.precursor_mz is None else f"{entry.precursor_mz:g}",
                "" if entry.fragment_mz is None else f"{entry.fragment_mz:g}",
                entry.detected_sample_count,
                entry.missing_sample_count,
                f"{entry.total_intensity:g}",
                f"{entry.mean_intensity:g}",
                f"{entry.median_intensity:g}",
                (
                    ""
                    if entry.median_retention_time_minutes is None
                    else f"{entry.median_retention_time_minutes:g}"
                ),
                f"{entry.median_relative_share:.6g}",
                "" if entry.min_q_value is None else f"{entry.min_q_value:.6g}",
                str(entry.weak).lower(),
                ";".join(entry.weak_reasons),
            ]
        )
    return buffer.getvalue()


def render_transition_qc_sample_tsv(report: DiaTransitionQcReport) -> str:
    """Render the sample-resolved transition QC ledger as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "transition_id",
            "precursor_id",
            "sample_id",
            "run_ids",
            "intensity",
            "retention_time_minutes",
            "q_value",
            "precursor_total_intensity",
            "relative_share",
            "source_observation_count",
            "detected",
        ]
    )
    for entry in report.entries:
        for value in entry.values:
            writer.writerow(
                [
                    entry.transition_id,
                    entry.precursor_id,
                    value.sample_id,
                    ";".join(value.run_ids),
                    "" if value.intensity is None else f"{value.intensity:g}",
                    (
                        ""
                        if value.retention_time_minutes is None
                        else f"{value.retention_time_minutes:g}"
                    ),
                    "" if value.q_value is None else f"{value.q_value:.6g}",
                    (
                        ""
                        if value.precursor_total_intensity is None
                        else f"{value.precursor_total_intensity:g}"
                    ),
                    ""
                    if value.relative_share is None
                    else f"{value.relative_share:.6g}",
                    value.source_observation_count,
                    str(value.detected).lower(),
                ]
            )
    return buffer.getvalue()


def render_transition_qc_weak_tsv(report: DiaTransitionQcReport) -> str:
    """Render the weak-transition QC ledger as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "transition_id",
            "precursor_id",
            "detected_sample_count",
            "sample_count",
            "detection_fraction",
            "median_relative_share",
            "weak_reasons",
        ]
    )
    for entry in report.weak_transitions:
        writer.writerow(
            [
                entry.transition_id,
                entry.precursor_id,
                entry.detected_sample_count,
                entry.sample_count,
                f"{entry.detection_fraction:.6g}",
                f"{entry.median_relative_share:.6g}",
                ";".join(entry.weak_reasons),
            ]
        )
    return buffer.getvalue()


def export_transition_qc_summary_tsv(report: DiaTransitionQcReport, path: Path) -> None:
    """Export the transition QC summary TSV."""

    write_output_table_tsv(path, render_transition_qc_summary_tsv(report))


def export_transition_qc_transition_tsv(
    report: DiaTransitionQcReport,
    path: Path,
) -> None:
    """Export the transition-level QC TSV."""

    write_output_table_tsv(path, render_transition_qc_transition_tsv(report))


def export_transition_qc_sample_tsv(report: DiaTransitionQcReport, path: Path) -> None:
    """Export the sample-resolved transition QC TSV."""

    write_output_table_tsv(path, render_transition_qc_sample_tsv(report))


def export_transition_qc_weak_tsv(report: DiaTransitionQcReport, path: Path) -> None:
    """Export the weak-transition QC TSV."""

    write_output_table_tsv(path, render_transition_qc_weak_tsv(report))
