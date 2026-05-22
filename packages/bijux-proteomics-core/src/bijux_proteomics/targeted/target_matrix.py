# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned target-matrix review surfaces over imported targeted observations."""

from __future__ import annotations

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
    intensity: float | None = Field(default=None, ge=0.0)
    retention_time_minutes: float | None = Field(default=None, ge=0.0)
    quality_flags: tuple[str, ...] = Field(default_factory=tuple)
    detected: bool


class TargetedMatrixRow(JsonModel):
    """One precursor-target row across all samples."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    protein_ref: str | None = None
    source_transition_ids: tuple[str, ...] = Field(default_factory=tuple)
    values: tuple[TargetedMatrixValue, ...] = Field(default_factory=tuple)
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
    quality_flag_count: int = Field(..., ge=0)


class TargetedMatrixReport(JsonModel):
    """Owned targeted precursor-target matrix with sample-resolved intensities."""

    model_config = ConfigDict(extra="forbid")

    source_name: str = Field(..., min_length=1)
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    rows: tuple[TargetedMatrixRow, ...] = Field(default_factory=tuple)
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
    observed_cell_count = 0
    missing_cell_count = 0
    quality_flag_count = 0
    for target_id, observations in sorted(grouped.items()):
        sample_values: list[TargetedMatrixValue] = []
        peptide_sequence = observations[0].peptide_sequence
        protein_ref = observations[0].protein_ref
        source_transition_ids = tuple(
            sorted({item.transition_id for item in observations})
        )
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
                sample_values.append(
                    TargetedMatrixValue(
                        sample_id=sample_id,
                        detected=False,
                    )
                )
                continue
            observed_cell_count += 1
            intensity = sum(item.intensity for item in sample_observations)
            sample_retention_times = [
                item.retention_time_minutes
                for item in sample_observations
                if item.retention_time_minutes is not None
            ]
            sample_quality_flags = tuple(
                sorted(
                    {
                        item.quality_flag
                        for item in sample_observations
                        if item.quality_flag is not None and item.quality_flag != "pass"
                    }
                )
            )
            detected_intensities.append(intensity)
            retention_times.extend(sample_retention_times)
            row_quality_flag_count += len(sample_quality_flags)
            quality_flag_count += len(sample_quality_flags)
            if sample_quality_flags:
                flagged_sample_count += 1
            sample_values.append(
                TargetedMatrixValue(
                    sample_id=sample_id,
                    source_transition_ids=tuple(
                        sorted({item.transition_id for item in sample_observations})
                    ),
                    intensity=intensity,
                    retention_time_minutes=(
                        sum(sample_retention_times) / len(sample_retention_times)
                        if sample_retention_times
                        else None
                    ),
                    quality_flags=sample_quality_flags,
                    detected=True,
                )
            )
        rows.append(
            TargetedMatrixRow(
                target_id=target_id,
                peptide_sequence=peptide_sequence,
                protein_ref=protein_ref,
                source_transition_ids=source_transition_ids,
                values=tuple(sample_values),
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
        summary=TargetedMatrixSummary(
            target_count=len(rows),
            sample_count=len(sample_ids),
            observed_cell_count=observed_cell_count,
            missing_cell_count=missing_cell_count,
            quality_flag_count=quality_flag_count,
        ),
        note=(
            "target matrix rolls imported targeted transition observations up to precursor targets while preserving sample-resolved intensities, retention-time evidence, quality flags, and source transition linkage"
        ),
    )


def build_skyline_targeted_matrix_report(path: Path) -> TargetedMatrixReport:
    """Build one targeted precursor matrix directly from a Skyline-style export."""

    return build_targeted_matrix_report(build_skyline_result_import_report(path))


def build_transition_table_targeted_matrix_report(path: Path) -> TargetedMatrixReport:
    """Build one targeted precursor matrix directly from an exported transition table."""

    return build_targeted_matrix_report(build_transition_table_result_import_report(path))


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2.0
