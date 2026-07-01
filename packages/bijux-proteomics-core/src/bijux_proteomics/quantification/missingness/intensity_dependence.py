# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Intensity-dependent missingness profiling."""

from __future__ import annotations

import math

import numpy as np

from bijux_proteomics.quantification.contracts.input_models import MissingValueKind
from bijux_proteomics.quantification.contracts.matrix_building import (
    _matrix_value_index,
)
from bijux_proteomics.quantification.contracts.matrix_models import LabelFreeQuantTable
from bijux_proteomics.quantification.contracts.missingness import (
    MissingnessIntensityBinEntry,
    MissingnessIntensityDependenceReport,
    MissingnessIntensityPoint,
    MissingValueSummaryPolicy,
)
from bijux_proteomics.quantification.matrix import (
    build_dense_label_free_quant_table_view,
)
from bijux_proteomics.quantification.missingness.policy import (
    _MISSING_BURDEN_CODES,
    _OBSERVED_VALUE_CODES,
    apply_missing_value_summary_policy,
    apply_missing_value_summary_policy_codes,
    is_missing_burden,
)


def build_missingness_intensity_dependence_report(
    table: LabelFreeQuantTable,
    *,
    bin_count: int = 4,
    policy: MissingValueSummaryPolicy | None = None,
) -> MissingnessIntensityDependenceReport:
    return _build_missingness_intensity_dependence_report_vectorized(
        table,
        bin_count=bin_count,
        policy=policy,
    )


def _build_missingness_intensity_dependence_report_pure(
    table: LabelFreeQuantTable,
    *,
    bin_count: int = 4,
    policy: MissingValueSummaryPolicy | None = None,
) -> MissingnessIntensityDependenceReport:
    """Profile how missingness burden changes with observed abundance intensity."""
    active_policy = policy or MissingValueSummaryPolicy()
    lookup = _matrix_value_index(table)
    points: list[MissingnessIntensityPoint] = []
    for entity_id in table.entity_ids:
        observed_abundances = [
            float(value.abundance or 0.0)
            for value in table.values
            if value.entity_id == entity_id
            and value.abundance is not None
            and apply_missing_value_summary_policy(
                value.missing_value_kind,
                policy=active_policy,
            )
            in (
                MissingValueKind.OBSERVED,
                MissingValueKind.ZERO,
                MissingValueKind.IMPUTED,
            )
        ]
        if not observed_abundances:
            continue
        missing_count = sum(
            1
            for sample_id in table.sample_ids
            if is_missing_burden(
                apply_missing_value_summary_policy(
                    lookup[(entity_id, sample_id)].missing_value_kind,
                    policy=active_policy,
                )
            )
        )
        points.append(
            MissingnessIntensityPoint(
                entity_id=entity_id,
                mean_log2_observed_abundance=float(
                    np.mean(np.log2(np.array(observed_abundances, dtype=float) + 1.0))
                ),
                missing_fraction=float(missing_count / len(table.sample_ids))
                if table.sample_ids
                else 0.0,
            )
        )

    ordered_points = tuple(
        sorted(points, key=lambda point: point.mean_log2_observed_abundance)
    )
    bins: list[MissingnessIntensityBinEntry] = []
    if ordered_points:
        active_bin_count = max(1, min(bin_count, len(ordered_points)))
        groups = np.array_split(
            np.array(ordered_points, dtype=object), active_bin_count
        )
        for group in groups:
            bucket = [point for point in group.tolist() if point is not None]
            if not bucket:
                continue
            bins.append(
                MissingnessIntensityBinEntry(
                    lower_log2_abundance=bucket[0].mean_log2_observed_abundance,
                    upper_log2_abundance=bucket[-1].mean_log2_observed_abundance,
                    entity_count=len(bucket),
                    mean_missing_fraction=float(
                        np.mean(
                            np.array(
                                [point.missing_fraction for point in bucket],
                                dtype=float,
                            )
                        )
                    ),
                )
            )

    trend_correlation = _trend_correlation(ordered_points)
    detected = (
        trend_correlation is not None
        and trend_correlation <= -0.5
        and any(point.missing_fraction > 0.0 for point in ordered_points)
    )
    return MissingnessIntensityDependenceReport(
        entity_level=table.entity_level,
        plot_points=ordered_points,
        bins=tuple(bins),
        trend_correlation=trend_correlation,
        intensity_dependent_missingness_detected=detected,
    )


def _build_missingness_intensity_dependence_report_vectorized(
    table: LabelFreeQuantTable,
    *,
    bin_count: int = 4,
    policy: MissingValueSummaryPolicy | None = None,
) -> MissingnessIntensityDependenceReport:
    active_policy = policy or MissingValueSummaryPolicy()
    dense_view = build_dense_label_free_quant_table_view(table)
    missing_kind_codes = apply_missing_value_summary_policy_codes(
        dense_view.missing_kind_codes,
        policy=active_policy,
    )
    observed_like_mask = np.isin(missing_kind_codes, _OBSERVED_VALUE_CODES)
    missing_burden_mask = np.isin(missing_kind_codes, _MISSING_BURDEN_CODES)
    observed_abundance = np.where(
        observed_like_mask,
        dense_view.abundance_matrix,
        np.nan,
    )
    has_observed = np.any(~np.isnan(observed_abundance), axis=1)
    logged_observed_abundance = np.where(
        np.isnan(observed_abundance),
        np.nan,
        np.log2(observed_abundance + 1.0),
    )
    observed_counts = np.sum(~np.isnan(logged_observed_abundance), axis=1)
    mean_log2_observed = np.divide(
        np.nansum(logged_observed_abundance, axis=1),
        observed_counts,
        out=np.full(len(table.entity_ids), np.nan, dtype=float),
        where=observed_counts > 0,
    )
    missing_fraction = (
        np.sum(missing_burden_mask, axis=1) / len(table.sample_ids)
        if table.sample_ids
        else np.zeros(len(table.entity_ids), dtype=float)
    )
    points = tuple(
        MissingnessIntensityPoint(
            entity_id=entity_id,
            mean_log2_observed_abundance=float(mean_log2_observed[row_index]),
            missing_fraction=float(missing_fraction[row_index]),
        )
        for row_index, entity_id in enumerate(table.entity_ids)
        if has_observed[row_index]
    )
    ordered_points = tuple(
        sorted(points, key=lambda point: point.mean_log2_observed_abundance)
    )
    bins: list[MissingnessIntensityBinEntry] = []
    if ordered_points:
        active_bin_count = max(1, min(bin_count, len(ordered_points)))
        groups = np.array_split(
            np.array(ordered_points, dtype=object), active_bin_count
        )
        for group in groups:
            bucket = [point for point in group.tolist() if point is not None]
            if not bucket:
                continue
            bins.append(
                MissingnessIntensityBinEntry(
                    lower_log2_abundance=bucket[0].mean_log2_observed_abundance,
                    upper_log2_abundance=bucket[-1].mean_log2_observed_abundance,
                    entity_count=len(bucket),
                    mean_missing_fraction=float(
                        np.mean(
                            np.array(
                                [point.missing_fraction for point in bucket],
                                dtype=float,
                            )
                        )
                    ),
                )
            )
    trend_correlation = _trend_correlation(ordered_points)
    detected = (
        trend_correlation is not None
        and trend_correlation <= -0.5
        and any(point.missing_fraction > 0.0 for point in ordered_points)
    )
    return MissingnessIntensityDependenceReport(
        entity_level=table.entity_level,
        plot_points=ordered_points,
        bins=tuple(bins),
        trend_correlation=trend_correlation,
        intensity_dependent_missingness_detected=detected,
    )


def low_intensity_cutoff(report: MissingnessIntensityDependenceReport) -> float:
    if not report.plot_points:
        return math.inf
    values = np.array(
        [point.mean_log2_observed_abundance for point in report.plot_points],
        dtype=float,
    )
    return min(
        float(np.quantile(values, 0.2)),
        float(np.median(values) - 1.0),
    )


def _trend_correlation(
    ordered_points: tuple[MissingnessIntensityPoint, ...],
) -> float | None:
    if len(ordered_points) < 2:
        return None
    x = np.array(
        [point.mean_log2_observed_abundance for point in ordered_points],
        dtype=float,
    )
    y = np.array([point.missing_fraction for point in ordered_points], dtype=float)
    if np.std(x) <= 0.0 or np.std(y) <= 0.0:
        return None
    correlation = float(np.corrcoef(x, y)[0, 1])
    return correlation if math.isfinite(correlation) else None
