# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned label-free normalization methods and review summaries."""

from __future__ import annotations

import math
from typing import TypedDict

import numpy as np

from bijux_proteomics.quantification.normalization.composition import (
    CompositionalBiasReport,
    detect_compositional_bias,
)
from bijux_proteomics.quantification.matrix.core_matrix import (
    quant_matrix_to_dense_array,
    rebuild_quant_matrix_from_dense_array,
)
from bijux_proteomics.quantification.contracts import (
    LabelFreeQuantTable,
    NormalizationComparisonReport,
    NormalizationDistributionSnapshot,
    NormalizationLogTransformPreparation,
    NormalizationMethod,
    NormalizationSampleSnapshot,
    NormalizationStrategyComparisonReport,
    NormalizationStrategySummaryEntry,
    QuantMeasureKind,
    _rebuild_table_from_matrix,
    _table_matrix,
)


class _PreparedLogTransform(TypedDict):
    """Typed scratch state for log-domain normalization paths."""

    log_matrix: np.ndarray
    pseudocount: float | None


def build_normalization_comparison_report(
    before: LabelFreeQuantTable,
    after: LabelFreeQuantTable,
) -> NormalizationComparisonReport:
    """Build a before/after normalization summary over sample totals and spread."""
    if before.sample_ids != after.sample_ids or before.entity_ids != after.entity_ids:
        raise ValueError(
            "before and after tables must cover the same sample/entity grid"
        )
    return NormalizationComparisonReport(
        method=after.normalization_method,
        normalization_factors=after.normalization_factors,
        before=tuple(
            _sample_snapshot(before, sample_id) for sample_id in before.sample_ids
        ),
        after=tuple(
            _sample_snapshot(after, sample_id) for sample_id in after.sample_ids
        ),
        before_distributions=tuple(
            _distribution_snapshot(before, sample_id) for sample_id in before.sample_ids
        ),
        after_distributions=tuple(
            _distribution_snapshot(after, sample_id) for sample_id in after.sample_ids
        ),
        log_transform_preparation=_log_transform_preparation(
            before,
            method=after.normalization_method,
        ),
    )


def build_normalization_strategy_comparison_report(
    table: LabelFreeQuantTable,
    *,
    methods: tuple[NormalizationMethod, ...] = (
        NormalizationMethod.NONE,
        NormalizationMethod.TIC,
        NormalizationMethod.MEDIAN,
        NormalizationMethod.QUANTILE,
        NormalizationMethod.LOG2_MEDIAN_CENTERING,
        NormalizationMethod.VSN_LIKE,
    ),
) -> NormalizationStrategyComparisonReport:
    """Compare normalization methods using stable sample-balance summary metrics."""
    composition_report = detect_compositional_bias(table)
    tic_penalty = _tic_composition_penalty(composition_report)
    entries: list[NormalizationStrategySummaryEntry] = []
    for method in methods:
        candidate = normalize_label_free_table(table, method=method)
        snapshots = [
            _sample_snapshot(candidate, sample_id) for sample_id in candidate.sample_ids
        ]
        total_cv = _coefficient_of_variation(
            [snapshot.total_abundance for snapshot in snapshots]
        )
        median_cv = _coefficient_of_variation(
            [snapshot.median_abundance for snapshot in snapshots]
        )
        iqr_cv = _coefficient_of_variation(
            [snapshot.interquartile_range for snapshot in snapshots]
        )
        balance_score = total_cv + median_cv + iqr_cv
        if method is NormalizationMethod.TIC:
            balance_score += tic_penalty
        entries.append(
            NormalizationStrategySummaryEntry(
                method=method,
                total_abundance_cv=total_cv,
                median_abundance_cv=median_cv,
                interquartile_range_cv=iqr_cv,
                balance_score=balance_score,
            )
        )
    ordered = tuple(
        sorted(
            entries,
            key=lambda entry: (entry.balance_score, entry.method.value),
        )
    )
    return NormalizationStrategyComparisonReport(
        entity_level=table.entity_level,
        entries=ordered,
        recommended_method=ordered[0].method,
    )


def normalize_label_free_table(
    table: LabelFreeQuantTable,
    *,
    method: NormalizationMethod = NormalizationMethod.MEDIAN,
) -> LabelFreeQuantTable:
    """Normalize a label-free intensity table with one stable baseline method."""
    if table.measure_kind is not QuantMeasureKind.INTENSITY:
        raise ValueError("normalization only applies to intensity-based quant tables")
    if method is NormalizationMethod.NONE:
        quant_matrix = rebuild_quant_matrix_from_dense_array(
            table.to_quant_matrix(),
            quant_matrix_to_dense_array(table.to_quant_matrix()),
            transformation_step="normalization:none",
            metadata_updates={"normalization_method": method.value},
        )
        return table.model_copy(
            update={
                "quant_matrix": quant_matrix,
                "normalization_method": method,
                "normalization_factors": dict.fromkeys(table.sample_ids, 1.0),
            }
        )

    matrix, _ = _table_matrix(table)
    normalized_matrix, normalization_factors = _normalize_intensity_matrix_vectorized(
        matrix,
        table.sample_ids,
        method=method,
    )
    return _rebuild_table_from_matrix(
        table,
        normalized_matrix,
        normalization_method=method,
        normalization_factors=normalization_factors,
    )


def _normalize_intensity_matrix_pure(
    matrix: np.ndarray,
    sample_ids: tuple[str, ...],
    *,
    method: NormalizationMethod,
) -> tuple[np.ndarray, dict[str, float]]:
    if method is NormalizationMethod.TIC:
        totals = np.nansum(matrix, axis=0)
        global_total = (
            float(np.nanmean(totals[totals > 0])) if np.any(totals > 0) else 1.0
        )
        factors = {
            sample_id: (global_total / float(total)) if total > 0 else 1.0
            for sample_id, total in zip(sample_ids, totals, strict=True)
        }
        scaled = matrix.copy()
        for index, sample_id in enumerate(sample_ids):
            scaled[:, index] = scaled[:, index] * factors[sample_id]
        return scaled, factors

    if method is NormalizationMethod.MEDIAN:
        medians = np.array(
            [
                np.nanmedian(matrix[:, index])
                if np.any(~np.isnan(matrix[:, index]))
                else np.nan
                for index in range(matrix.shape[1])
            ],
            dtype=float,
        )
        global_median = (
            float(np.nanmedian(medians)) if np.any(~np.isnan(medians)) else 1.0
        )
        factors = {
            sample_id: (
                global_median / float(medians[index])
                if math.isfinite(float(medians[index])) and float(medians[index]) > 0
                else 1.0
            )
            for index, sample_id in enumerate(sample_ids)
        }
        scaled = matrix.copy()
        for index, sample_id in enumerate(sample_ids):
            scaled[:, index] = scaled[:, index] * factors[sample_id]
        return scaled, factors

    if method is NormalizationMethod.QUANTILE:
        quantile_matrix = matrix.copy()
        sorted_columns: list[np.ndarray] = []
        original_indexes: list[np.ndarray] = []
        for index in range(quantile_matrix.shape[1]):
            column = quantile_matrix[:, index]
            finite_indexes = np.where(~np.isnan(column))[0]
            finite_values = column[finite_indexes]
            order = np.argsort(finite_values)
            sorted_columns.append(finite_values[order])
            original_indexes.append(finite_indexes[order])
        max_length = max((column.size for column in sorted_columns), default=0)
        if max_length == 0:
            return quantile_matrix, dict.fromkeys(sample_ids, 1.0)
        rank_matrix = np.full((max_length, len(sample_ids)), np.nan, dtype=float)
        for index, column in enumerate(sorted_columns):
            rank_matrix[: column.size, index] = column
        rank_means = np.nanmean(rank_matrix, axis=1)
        normalized = quantile_matrix.copy()
        for index, ordered_rows in enumerate(original_indexes):
            for rank, row_index in enumerate(ordered_rows):
                normalized[row_index, index] = rank_means[rank]
        return normalized, dict.fromkeys(sample_ids, 1.0)

    if method in (
        NormalizationMethod.LOG2_MEDIAN_CENTERING,
        NormalizationMethod.VSN_LIKE,
    ):
        prepared = _prepare_nonpositive_values_for_log_transform(
            matrix,
            method=method,
        )
        log_matrix = prepared["log_matrix"]
        pseudocount = prepared["pseudocount"]
        if method is NormalizationMethod.VSN_LIKE and pseudocount is None:
            return matrix.copy(), dict.fromkeys(sample_ids, 1.0)
        sample_medians = _nanmedian_by_column(log_matrix)
        finite_medians = sample_medians[np.isfinite(sample_medians)]
        global_median = (
            float(np.nanmedian(finite_medians))
            if finite_medians.size
            else 0.0
        )
        shifts = np.array(
            [
                (
                    global_median - float(sample_medians[index])
                    if math.isfinite(float(sample_medians[index]))
                    else 0.0
                )
                for index in range(sample_medians.size)
            ],
            dtype=float,
        )
        normalized_log = log_matrix.copy()
        for index, shift in enumerate(shifts):
            normalized_log[:, index] = normalized_log[:, index] + shift
        normalized = _restore_log_normalized_values(
            matrix,
            normalized_log,
            pseudocount=pseudocount,
        )
        factors = {
            sample_id: float(np.power(2.0, shifts[index]))
            for index, sample_id in enumerate(sample_ids)
        }
        return normalized, factors

    raise ValueError(f"unsupported normalization method: {method.value}")


def _normalize_intensity_matrix_vectorized(
    matrix: np.ndarray,
    sample_ids: tuple[str, ...],
    *,
    method: NormalizationMethod,
) -> tuple[np.ndarray, dict[str, float]]:
    sample_ids_array = np.array(sample_ids, dtype=object)
    if method is NormalizationMethod.TIC:
        totals = np.nansum(matrix, axis=0)
        positive_totals = totals[totals > 0]
        global_total = float(np.nanmean(positive_totals)) if positive_totals.size else 1.0
        factor_array = np.where(totals > 0, global_total / totals, 1.0)
        scaled = matrix * factor_array[np.newaxis, :]
        return scaled, _normalization_factors_from_array(sample_ids_array, factor_array)

    if method is NormalizationMethod.MEDIAN:
        medians = _nanmedian_by_column(matrix)
        finite_medians = medians[np.isfinite(medians)]
        global_median = float(np.nanmedian(finite_medians)) if finite_medians.size else 1.0
        factor_array = np.where(
            np.isfinite(medians) & (medians > 0.0),
            global_median / medians,
            1.0,
        )
        scaled = matrix * factor_array[np.newaxis, :]
        return scaled, _normalization_factors_from_array(sample_ids_array, factor_array)

    if method is NormalizationMethod.QUANTILE:
        sorted_columns: list[np.ndarray] = []
        ordered_row_indexes: list[np.ndarray] = []
        for column_index in range(matrix.shape[1]):
            column = matrix[:, column_index]
            finite_row_indexes = np.flatnonzero(~np.isnan(column))
            finite_values = column[finite_row_indexes]
            order = np.argsort(finite_values)
            sorted_columns.append(finite_values[order])
            ordered_row_indexes.append(finite_row_indexes[order])
        max_length = max((column.size for column in sorted_columns), default=0)
        if max_length == 0:
            return matrix.copy(), dict.fromkeys(sample_ids, 1.0)
        rank_matrix = np.full((max_length, matrix.shape[1]), np.nan, dtype=float)
        for column_index, ordered_values in enumerate(sorted_columns):
            rank_matrix[: ordered_values.size, column_index] = ordered_values
        rank_means = np.nanmean(rank_matrix, axis=1)
        normalized = matrix.copy()
        for column_index, ordered_rows in enumerate(ordered_row_indexes):
            normalized[ordered_rows, column_index] = rank_means[: ordered_rows.size]
        return normalized, dict.fromkeys(sample_ids, 1.0)

    if method in (
        NormalizationMethod.LOG2_MEDIAN_CENTERING,
        NormalizationMethod.VSN_LIKE,
    ):
        prepared = _prepare_nonpositive_values_for_log_transform(
            matrix,
            method=method,
        )
        log_matrix = prepared["log_matrix"]
        pseudocount = prepared["pseudocount"]
        if method is NormalizationMethod.VSN_LIKE and pseudocount is None:
            return matrix.copy(), dict.fromkeys(sample_ids, 1.0)
        sample_medians = _nanmedian_by_column(log_matrix)
        finite_medians = sample_medians[np.isfinite(sample_medians)]
        global_median = float(np.nanmedian(finite_medians)) if finite_medians.size else 0.0
        shifts = np.where(
            np.isfinite(sample_medians),
            global_median - sample_medians,
            0.0,
        )
        normalized_log = log_matrix + shifts[np.newaxis, :]
        normalized = _restore_log_normalized_values(
            matrix,
            normalized_log,
            pseudocount=pseudocount,
        )
        factor_array = np.power(2.0, shifts)
        return normalized, _normalization_factors_from_array(sample_ids_array, factor_array)

    raise ValueError(f"unsupported normalization method: {method.value}")


def _coefficient_of_variation(values: list[float]) -> float:
    if not values:
        return 0.0
    mean_value = float(np.mean(np.array(values, dtype=float)))
    if mean_value == 0.0:
        return 0.0
    return float(np.std(np.array(values, dtype=float)) / mean_value)


def _tic_composition_penalty(composition_report: CompositionalBiasReport) -> float:
    if composition_report.high_risk_sample_count:
        return 1.0
    if composition_report.caution_sample_count:
        return 0.2
    return 0.0


def _sample_snapshot(
    table: LabelFreeQuantTable,
    sample_id: str,
) -> NormalizationSampleSnapshot:
    abundances = np.array(
        [
            value.abundance
            for value in table.values
            if value.sample_id == sample_id and value.abundance is not None
        ],
        dtype=float,
    )
    if abundances.size == 0:
        return NormalizationSampleSnapshot(
            sample_id=sample_id,
            total_abundance=0.0,
            median_abundance=0.0,
            interquartile_range=0.0,
        )
    return NormalizationSampleSnapshot(
        sample_id=sample_id,
        total_abundance=float(np.sum(abundances)),
        median_abundance=float(np.median(abundances)),
        interquartile_range=float(
            np.percentile(abundances, 75) - np.percentile(abundances, 25)
        ),
    )


def _distribution_snapshot(
    table: LabelFreeQuantTable,
    sample_id: str,
) -> NormalizationDistributionSnapshot:
    abundances = np.array(
        [
            value.abundance
            for value in table.values
            if value.sample_id == sample_id and value.abundance is not None
        ],
        dtype=float,
    )
    if abundances.size == 0:
        return NormalizationDistributionSnapshot(
            sample_id=sample_id,
            observed_count=0,
            zero_count=0,
            negative_count=0,
        )
    return NormalizationDistributionSnapshot(
        sample_id=sample_id,
        observed_count=int(abundances.size),
        zero_count=int(np.sum(abundances == 0.0)),
        negative_count=int(np.sum(abundances < 0.0)),
        min_abundance=float(np.min(abundances)),
        lower_quartile_abundance=float(np.percentile(abundances, 25)),
        median_abundance=float(np.percentile(abundances, 50)),
        upper_quartile_abundance=float(np.percentile(abundances, 75)),
        max_abundance=float(np.max(abundances)),
    )


def _log_transform_preparation(
    table: LabelFreeQuantTable,
    *,
    method: NormalizationMethod,
) -> tuple[NormalizationLogTransformPreparation, ...]:
    if method not in (
        NormalizationMethod.LOG2_MEDIAN_CENTERING,
        NormalizationMethod.VSN_LIKE,
    ):
        return ()

    entries: list[NormalizationLogTransformPreparation] = []
    pseudocount = _minimum_positive_pseudocount(_table_matrix(table)[0])
    for sample_id in table.sample_ids:
        abundances = np.array(
            [
                value.abundance
                for value in table.values
                if value.sample_id == sample_id and value.abundance is not None
            ],
            dtype=float,
        )
        if method is NormalizationMethod.LOG2_MEDIAN_CENTERING:
            handling_strategy = "exclude_nonpositive_values_before_log2_centering"
            effective_pseudocount = None
        else:
            handling_strategy = "floor_nonpositive_values_then_add_pseudocount"
            effective_pseudocount = pseudocount
        entries.append(
            NormalizationLogTransformPreparation(
                sample_id=sample_id,
                zero_count=int(np.sum(abundances == 0.0)),
                negative_count=int(np.sum(abundances < 0.0)),
                positive_count=int(np.sum(abundances > 0.0)),
                handling_strategy=handling_strategy,
                pseudocount=effective_pseudocount,
            )
        )
    return tuple(entries)


def _minimum_positive_pseudocount(matrix: np.ndarray) -> float | None:
    finite_positive = matrix[np.isfinite(matrix) & (matrix > 0.0)]
    if finite_positive.size == 0:
        return None
    return max(float(np.min(finite_positive)) / 2.0, 1e-6)


def _nanmedian_by_column(matrix: np.ndarray) -> np.ndarray:
    medians = np.full(matrix.shape[1], np.nan, dtype=float)
    for column_index in range(matrix.shape[1]):
        column = matrix[:, column_index]
        finite_mask = ~np.isnan(column)
        if np.any(finite_mask):
            medians[column_index] = float(np.nanmedian(column))
    return medians


def _normalization_factors_from_array(
    sample_ids: np.ndarray,
    factor_array: np.ndarray,
) -> dict[str, float]:
    return {
        str(sample_id): float(factor)
        for sample_id, factor in zip(sample_ids, factor_array, strict=True)
    }


def _prepare_nonpositive_values_for_log_transform(
    matrix: np.ndarray,
    *,
    method: NormalizationMethod,
) -> _PreparedLogTransform:
    positive_mask = np.isfinite(matrix) & (matrix > 0.0)
    if method is NormalizationMethod.LOG2_MEDIAN_CENTERING:
        log_matrix = np.full(matrix.shape, np.nan, dtype=float)
        log_matrix[positive_mask] = np.log2(matrix[positive_mask])
        return {
            "log_matrix": log_matrix,
            "pseudocount": None,
        }
    pseudocount = _minimum_positive_pseudocount(matrix)
    if pseudocount is None:
        return {
            "log_matrix": np.full(matrix.shape, np.nan, dtype=float),
            "pseudocount": None,
        }
    clipped = np.where(np.isnan(matrix), np.nan, np.maximum(matrix, 0.0))
    log_matrix = np.where(
        np.isnan(clipped),
        np.nan,
        np.log2(clipped + pseudocount),
    )
    return {
        "log_matrix": log_matrix,
        "pseudocount": pseudocount,
    }


def _restore_log_normalized_values(
    original_matrix: np.ndarray,
    normalized_log_matrix: np.ndarray,
    *,
    pseudocount: float | None = None,
) -> np.ndarray:
    restored = np.full(original_matrix.shape, np.nan, dtype=float)
    finite_mask = np.isfinite(normalized_log_matrix)
    if pseudocount is None:
        restored[finite_mask] = np.power(2.0, normalized_log_matrix[finite_mask])
    else:
        restored[finite_mask] = np.maximum(
            np.power(2.0, normalized_log_matrix[finite_mask]) - pseudocount,
            0.0,
        )
    zero_mask = np.isfinite(original_matrix) & (original_matrix == 0.0)
    negative_mask = np.isfinite(original_matrix) & (original_matrix < 0.0)
    restored[zero_mask] = 0.0
    restored[negative_mask] = 0.0
    return restored
