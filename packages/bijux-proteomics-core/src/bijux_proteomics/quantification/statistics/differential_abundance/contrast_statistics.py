# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Contrast-specific statistical engines for differential abundance."""

from __future__ import annotations

from collections.abc import Mapping
import math

import numpy as np

from bijux_proteomics.quantification.contracts.design import (
    QuantDesignContrast,
    QuantDesignMatrixReport,
)
from bijux_proteomics.quantification.contracts.differential import (
    _student_t_two_sided_p_value,
)
from bijux_proteomics.quantification.contracts.matrix_building import (
    _matrix_value_index,
)
from bijux_proteomics.quantification.contracts.matrix_models import (
    LabelFreeQuantTable,
    QuantValue,
)
from bijux_proteomics.quantification.statistics.differential_abundance.weighting import (
    combine_notes,
    effective_weighted_sample_size,
    weighted_observation_note,
    weighted_or_unweighted_mean,
    weighted_sample_standard_deviation,
)


def linear_model_contrast_statistics(
    table: LabelFreeQuantTable,
    entity_id: str,
    *,
    design_matrix: QuantDesignMatrixReport,
    contrast: QuantDesignContrast,
    sample_weights: dict[str, float] | None = None,
    exclusion_weight_threshold: float = 0.0,
) -> tuple[float, float, float | None, float | None, float | None, str | None]:
    """Estimate one design-matrix contrast from observed entity values."""

    if not contrast.coefficient_vector:
        return (
            0.0,
            1.0,
            None,
            None,
            None,
            "linear-model contrast requires an explicit coefficient vector",
        )
    full_matrix = np.array(
        [row.column_values for row in design_matrix.rows],
        dtype=float,
    )
    contrast_vector = -np.array(contrast.coefficient_vector, dtype=float)
    lookup = _matrix_value_index(table)
    observed_rows: list[np.ndarray] = []
    observed_values: list[float] = []
    observed_weights: list[float] = []
    for row_index, row in enumerate(design_matrix.rows):
        cell = lookup.get((entity_id, row.sample_id))
        if cell is None or cell.abundance is None:
            continue
        weight = (
            1.0
            if sample_weights is None
            else float(sample_weights.get(row.sample_id, 1.0))
        )
        if weight <= exclusion_weight_threshold:
            continue
        observed_rows.append(full_matrix[row_index])
        observed_values.append(math.log2(cell.abundance + 1.0))
        observed_weights.append(weight)
    if len(observed_values) < 2:
        return (
            0.0,
            1.0,
            None,
            None,
            None,
            "linear-model contrast requires at least two observed samples",
        )
    x_matrix = np.vstack(observed_rows)
    y_vector = np.array(observed_values, dtype=float)
    weight_vector = np.array(observed_weights, dtype=float)
    sqrt_weight_vector = np.sqrt(weight_vector)
    weighted_x = x_matrix * sqrt_weight_vector[:, np.newaxis]
    weighted_y = y_vector * sqrt_weight_vector
    coefficients, _, _, _ = np.linalg.lstsq(weighted_x, weighted_y, rcond=None)
    fitted = x_matrix @ coefficients
    residuals = y_vector - fitted
    rank = int(np.linalg.matrix_rank(x_matrix))
    residual_df = len(observed_values) - rank
    estimate = float(np.dot(contrast_vector, coefficients))
    if residual_df <= 0:
        return (
            estimate,
            1.0,
            None,
            None,
            None,
            "linear-model contrast requires positive residual degrees of freedom",
        )
    rss = float(np.dot(weight_vector, residuals * residuals))
    sigma_squared = rss / float(residual_df)
    xtx_inverse = np.linalg.pinv(x_matrix.T @ np.diag(weight_vector) @ x_matrix)
    contrast_variance = float(
        sigma_squared * (contrast_vector @ xtx_inverse @ contrast_vector)
    )
    if contrast_variance <= 0.0 or not math.isfinite(contrast_variance):
        return (
            estimate,
            1.0,
            None,
            None,
            None,
            "linear-model contrast variance could not be estimated robustly",
        )
    standard_error = math.sqrt(contrast_variance)
    if standard_error == 0.0 or not math.isfinite(standard_error):
        return (
            estimate,
            1.0,
            None,
            None,
            None,
            "linear-model contrast standard error collapsed to zero",
        )
    t_statistic = estimate / standard_error
    p_value = _student_t_two_sided_p_value(abs(t_statistic), float(residual_df))
    interval_radius = 1.96 * standard_error
    note = None
    if standard_error > 1.0:
        note = "uncertainty remains wide relative to the modeled contrast estimate"
    if sample_weights is not None:
        note = combine_notes(
            note,
            weighted_observation_note(
                weight_vector,
                np.array((), dtype=float),
                exclusion_weight_threshold=exclusion_weight_threshold,
            ),
        )
    return (
        estimate,
        p_value,
        standard_error,
        estimate - interval_radius,
        estimate + interval_radius,
        note,
    )


def paired_t_test_statistics(
    lookup: Mapping[tuple[str, str], QuantValue],
    entity_id: str,
    *,
    complete_design_pairs: tuple[tuple[str, str, str], ...],
    sample_weights: dict[str, float] | None = None,
    exclusion_weight_threshold: float = 0.0,
) -> tuple[
    float,
    float,
    float,
    float,
    float | None,
    float | None,
    float | None,
    float | None,
    int,
    str | None,
]:
    """Estimate one paired contrast from complete observed design pairs."""

    paired_a: list[float] = []
    paired_b: list[float] = []
    pair_weights: list[float] = []
    for _, sample_id_a, sample_id_b in complete_design_pairs:
        cell_a = lookup.get((entity_id, sample_id_a))
        cell_b = lookup.get((entity_id, sample_id_b))
        if (
            cell_a is None
            or cell_b is None
            or cell_a.abundance is None
            or cell_b.abundance is None
        ):
            continue
        pair_weight = min(
            1.0
            if sample_weights is None
            else float(sample_weights.get(sample_id_a, 1.0)),
            1.0
            if sample_weights is None
            else float(sample_weights.get(sample_id_b, 1.0)),
        )
        if pair_weight <= exclusion_weight_threshold:
            continue
        paired_a.append(math.log2(cell_a.abundance + 1.0))
        paired_b.append(math.log2(cell_b.abundance + 1.0))
        pair_weights.append(pair_weight)
    if not paired_a:
        return (
            0.0,
            0.0,
            0.0,
            1.0,
            None,
            None,
            None,
            None,
            0,
            "paired test could not use any complete observed pairs for this entity",
        )
    values_a = np.array(paired_a, dtype=float)
    values_b = np.array(paired_b, dtype=float)
    weights = np.array(pair_weights, dtype=float)
    differences = values_b - values_a
    complete_pair_count = int(differences.size)
    mean_a = weighted_or_unweighted_mean(values_a, weights)
    mean_b = weighted_or_unweighted_mean(values_b, weights)
    estimate = weighted_or_unweighted_mean(differences, weights)
    effective_pairs = effective_weighted_sample_size(weights)
    if complete_pair_count < 2:
        return (
            mean_a,
            mean_b,
            estimate,
            1.0,
            None,
            None,
            None,
            None,
            complete_pair_count,
            "paired test requires at least two positive-weight complete observed pairs per entity",
        )
    sample_std = weighted_sample_standard_deviation(differences, weights)
    if sample_std is None:
        return (
            mean_a,
            mean_b,
            estimate,
            1.0,
            None,
            None,
            None,
            None,
            complete_pair_count,
            "paired test could not estimate weighted within-pair variance robustly",
        )
    if sample_std == 0.0 or not math.isfinite(sample_std):
        collapsed_note = (
            "within-pair differences collapsed to one value so paired uncertainty "
            "could not be estimated robustly"
        )
        return (
            mean_a,
            mean_b,
            estimate,
            1.0 if estimate == 0.0 else 0.0,
            0.0,
            estimate,
            estimate,
            None,
            complete_pair_count,
            collapsed_note,
        )
    standard_error = sample_std / math.sqrt(effective_pairs)
    t_statistic = estimate / standard_error
    p_value = _student_t_two_sided_p_value(
        abs(t_statistic),
        float(max(effective_pairs - 1.0, 1.0)),
    )
    interval_radius = 1.96 * standard_error
    effect_size = estimate / sample_std
    note: str | None = None
    if complete_pair_count < len(complete_design_pairs):
        note = (
            f"paired test used {complete_pair_count} complete observed pairs out of "
            f"{len(complete_design_pairs)} complete design pairs"
        )
    elif standard_error > 1.0:
        note = "within-pair uncertainty remains wide relative to the estimated effect"
    if sample_weights is not None:
        note = combine_notes(
            note,
            weighted_observation_note(
                weights,
                np.array((), dtype=float),
                exclusion_weight_threshold=exclusion_weight_threshold,
            ),
        )
    return (
        mean_a,
        mean_b,
        estimate,
        p_value,
        standard_error,
        estimate - interval_radius,
        estimate + interval_radius,
        effect_size,
        complete_pair_count,
        note,
    )


__all__ = [
    "linear_model_contrast_statistics",
    "paired_t_test_statistics",
]
