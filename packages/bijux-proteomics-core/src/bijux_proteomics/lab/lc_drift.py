# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Run-order LC drift detection over governed run-QC tables."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from statistics import median

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class LcDriftDimension(StrEnum):
    """Stable run-QC dimensions that can drift across injection order."""

    MEDIAN_RT = "median_rt"
    TIC = "tic"
    MS2_COUNT = "ms2_count"
    ID_COUNT = "id_count"
    MEDIAN_PEAK_WIDTH = "median_peak_width"


class LcDriftDirection(StrEnum):
    """Stable direction for a gradual LC drift pattern."""

    INCREASING = "increasing"
    DECREASING = "decreasing"


class LcDriftSeverity(StrEnum):
    """Stable severity tiers for gradual LC drift."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class LcDriftRunQcEntry(JsonModel):
    """One ordered run-QC row used for LC drift detection."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    run_order: int = Field(..., ge=1)
    median_rt: float = Field(..., ge=0.0)
    tic: float = Field(..., ge=0.0)
    ms2_count: int = Field(..., ge=0)
    id_count: int = Field(..., ge=0)
    median_peak_width: float = Field(..., ge=0.0)


class LcDriftDetectionEntry(JsonModel):
    """One run and QC dimension affected by gradual LC drift."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    run_order: int = Field(..., ge=1)
    drift_metric: float = Field(..., ge=0.0)
    drift_direction: LcDriftDirection
    drift_severity: LcDriftSeverity
    affected_qc_dimension: LcDriftDimension


class _LcDriftMetricPolicy(JsonModel):
    """Thresholds that keep gradual drift separate from one-run failures."""

    model_config = ConfigDict(extra="forbid")

    minimum_relative_shift: float = Field(..., gt=0.0)
    minimum_row_shift: float = Field(..., gt=0.0)


_DRIFT_POLICIES: dict[LcDriftDimension, _LcDriftMetricPolicy] = {
    LcDriftDimension.MEDIAN_RT: _LcDriftMetricPolicy(
        minimum_relative_shift=0.04,
        minimum_row_shift=0.02,
    ),
    LcDriftDimension.TIC: _LcDriftMetricPolicy(
        minimum_relative_shift=0.12,
        minimum_row_shift=0.06,
    ),
    LcDriftDimension.MS2_COUNT: _LcDriftMetricPolicy(
        minimum_relative_shift=0.12,
        minimum_row_shift=0.06,
    ),
    LcDriftDimension.ID_COUNT: _LcDriftMetricPolicy(
        minimum_relative_shift=0.12,
        minimum_row_shift=0.06,
    ),
    LcDriftDimension.MEDIAN_PEAK_WIDTH: _LcDriftMetricPolicy(
        minimum_relative_shift=0.08,
        minimum_row_shift=0.04,
    ),
}


def detect_lc_drift(
    run_qc_table: tuple[LcDriftRunQcEntry, ...],
    *,
    minimum_correlation: float = 0.85,
    minimum_directional_fraction: float = 0.75,
    maximum_step_concentration: float = 0.6,
) -> tuple[LcDriftDetectionEntry, ...]:
    """Detect gradual run-order LC drift separately from one-run QC failures."""

    if len(run_qc_table) < 4:
        raise ValueError("lc_drift analysis requires at least four ordered runs")
    if not 0.0 < minimum_correlation <= 1.0:
        raise ValueError("minimum_correlation must be between 0 and 1")
    if not 0.0 < minimum_directional_fraction <= 1.0:
        raise ValueError("minimum_directional_fraction must be between 0 and 1")
    if not 0.0 < maximum_step_concentration <= 1.0:
        raise ValueError("maximum_step_concentration must be between 0 and 1")

    ordered_runs = _ordered_runs(run_qc_table)
    baseline_window = max(2, len(ordered_runs) // 3)
    rows: list[LcDriftDetectionEntry] = []

    for dimension, policy in _DRIFT_POLICIES.items():
        values = [_metric_value(entry, dimension) for entry in ordered_runs]
        shift_fraction = _half_median_shift_fraction(values)
        if shift_fraction < policy.minimum_relative_shift:
            continue

        correlation = _pearson_correlation(
            [entry.run_order for entry in ordered_runs],
            values,
        )
        if correlation is None or abs(correlation) < minimum_correlation:
            continue

        deltas = [right - left for left, right in zip(values, values[1:], strict=False)]
        total_absolute_delta = sum(abs(delta) for delta in deltas)
        if total_absolute_delta <= 0.0:
            continue

        direction = (
            LcDriftDirection.INCREASING
            if correlation > 0.0
            else LcDriftDirection.DECREASING
        )
        directional_fraction = _directional_fraction(deltas, direction)
        if directional_fraction < minimum_directional_fraction:
            continue

        # A genuine drift spreads movement across the sequence instead of one jump.
        step_concentration = max(abs(delta) for delta in deltas) / total_absolute_delta
        if step_concentration > maximum_step_concentration:
            continue

        baseline_value = median(
            _metric_value(entry, dimension) for entry in ordered_runs[:baseline_window]
        )
        scale = max(abs(baseline_value), abs(median(values)), 1.0)
        trend_support = abs(correlation) * directional_fraction * (
            1.0 - step_concentration
        )

        for entry in ordered_runs[baseline_window:]:
            relative_shift = abs(_metric_value(entry, dimension) - baseline_value) / scale
            if relative_shift < policy.minimum_row_shift:
                continue
            drift_metric = round(relative_shift * trend_support, 4)
            if drift_metric <= 0.0:
                continue
            rows.append(
                LcDriftDetectionEntry(
                    run_id=entry.run_id,
                    run_order=entry.run_order,
                    drift_metric=drift_metric,
                    drift_direction=direction,
                    drift_severity=_severity(relative_shift, policy),
                    affected_qc_dimension=dimension,
                )
            )

    return tuple(
        sorted(
            rows,
            key=lambda entry: (
                entry.run_order,
                entry.affected_qc_dimension.value,
                entry.run_id,
            ),
        )
    )


def render_lc_drift_tsv(rows: tuple[LcDriftDetectionEntry, ...]) -> str:
    """Render LC drift detection rows as a governed TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "run_id",
            "drift_metric",
            "drift_direction",
            "drift_severity",
            "affected_qc_dimension",
        )
    )
    for row in rows:
        writer.writerow(
            (
                row.run_id,
                f"{row.drift_metric:.4f}",
                row.drift_direction.value,
                row.drift_severity.value,
                row.affected_qc_dimension.value,
            )
        )
    return buffer.getvalue()


def _ordered_runs(
    run_qc_table: tuple[LcDriftRunQcEntry, ...],
) -> tuple[LcDriftRunQcEntry, ...]:
    duplicate_run_ids = {
        entry.run_id
        for entry in run_qc_table
        if sum(candidate.run_id == entry.run_id for candidate in run_qc_table) > 1
    }
    if duplicate_run_ids:
        raise ValueError(
            "lc_drift analysis requires unique run_id values and found duplicates for: "
            + ", ".join(sorted(duplicate_run_ids))
        )
    duplicate_run_orders = {
        entry.run_order
        for entry in run_qc_table
        if sum(candidate.run_order == entry.run_order for candidate in run_qc_table) > 1
    }
    if duplicate_run_orders:
        raise ValueError(
            "lc_drift analysis requires unique run_order values and found duplicates for: "
            + ", ".join(str(value) for value in sorted(duplicate_run_orders))
        )
    return tuple(sorted(run_qc_table, key=lambda entry: (entry.run_order, entry.run_id)))


def _metric_value(entry: LcDriftRunQcEntry, dimension: LcDriftDimension) -> float:
    if dimension is LcDriftDimension.MEDIAN_RT:
        return entry.median_rt
    if dimension is LcDriftDimension.TIC:
        return entry.tic
    if dimension is LcDriftDimension.MS2_COUNT:
        return float(entry.ms2_count)
    if dimension is LcDriftDimension.ID_COUNT:
        return float(entry.id_count)
    return entry.median_peak_width


def _half_median_shift_fraction(values: list[float]) -> float:
    half_window = max(2, len(values) // 2)
    early_median = median(values[:half_window])
    late_median = median(values[-half_window:])
    scale = max(abs(early_median), abs(late_median), abs(median(values)), 1.0)
    return abs(late_median - early_median) / scale


def _pearson_correlation(x_values: list[int], y_values: list[float]) -> float | None:
    count = len(x_values)
    if count != len(y_values) or count < 2:
        return None
    mean_x = sum(x_values) / count
    mean_y = sum(y_values) / count
    centered_x = [value - mean_x for value in x_values]
    centered_y = [value - mean_y for value in y_values]
    covariance = sum(x * y for x, y in zip(centered_x, centered_y, strict=False))
    variance_x = sum(value * value for value in centered_x)
    variance_y = sum(value * value for value in centered_y)
    if variance_x <= 0.0 or variance_y <= 0.0:
        return None
    return covariance / (variance_x * variance_y) ** 0.5


def _directional_fraction(
    deltas: list[float],
    direction: LcDriftDirection,
) -> float:
    if not deltas:
        return 0.0
    if direction is LcDriftDirection.INCREASING:
        matches = sum(1 for delta in deltas if delta > 0.0)
    else:
        matches = sum(1 for delta in deltas if delta < 0.0)
    return matches / len(deltas)


def _severity(
    relative_shift: float,
    policy: _LcDriftMetricPolicy,
) -> LcDriftSeverity:
    if relative_shift >= max(policy.minimum_relative_shift * 3.0, 0.25):
        return LcDriftSeverity.HIGH
    if relative_shift >= max(policy.minimum_relative_shift * 1.75, 0.12):
        return LcDriftSeverity.MODERATE
    return LcDriftSeverity.LOW


__all__ = [
    "LcDriftDetectionEntry",
    "LcDriftDirection",
    "LcDriftDimension",
    "LcDriftRunQcEntry",
    "LcDriftSeverity",
    "detect_lc_drift",
    "render_lc_drift_tsv",
]
