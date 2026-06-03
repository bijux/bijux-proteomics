# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Score targeted transition-ratio drift across samples."""

from __future__ import annotations

import csv
from io import StringIO
from statistics import median

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class TargetedFragmentRatioMatrixEntry(JsonModel):
    """One targeted transition intensity inside one sample-level precursor group."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    transition_id: str = Field(..., min_length=1)
    intensity: float = Field(..., ge=0.0)


class TargetedFragmentRatioDriftEntry(JsonModel):
    """One targeted transition ratio-drift summary across all observed samples."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    transition_id: str = Field(..., min_length=1)
    expected_ratio: float = Field(..., ge=0.0, le=1.0)
    observed_ratio_cv: float | None = Field(default=None, ge=0.0)
    drift_flag: bool = False


def score_fragment_ratio_drift(
    transition_matrix: tuple[TargetedFragmentRatioMatrixEntry, ...],
    *,
    observed_ratio_cv_threshold: float = 0.25,
) -> tuple[TargetedFragmentRatioDriftEntry, ...]:
    """Score targeted transition-ratio drift across observed sample groups."""

    if not transition_matrix:
        raise ValueError("transition_matrix must not be empty")
    if observed_ratio_cv_threshold <= 0.0:
        raise ValueError("observed_ratio_cv_threshold must be greater than zero")

    grouped_by_sample: dict[
        tuple[str, str], list[TargetedFragmentRatioMatrixEntry]
    ] = {}
    for entry in transition_matrix:
        grouped_by_sample.setdefault((entry.target_id, entry.sample_id), []).append(
            entry
        )

    ratios_by_transition: dict[tuple[str, str], list[float]] = {}
    for (target_id, _sample_id), sample_entries in sorted(grouped_by_sample.items()):
        total_intensity = sum(entry.intensity for entry in sample_entries)
        if total_intensity <= 0.0:
            continue
        for entry in sample_entries:
            ratios_by_transition.setdefault(
                (target_id, entry.transition_id), []
            ).append(entry.intensity / total_intensity)

    rows: list[TargetedFragmentRatioDriftEntry] = []
    for (target_id, transition_id), observed_ratios in sorted(
        ratios_by_transition.items()
    ):
        expected_ratio = median(observed_ratios)
        observed_ratio_cv = _coefficient_of_variation(observed_ratios)
        drift_flag = bool(
            observed_ratio_cv is not None
            and observed_ratio_cv > observed_ratio_cv_threshold
        )
        rows.append(
            TargetedFragmentRatioDriftEntry(
                target_id=target_id,
                transition_id=transition_id,
                expected_ratio=round(expected_ratio, 6),
                observed_ratio_cv=(
                    None if observed_ratio_cv is None else round(observed_ratio_cv, 6)
                ),
                drift_flag=drift_flag,
            )
        )
    return tuple(rows)


def render_fragment_ratio_drift_tsv(
    rows: tuple[TargetedFragmentRatioDriftEntry, ...],
) -> str:
    """Render targeted transition-ratio drift summaries as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "target_id",
            "transition_id",
            "expected_ratio",
            "observed_ratio_cv",
            "drift_flag",
        )
    )
    for row in rows:
        writer.writerow(
            (
                row.target_id,
                row.transition_id,
                f"{row.expected_ratio:.6f}",
                "" if row.observed_ratio_cv is None else f"{row.observed_ratio_cv:.6f}",
                str(row.drift_flag).lower(),
            )
        )
    return buffer.getvalue()


def _coefficient_of_variation(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    mean_value = sum(values) / len(values)
    if mean_value <= 0.0:
        return None
    squared_distance_sum = sum((value - mean_value) ** 2 for value in values)
    variance = float(squared_distance_sum / (len(values) - 1))
    return float(variance**0.5 / mean_value)
