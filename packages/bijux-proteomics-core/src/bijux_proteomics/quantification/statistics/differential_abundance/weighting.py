# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Reliability weighting and uncertainty math for differential abundance."""

from __future__ import annotations

import math
from typing import Protocol

import numpy as np

from bijux_proteomics.quantification.contracts.study_qc import (
    SampleReliabilityWeightReport,
)


class StudentTPValue(Protocol):
    """One callable that converts |t| and degrees of freedom into a p-value."""

    def __call__(self, t_statistic: float, degrees_of_freedom: float, /) -> float: ...


def sample_weight_lookup(
    report: SampleReliabilityWeightReport | None,
) -> dict[str, float] | None:
    """Return reliability weights keyed by sample id when weighting is active."""

    if report is None:
        return None
    return {
        entry.sample_id: float(entry.reliability_weight) for entry in report.entries
    }


def weighted_or_unweighted_mean(values: np.ndarray, weights: np.ndarray) -> float:
    """Return the weighted mean when informative weights are present."""

    if values.size == 0:
        return 0.0
    if weights.size != values.size or np.allclose(weights, 1.0):
        return float(np.mean(values))
    weight_sum = float(np.sum(weights))
    if weight_sum <= 0.0:
        return 0.0
    return float(np.sum(values * weights) / weight_sum)


def effective_weighted_sample_size(weights: np.ndarray) -> float:
    """Return the Kish effective sample size for one weight vector."""

    if weights.size == 0:
        return 0.0
    weight_sum = float(np.sum(weights))
    weight_square_sum = float(np.sum(weights * weights))
    if weight_sum <= 0.0 or weight_square_sum <= 0.0:
        return 0.0
    return (weight_sum * weight_sum) / weight_square_sum


def weighted_sample_variance(values: np.ndarray, weights: np.ndarray) -> float | None:
    """Return the unbiased weighted sample variance when estimable."""

    if values.size < 2 or weights.size != values.size:
        return None
    weight_sum = float(np.sum(weights))
    weight_square_sum = float(np.sum(weights * weights))
    denominator = (
        weight_sum - (weight_square_sum / weight_sum) if weight_sum > 0 else 0.0
    )
    if denominator <= 0.0:
        return None
    mean_value = weighted_or_unweighted_mean(values, weights)
    centered = values - mean_value
    return float(np.sum(weights * centered * centered) / denominator)


def weighted_sample_standard_deviation(
    values: np.ndarray,
    weights: np.ndarray,
) -> float | None:
    """Return the weighted sample standard deviation when estimable."""

    variance = weighted_sample_variance(values, weights)
    if variance is None or variance < 0.0 or not math.isfinite(variance):
        return None
    return math.sqrt(variance)


def weighted_effect_size_and_uncertainty(
    values_a: np.ndarray,
    weights_a: np.ndarray,
    values_b: np.ndarray,
    weights_b: np.ndarray,
    log2_fold_change: float,
) -> tuple[float | None, float | None, float | None, float | None, str | None]:
    """Estimate weighted uncertainty and effect size for one contrast."""

    variance_a = weighted_sample_variance(values_a, weights_a)
    variance_b = weighted_sample_variance(values_b, weights_b)
    if (
        values_a.size < 2
        or values_b.size < 2
        or variance_a is None
        or variance_b is None
    ):
        return (
            None,
            None,
            None,
            None,
            "confidence intervals and effect sizes require at least two positive-weight observations per condition after reliability weighting",
        )
    effective_a = effective_weighted_sample_size(weights_a)
    effective_b = effective_weighted_sample_size(weights_b)
    standard_error = math.sqrt(variance_a / effective_a + variance_b / effective_b)
    interval_radius = 1.96 * standard_error
    pooled_variance_numerator = (
        max(effective_a - 1.0, 0.0) * variance_a
        + max(effective_b - 1.0, 0.0) * variance_b
    )
    pooled_variance_denominator = effective_a + effective_b - 2.0
    pooled_sd = (
        math.sqrt(pooled_variance_numerator / pooled_variance_denominator)
        if pooled_variance_denominator > 0.0
        else None
    )
    cohens_d = (
        log2_fold_change / pooled_sd
        if pooled_sd is not None and pooled_sd > 0.0
        else None
    )
    note = None
    if standard_error > 1.0:
        note = "uncertainty remains wide relative to the estimated fold change"
    return (
        standard_error,
        log2_fold_change - interval_radius,
        log2_fold_change + interval_radius,
        cohens_d,
        note,
    )


def weighted_welch_statistics(
    values_a: np.ndarray,
    weights_a: np.ndarray,
    values_b: np.ndarray,
    weights_b: np.ndarray,
    *,
    exclusion_weight_threshold: float,
    student_t_two_sided_p_value: StudentTPValue,
) -> tuple[
    float, float, float | None, float | None, float | None, float | None, str | None
]:
    """Return weighted Welch statistics for one entity-level contrast."""

    mean_a = weighted_or_unweighted_mean(values_a, weights_a)
    mean_b = weighted_or_unweighted_mean(values_b, weights_b)
    estimate = mean_b - mean_a
    variance_a = weighted_sample_variance(values_a, weights_a)
    variance_b = weighted_sample_variance(values_b, weights_b)
    if (
        values_a.size < 2
        or values_b.size < 2
        or variance_a is None
        or variance_b is None
    ):
        note = combine_notes(
            "weighted differential testing requires at least two positive-weight observations per condition after reliability weighting",
            weighted_observation_note(
                weights_a,
                weights_b,
                exclusion_weight_threshold=exclusion_weight_threshold,
            ),
        )
        return estimate, 1.0, None, None, None, None, note
    effective_a = effective_weighted_sample_size(weights_a)
    effective_b = effective_weighted_sample_size(weights_b)
    if variance_a == 0.0 and variance_b == 0.0:
        return (
            estimate,
            1.0,
            0.0,
            estimate,
            estimate,
            None,
            weighted_observation_note(
                weights_a,
                weights_b,
                exclusion_weight_threshold=exclusion_weight_threshold,
            ),
        )
    standard_error = math.sqrt(variance_a / effective_a + variance_b / effective_b)
    if standard_error == 0.0 or not math.isfinite(standard_error):
        return (
            estimate,
            1.0,
            None,
            None,
            None,
            None,
            combine_notes(
                "weighted differential uncertainty collapsed to zero",
                weighted_observation_note(
                    weights_a,
                    weights_b,
                    exclusion_weight_threshold=exclusion_weight_threshold,
                ),
            ),
        )
    t_statistic = estimate / standard_error
    numerator = (variance_a / effective_a + variance_b / effective_b) ** 2
    denominator_df = ((variance_a / effective_a) ** 2) / max(effective_a - 1.0, 1.0) + (
        (variance_b / effective_b) ** 2
    ) / max(effective_b - 1.0, 1.0)
    degrees_of_freedom = numerator / denominator_df if denominator_df > 0.0 else 0.0
    p_value = student_t_two_sided_p_value(abs(t_statistic), degrees_of_freedom)
    (
        _standard_error,
        confidence_interval_low,
        confidence_interval_high,
        effect_size_cohens_d,
        effect_note,
    ) = weighted_effect_size_and_uncertainty(
        values_a,
        weights_a,
        values_b,
        weights_b,
        estimate,
    )
    note = combine_notes(
        effect_note,
        weighted_observation_note(
            weights_a,
            weights_b,
            exclusion_weight_threshold=exclusion_weight_threshold,
        ),
    )
    return (
        estimate,
        p_value,
        standard_error,
        confidence_interval_low,
        confidence_interval_high,
        effect_size_cohens_d,
        note,
    )


def weighted_observation_note(
    weights_a: np.ndarray,
    weights_b: np.ndarray,
    *,
    exclusion_weight_threshold: float,
) -> str | None:
    """Describe excluded or downweighted observations for one comparison."""

    all_weights = np.concatenate((weights_a, weights_b))
    if all_weights.size == 0:
        return None
    excluded_count = int(np.sum(all_weights <= exclusion_weight_threshold))
    downweighted_count = int(
        np.sum((all_weights > exclusion_weight_threshold) & (all_weights < 1.0))
    )
    if excluded_count == 0 and downweighted_count == 0:
        return None
    if excluded_count > 0 and downweighted_count > 0:
        return (
            "reliability weighting excluded "
            f"{excluded_count} observed sample(s) and downweighted {downweighted_count} additional observed sample(s)"
        )
    if excluded_count > 0:
        return f"reliability weighting excluded {excluded_count} observed sample(s)"
    return f"reliability weighting downweighted {downweighted_count} observed sample(s)"


def combine_notes(*notes: str | None) -> str | None:
    """Combine unique explanatory notes into one stable summary string."""

    unique_notes: list[str] = []
    for note in notes:
        if note is None or note == "" or note in unique_notes:
            continue
        unique_notes.append(note)
    ordered_notes = tuple(unique_notes)
    if not ordered_notes:
        return None
    return "; ".join(ordered_notes)


__all__ = [
    "combine_notes",
    "effective_weighted_sample_size",
    "sample_weight_lookup",
    "weighted_effect_size_and_uncertainty",
    "weighted_observation_note",
    "weighted_or_unweighted_mean",
    "weighted_sample_standard_deviation",
    "weighted_sample_variance",
    "weighted_welch_statistics",
]
