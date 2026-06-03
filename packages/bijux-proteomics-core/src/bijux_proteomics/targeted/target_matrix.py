# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned target-matrix review surfaces over imported targeted observations."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.targeted.result_import import (
    TargetedResultImportReport,
    TargetedResultObservation,
    build_skyline_result_import_report,
    build_transition_table_result_import_report,
)
from bijux_proteomics_foundation import JsonModel


class TargetedMatrixValue(JsonModel):
    """One sample-specific target-matrix cell."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    source_transition_ids: tuple[str, ...] = Field(default_factory=tuple)
    retained_transition_ids: tuple[str, ...] = Field(default_factory=tuple)
    excluded_transition_ids: tuple[str, ...] = Field(default_factory=tuple)
    observed_transition_count: int = Field(..., ge=0)
    retained_transition_count: int = Field(..., ge=0)
    excluded_transition_count: int = Field(..., ge=0)
    intensity: float | None = Field(default=None, ge=0.0)
    retention_time_minutes: float | None = Field(default=None, ge=0.0)
    quality_flags: tuple[str, ...] = Field(default_factory=tuple)
    missing_reason: str | None = None
    detected: bool


class TargetedMatrixRow(JsonModel):
    """One precursor-target row across all samples."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    protein_ref: str | None = None
    source_transition_ids: tuple[str, ...] = Field(default_factory=tuple)
    retained_transition_ids: tuple[str, ...] = Field(default_factory=tuple)
    excluded_transition_ids: tuple[str, ...] = Field(default_factory=tuple)
    values: tuple[TargetedMatrixValue, ...] = Field(default_factory=tuple)
    retained_transition_count: int = Field(..., ge=0)
    excluded_transition_count: int = Field(..., ge=0)
    detected_sample_count: int = Field(..., ge=0)
    total_intensity: float = Field(..., ge=0.0)
    mean_intensity: float = Field(..., ge=0.0)
    median_retention_time_minutes: float | None = Field(default=None, ge=0.0)
    quality_flag_count: int = Field(..., ge=0)
    flagged_sample_count: int = Field(..., ge=0)


class TargetedMatrixSummary(JsonModel):
    """Compact summary over one targeted precursor matrix."""

    model_config = ConfigDict(extra="forbid")

    target_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    observed_cell_count: int = Field(..., ge=0)
    missing_cell_count: int = Field(..., ge=0)
    zero_passing_cell_count: int = Field(..., ge=0)
    retained_transition_count: int = Field(..., ge=0)
    excluded_transition_count: int = Field(..., ge=0)
    quality_flag_count: int = Field(..., ge=0)


class TargetedRetainedTransitionEntry(JsonModel):
    """One retained transition observation used by the target matrix."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    transition_id: str = Field(..., min_length=1)
    intensity: float = Field(..., ge=0.0)
    retention_time_minutes: float | None = Field(default=None, ge=0.0)
    quality_flag: str | None = None


class TargetedExcludedTransitionEntry(JsonModel):
    """One excluded transition observation kept visible beside the target matrix."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    transition_id: str = Field(..., min_length=1)
    intensity: float = Field(..., ge=0.0)
    retention_time_minutes: float | None = Field(default=None, ge=0.0)
    quality_flag: str | None = None
    exclusion_reason: str = Field(..., min_length=1)


class TargetedMissingnessEntry(JsonModel):
    """One target-by-sample missingness decision for the retained matrix."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    observed_transition_count: int = Field(..., ge=0)
    retained_transition_count: int = Field(..., ge=0)
    excluded_transition_count: int = Field(..., ge=0)
    missing: bool
    missing_reason: str | None = None


class TargetedMatrixReport(JsonModel):
    """Owned targeted precursor-target matrix with sample-resolved intensities."""

    model_config = ConfigDict(extra="forbid")

    source_name: str = Field(..., min_length=1)
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    rows: tuple[TargetedMatrixRow, ...] = Field(default_factory=tuple)
    retained_transitions: tuple[TargetedRetainedTransitionEntry, ...] = Field(
        default_factory=tuple
    )
    excluded_transitions: tuple[TargetedExcludedTransitionEntry, ...] = Field(
        default_factory=tuple
    )
    missingness: tuple[TargetedMissingnessEntry, ...] = Field(default_factory=tuple)
    summary: TargetedMatrixSummary
    note: str = Field(..., min_length=1)


def build_targeted_matrix_report(
    import_report: TargetedResultImportReport,
) -> TargetedMatrixReport:
    """Build one targeted precursor matrix from imported targeted observations."""

    sample_ids = tuple(sorted({item.sample_id for item in import_report.observations}))
    grouped: dict[str, list[TargetedResultObservation]] = {}
    for observation in import_report.observations:
        grouped.setdefault(observation.precursor_id, []).append(observation)

    rows: list[TargetedMatrixRow] = []
    retained_transitions: list[TargetedRetainedTransitionEntry] = []
    excluded_transitions: list[TargetedExcludedTransitionEntry] = []
    missingness: list[TargetedMissingnessEntry] = []
    observed_cell_count = 0
    missing_cell_count = 0
    zero_passing_cell_count = 0
    retained_transition_count = 0
    excluded_transition_count = 0
    quality_flag_count = 0
    for target_id, observations in sorted(grouped.items()):
        sample_values: list[TargetedMatrixValue] = []
        peptide_sequence = observations[0].peptide_sequence
        protein_ref = observations[0].protein_ref
        source_transition_ids = tuple(
            sorted({item.transition_id for item in observations})
        )
        row_retained_transition_ids: set[str] = set()
        row_excluded_transition_ids: set[str] = set()
        detected_intensities: list[float] = []
        retention_times: list[float] = []
        row_quality_flag_count = 0
        flagged_sample_count = 0
        for sample_id in sample_ids:
            sample_observations = [
                item for item in observations if item.sample_id == sample_id
            ]
            if not sample_observations:
                missing_cell_count += 1
                missingness.append(
                    TargetedMissingnessEntry(
                        target_id=target_id,
                        sample_id=sample_id,
                        observed_transition_count=0,
                        retained_transition_count=0,
                        excluded_transition_count=0,
                        missing=True,
                        missing_reason="no_observation",
                    )
                )
                sample_values.append(
                    TargetedMatrixValue(
                        sample_id=sample_id,
                        observed_transition_count=0,
                        retained_transition_count=0,
                        excluded_transition_count=0,
                        missing_reason="no_observation",
                        detected=False,
                    )
                )
                continue
            retained_observations = [
                item for item in sample_observations if _passes_matrix_filter(item)
            ]
            excluded_observations = [
                item for item in sample_observations if not _passes_matrix_filter(item)
            ]
            retained_ids = tuple(
                sorted({item.transition_id for item in retained_observations})
            )
            excluded_ids = tuple(
                sorted({item.transition_id for item in excluded_observations})
            )
            row_retained_transition_ids.update(retained_ids)
            row_excluded_transition_ids.update(excluded_ids)
            retained_transition_count += len(retained_observations)
            excluded_transition_count += len(excluded_observations)
            intensity = sum(item.intensity for item in retained_observations)
            sample_retention_times = [
                item.retention_time_minutes
                for item in retained_observations
                if item.retention_time_minutes is not None
            ]
            sample_quality_flags = tuple(
                sorted(
                    {
                        item.quality_flag
                        for item in excluded_observations
                        if item.quality_flag is not None and item.quality_flag != "pass"
                    }
                )
            )
            row_quality_flag_count += len(sample_quality_flags)
            quality_flag_count += len(sample_quality_flags)
            if sample_quality_flags:
                flagged_sample_count += 1
            for item in retained_observations:
                retained_transitions.append(
                    TargetedRetainedTransitionEntry(
                        target_id=target_id,
                        sample_id=sample_id,
                        transition_id=item.transition_id,
                        intensity=item.intensity,
                        retention_time_minutes=item.retention_time_minutes,
                        quality_flag=item.quality_flag,
                    )
                )
            for item in excluded_observations:
                excluded_transitions.append(
                    TargetedExcludedTransitionEntry(
                        target_id=target_id,
                        sample_id=sample_id,
                        transition_id=item.transition_id,
                        intensity=item.intensity,
                        retention_time_minutes=item.retention_time_minutes,
                        quality_flag=item.quality_flag,
                        exclusion_reason="quality_filter",
                    )
                )
            if retained_observations:
                observed_cell_count += 1
                detected_intensities.append(intensity)
                retention_times.extend(sample_retention_times)
                missingness.append(
                    TargetedMissingnessEntry(
                        target_id=target_id,
                        sample_id=sample_id,
                        observed_transition_count=len(sample_observations),
                        retained_transition_count=len(retained_observations),
                        excluded_transition_count=len(excluded_observations),
                        missing=False,
                    )
                )
            else:
                missing_cell_count += 1
                zero_passing_cell_count += 1
                missingness.append(
                    TargetedMissingnessEntry(
                        target_id=target_id,
                        sample_id=sample_id,
                        observed_transition_count=len(sample_observations),
                        retained_transition_count=0,
                        excluded_transition_count=len(excluded_observations),
                        missing=True,
                        missing_reason="no_passing_transitions",
                    )
                )
            sample_values.append(
                TargetedMatrixValue(
                    sample_id=sample_id,
                    source_transition_ids=tuple(
                        sorted({item.transition_id for item in sample_observations})
                    ),
                    retained_transition_ids=retained_ids,
                    excluded_transition_ids=excluded_ids,
                    observed_transition_count=len(sample_observations),
                    retained_transition_count=len(retained_observations),
                    excluded_transition_count=len(excluded_observations),
                    intensity=intensity if retained_observations else None,
                    retention_time_minutes=(
                        sum(sample_retention_times) / len(sample_retention_times)
                        if sample_retention_times
                        else None
                    ),
                    quality_flags=sample_quality_flags,
                    missing_reason=(
                        None if retained_observations else "no_passing_transitions"
                    ),
                    detected=bool(retained_observations),
                )
            )
        rows.append(
            TargetedMatrixRow(
                target_id=target_id,
                peptide_sequence=peptide_sequence,
                protein_ref=protein_ref,
                source_transition_ids=source_transition_ids,
                retained_transition_ids=tuple(sorted(row_retained_transition_ids)),
                excluded_transition_ids=tuple(sorted(row_excluded_transition_ids)),
                values=tuple(sample_values),
                retained_transition_count=len(row_retained_transition_ids),
                excluded_transition_count=len(row_excluded_transition_ids),
                detected_sample_count=len(detected_intensities),
                total_intensity=sum(detected_intensities),
                mean_intensity=(
                    sum(detected_intensities) / len(detected_intensities)
                    if detected_intensities
                    else 0.0
                ),
                median_retention_time_minutes=_median(retention_times),
                quality_flag_count=row_quality_flag_count,
                flagged_sample_count=flagged_sample_count,
            )
        )
    return TargetedMatrixReport(
        source_name=import_report.source_name,
        sample_ids=sample_ids,
        rows=tuple(rows),
        retained_transitions=tuple(
            sorted(
                retained_transitions,
                key=lambda item: (
                    item.target_id,
                    item.sample_id,
                    item.transition_id,
                ),
            )
        ),
        excluded_transitions=tuple(
            sorted(
                excluded_transitions,
                key=lambda item: (
                    item.target_id,
                    item.sample_id,
                    item.transition_id,
                ),
            )
        ),
        missingness=tuple(
            sorted(
                missingness,
                key=lambda item: (
                    item.target_id,
                    item.sample_id,
                ),
            )
        ),
        summary=TargetedMatrixSummary(
            target_count=len(rows),
            sample_count=len(sample_ids),
            observed_cell_count=observed_cell_count,
            missing_cell_count=missing_cell_count,
            zero_passing_cell_count=zero_passing_cell_count,
            retained_transition_count=retained_transition_count,
            excluded_transition_count=excluded_transition_count,
            quality_flag_count=quality_flag_count,
        ),
        note=(
            "target matrix rolls imported targeted transition observations up to precursor targets while preserving retained-versus-excluded transition evidence, sample-resolved missingness, retention-time evidence, quality flags, and source transition linkage"
        ),
    )


def build_skyline_targeted_matrix_report(path: Path) -> TargetedMatrixReport:
    """Build one targeted precursor matrix directly from a Skyline-style export."""

    return build_targeted_matrix_report(build_skyline_result_import_report(path))


def build_transition_table_targeted_matrix_report(path: Path) -> TargetedMatrixReport:
    """Build one targeted precursor matrix directly from an exported transition table."""

    return build_targeted_matrix_report(
        build_transition_table_result_import_report(path)
    )


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2.0


def _passes_matrix_filter(observation: TargetedResultObservation) -> bool:
    quality_flag = observation.quality_flag
    return quality_flag is None or quality_flag == "pass"


def render_targeted_matrix_summary_tsv(report: TargetedMatrixReport) -> str:
    """Render the compact summary for one targeted target matrix."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "source_name",
            "target_count",
            "sample_count",
            "observed_cell_count",
            "missing_cell_count",
            "zero_passing_cell_count",
            "retained_transition_count",
            "excluded_transition_count",
            "quality_flag_count",
            "note",
        ]
    )
    writer.writerow(
        [
            report.source_name,
            report.summary.target_count,
            report.summary.sample_count,
            report.summary.observed_cell_count,
            report.summary.missing_cell_count,
            report.summary.zero_passing_cell_count,
            report.summary.retained_transition_count,
            report.summary.excluded_transition_count,
            report.summary.quality_flag_count,
            report.note,
        ]
    )
    return buffer.getvalue()


def render_targeted_matrix_target_tsv(report: TargetedMatrixReport) -> str:
    """Render the target-level matrix ledger as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "target_id",
            "peptide_sequence",
            "protein_ref",
            "source_transition_ids",
            "retained_transition_ids",
            "excluded_transition_ids",
            "retained_transition_count",
            "excluded_transition_count",
            "detected_sample_count",
            "total_intensity",
            "mean_intensity",
            "median_retention_time_minutes",
            "quality_flag_count",
            "flagged_sample_count",
        ]
    )
    for row in report.rows:
        writer.writerow(
            [
                row.target_id,
                row.peptide_sequence,
                "" if row.protein_ref is None else row.protein_ref,
                ";".join(row.source_transition_ids),
                ";".join(row.retained_transition_ids),
                ";".join(row.excluded_transition_ids),
                row.retained_transition_count,
                row.excluded_transition_count,
                row.detected_sample_count,
                f"{row.total_intensity:g}",
                f"{row.mean_intensity:g}",
                (
                    ""
                    if row.median_retention_time_minutes is None
                    else f"{row.median_retention_time_minutes:g}"
                ),
                row.quality_flag_count,
                row.flagged_sample_count,
            ]
        )
    return buffer.getvalue()


def render_targeted_matrix_sample_tsv(report: TargetedMatrixReport) -> str:
    """Render the sample-resolved targeted matrix ledger as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "target_id",
            "sample_id",
            "source_transition_ids",
            "retained_transition_ids",
            "excluded_transition_ids",
            "observed_transition_count",
            "retained_transition_count",
            "excluded_transition_count",
            "intensity",
            "retention_time_minutes",
            "quality_flags",
            "missing_reason",
            "detected",
        ]
    )
    for row in report.rows:
        for value in row.values:
            writer.writerow(
                [
                    row.target_id,
                    value.sample_id,
                    ";".join(value.source_transition_ids),
                    ";".join(value.retained_transition_ids),
                    ";".join(value.excluded_transition_ids),
                    value.observed_transition_count,
                    value.retained_transition_count,
                    value.excluded_transition_count,
                    "" if value.intensity is None else f"{value.intensity:g}",
                    (
                        ""
                        if value.retention_time_minutes is None
                        else f"{value.retention_time_minutes:g}"
                    ),
                    ";".join(value.quality_flags),
                    "" if value.missing_reason is None else value.missing_reason,
                    str(value.detected).lower(),
                ]
            )
    return buffer.getvalue()


def render_targeted_matrix_retained_transition_tsv(report: TargetedMatrixReport) -> str:
    """Render retained transition observations used by the target matrix."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "target_id",
            "sample_id",
            "transition_id",
            "intensity",
            "retention_time_minutes",
            "quality_flag",
        ]
    )
    for entry in report.retained_transitions:
        writer.writerow(
            [
                entry.target_id,
                entry.sample_id,
                entry.transition_id,
                f"{entry.intensity:g}",
                (
                    ""
                    if entry.retention_time_minutes is None
                    else f"{entry.retention_time_minutes:g}"
                ),
                "" if entry.quality_flag is None else entry.quality_flag,
            ]
        )
    return buffer.getvalue()


def render_targeted_matrix_excluded_transition_tsv(report: TargetedMatrixReport) -> str:
    """Render excluded transition observations beside the target matrix."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "target_id",
            "sample_id",
            "transition_id",
            "intensity",
            "retention_time_minutes",
            "quality_flag",
            "exclusion_reason",
        ]
    )
    for entry in report.excluded_transitions:
        writer.writerow(
            [
                entry.target_id,
                entry.sample_id,
                entry.transition_id,
                f"{entry.intensity:g}",
                (
                    ""
                    if entry.retention_time_minutes is None
                    else f"{entry.retention_time_minutes:g}"
                ),
                "" if entry.quality_flag is None else entry.quality_flag,
                entry.exclusion_reason,
            ]
        )
    return buffer.getvalue()


def render_targeted_matrix_missingness_tsv(report: TargetedMatrixReport) -> str:
    """Render target-by-sample missingness decisions for the retained matrix."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "target_id",
            "sample_id",
            "observed_transition_count",
            "retained_transition_count",
            "excluded_transition_count",
            "missing",
            "missing_reason",
        ]
    )
    for entry in report.missingness:
        writer.writerow(
            [
                entry.target_id,
                entry.sample_id,
                entry.observed_transition_count,
                entry.retained_transition_count,
                entry.excluded_transition_count,
                str(entry.missing).lower(),
                "" if entry.missing_reason is None else entry.missing_reason,
            ]
        )
    return buffer.getvalue()


def render_targeted_matrix_flagged_tsv(report: TargetedMatrixReport) -> str:
    """Render one flagged-target ledger as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "target_id",
            "peptide_sequence",
            "protein_ref",
            "quality_flag_count",
            "flagged_sample_count",
        ]
    )
    for row in report.rows:
        if row.quality_flag_count <= 0:
            continue
        writer.writerow(
            [
                row.target_id,
                row.peptide_sequence,
                "" if row.protein_ref is None else row.protein_ref,
                row.quality_flag_count,
                row.flagged_sample_count,
            ]
        )
    return buffer.getvalue()
