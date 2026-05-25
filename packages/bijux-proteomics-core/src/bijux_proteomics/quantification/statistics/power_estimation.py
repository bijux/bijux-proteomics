# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned power and sample-size estimation over governed quantification tables."""

from __future__ import annotations

import csv
from io import StringIO
import math
from pathlib import Path

import numpy as np
from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics.domain.records import QuantMatrix as CanonicalQuantMatrix
from bijux_proteomics.io.stable_outputs import sort_rows_by_fields
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import (
    LabelFreeQuantTable,
    QuantEntityLevel,
    QuantMeasureKind,
    QuantRollupMethod,
    _condition_lookup,
    _matrix_value_index,
    coerce_label_free_quant_table,
)
from bijux_proteomics_foundation import JsonModel


class PowerEstimationPolicy(JsonModel):
    """Policy for detectable-effect estimation from pilot quantification data."""

    model_config = ConfigDict(extra="forbid")

    fdr_target: float = Field(default=0.05, gt=0.0, le=0.25)
    target_power: float = Field(default=0.8, gt=0.5, lt=0.999)
    candidate_replicates_per_condition: tuple[int, ...] = Field(
        default=(2, 3, 4, 5, 6)
    )
    minimum_condition_replicates_for_variance: int = Field(default=2, ge=2)

    @field_validator("candidate_replicates_per_condition", mode="before")
    @classmethod
    def _normalize_candidate_replicates(cls, value: object) -> tuple[int, ...]:
        if value in (None, ()):
            return (2, 3, 4, 5, 6)
        normalized = tuple(
            sorted(
                {
                    int(candidate)
                    for candidate in value  # type: ignore[arg-type]
                    if int(candidate) >= 1
                }
            )
        )
        if not normalized:
            raise ValueError("at least one replicate count is required")
        return normalized


class PowerVarianceEntry(JsonModel):
    """One entity-level pilot variance estimate."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    observed_sample_count: int = Field(..., ge=0)
    missing_sample_count: int = Field(..., ge=0)
    missing_fraction: float = Field(..., ge=0.0, le=1.0)
    contributing_condition_count: int = Field(..., ge=0)
    used_global_variance_fallback: bool = False
    pooled_log2_variance: float = Field(..., ge=0.0)
    pooled_log2_stddev: float = Field(..., ge=0.0)


class PowerEffectSizeGridEntry(JsonModel):
    """One replicate-count row in the detectable-effect grid."""

    model_config = ConfigDict(extra="forbid")

    replicates_per_condition: int = Field(..., ge=1)
    evaluable_entity_count: int = Field(..., ge=0)
    median_effective_replicates_per_condition: float = Field(..., ge=0.0)
    median_detectable_log2_fold_change: float = Field(..., ge=0.0)
    p75_detectable_log2_fold_change: float = Field(..., ge=0.0)


class PowerEstimationSummary(JsonModel):
    """Compact summary over one power-estimation run."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    measure_kind: QuantMeasureKind
    aggregation_method: QuantRollupMethod
    normalization_method: str = Field(..., min_length=1)
    sample_count: int = Field(..., ge=0)
    evaluated_entity_count: int = Field(..., ge=0)
    fdr_target: float = Field(..., gt=0.0, le=0.25)
    target_power: float = Field(..., gt=0.5, lt=0.999)
    weaker_power_with_fewer_replicates: bool


class PowerEstimationReport(JsonModel):
    """Owned power and sample-size estimation surface."""

    model_config = ConfigDict(extra="forbid")

    summary: PowerEstimationSummary
    policy: PowerEstimationPolicy
    variance_entries: tuple[PowerVarianceEntry, ...] = Field(default_factory=tuple)
    effect_size_grid: tuple[PowerEffectSizeGridEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


def build_power_estimation_report(
    table: LabelFreeQuantTable | CanonicalQuantMatrix,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    policy: PowerEstimationPolicy | None = None,
) -> PowerEstimationReport:
    """Estimate detectable log2 fold-change across candidate replicate counts."""

    table = coerce_label_free_quant_table(table)
    active_policy = policy or PowerEstimationPolicy()
    value_lookup = _matrix_value_index(table)
    condition_by_sample = _condition_lookup(design_entries)
    variance_entries: list[PowerVarianceEntry] = []
    for entity_id in table.entity_ids:
        observed_values_by_condition: dict[str, list[float]] = {}
        all_observed_values: list[float] = []
        missing_sample_count = 0
        for sample_id in table.sample_ids:
            abundance = value_lookup[(entity_id, sample_id)].abundance
            if abundance is None:
                missing_sample_count += 1
                continue
            log2_value = math.log2(float(abundance) + 1.0)
            all_observed_values.append(log2_value)
            condition = condition_by_sample.get(sample_id, "__study__")
            observed_values_by_condition.setdefault(condition, []).append(log2_value)
        observed_sample_count = len(all_observed_values)
        if observed_sample_count < 2:
            continue
        pooled_variance, contributing_condition_count, used_fallback = _pooled_variance(
            observed_values_by_condition=observed_values_by_condition,
            all_observed_values=tuple(all_observed_values),
            minimum_condition_replicates_for_variance=(
                active_policy.minimum_condition_replicates_for_variance
            ),
        )
        missing_fraction = (
            missing_sample_count / len(table.sample_ids) if table.sample_ids else 0.0
        )
        variance_entries.append(
            PowerVarianceEntry(
                entity_id=entity_id,
                protein_refs=table.entity_protein_refs.get(entity_id, ()),
                observed_sample_count=observed_sample_count,
                missing_sample_count=missing_sample_count,
                missing_fraction=missing_fraction,
                contributing_condition_count=contributing_condition_count,
                used_global_variance_fallback=used_fallback,
                pooled_log2_variance=pooled_variance,
                pooled_log2_stddev=math.sqrt(pooled_variance),
            )
        )

    variance_entries = sorted(variance_entries, key=lambda entry: entry.entity_id)
    effect_size_grid: list[PowerEffectSizeGridEntry] = []
    for replicates_per_condition in active_policy.candidate_replicates_per_condition:
        detectable_effects: list[float] = []
        effective_replicates: list[float] = []
        for entry in variance_entries:
            effective_replicate_count = replicates_per_condition * max(
                0.0,
                1.0 - entry.missing_fraction,
            )
            if effective_replicate_count <= 0.0:
                continue
            detectable_effects.append(
                _detectable_log2_fold_change(
                    pooled_log2_stddev=entry.pooled_log2_stddev,
                    effective_replicates_per_condition=effective_replicate_count,
                    fdr_target=active_policy.fdr_target,
                    target_power=active_policy.target_power,
                )
            )
            effective_replicates.append(effective_replicate_count)
        if not detectable_effects:
            continue
        effect_size_grid.append(
            PowerEffectSizeGridEntry(
                replicates_per_condition=replicates_per_condition,
                evaluable_entity_count=len(detectable_effects),
                median_effective_replicates_per_condition=float(
                    np.median(np.array(effective_replicates, dtype=float))
                ),
                median_detectable_log2_fold_change=float(
                    np.median(np.array(detectable_effects, dtype=float))
                ),
                p75_detectable_log2_fold_change=float(
                    np.quantile(np.array(detectable_effects, dtype=float), 0.75)
                ),
            )
        )
    weaker_power = all(
        left.median_detectable_log2_fold_change >= right.median_detectable_log2_fold_change
        for left, right in zip(effect_size_grid, effect_size_grid[1:], strict=False)
    )
    return PowerEstimationReport(
        summary=PowerEstimationSummary(
            entity_level=table.entity_level,
            measure_kind=table.measure_kind,
            aggregation_method=table.aggregation_method,
            normalization_method=table.normalization_method.value,
            sample_count=len(table.sample_ids),
            evaluated_entity_count=len(variance_entries),
            fdr_target=active_policy.fdr_target,
            target_power=active_policy.target_power,
            weaker_power_with_fewer_replicates=weaker_power,
        ),
        policy=active_policy,
        variance_entries=tuple(variance_entries),
        effect_size_grid=tuple(effect_size_grid),
        note=(
            "power estimation links pilot log2 variance, missingness burden, replicate count, and fdr target to one detectable-effect grid"
        ),
    )


def render_power_estimation_summary_tsv(report: PowerEstimationReport) -> str:
    """Render one compact power-estimation summary as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "entity_level",
            "measure_kind",
            "aggregation_method",
            "normalization_method",
            "sample_count",
            "evaluated_entity_count",
            "fdr_target",
            "target_power",
            "weaker_power_with_fewer_replicates",
        )
    )
    writer.writerow(
        (
            report.summary.entity_level.value,
            report.summary.measure_kind.value,
            report.summary.aggregation_method.value,
            report.summary.normalization_method,
            report.summary.sample_count,
            report.summary.evaluated_entity_count,
            f"{report.summary.fdr_target:g}",
            f"{report.summary.target_power:g}",
            str(report.summary.weaker_power_with_fewer_replicates).lower(),
        )
    )
    return handle.getvalue()


def render_power_variance_tsv(report: PowerEstimationReport) -> str:
    """Render the entity-level pilot variance table as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "entity_id",
            "protein_refs",
            "observed_sample_count",
            "missing_sample_count",
            "missing_fraction",
            "contributing_condition_count",
            "used_global_variance_fallback",
            "pooled_log2_variance",
            "pooled_log2_stddev",
        )
    )
    for entry in sort_rows_by_fields(report.variance_entries, "entity_id"):
        writer.writerow(
            (
                entry.entity_id,
                ";".join(entry.protein_refs),
                entry.observed_sample_count,
                entry.missing_sample_count,
                f"{entry.missing_fraction:g}",
                entry.contributing_condition_count,
                str(entry.used_global_variance_fallback).lower(),
                f"{entry.pooled_log2_variance:g}",
                f"{entry.pooled_log2_stddev:g}",
            )
        )
    return handle.getvalue()


def render_power_effect_size_grid_tsv(report: PowerEstimationReport) -> str:
    """Render the detectable-effect grid as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "replicates_per_condition",
            "evaluable_entity_count",
            "median_effective_replicates_per_condition",
            "median_detectable_log2_fold_change",
            "p75_detectable_log2_fold_change",
        )
    )
    for entry in sort_rows_by_fields(report.effect_size_grid, "replicates_per_condition"):
        writer.writerow(
            (
                entry.replicates_per_condition,
                entry.evaluable_entity_count,
                f"{entry.median_effective_replicates_per_condition:g}",
                f"{entry.median_detectable_log2_fold_change:g}",
                f"{entry.p75_detectable_log2_fold_change:g}",
            )
        )
    return handle.getvalue()


def export_power_estimation_summary_tsv(report: PowerEstimationReport, path: Path) -> None:
    """Write one power-estimation summary TSV artifact."""

    path.write_text(render_power_estimation_summary_tsv(report), encoding="utf-8")


def export_power_variance_tsv(report: PowerEstimationReport, path: Path) -> None:
    """Write one variance-table TSV artifact."""

    path.write_text(render_power_variance_tsv(report), encoding="utf-8")


def export_power_effect_size_grid_tsv(
    report: PowerEstimationReport,
    path: Path,
) -> None:
    """Write one detectable-effect grid TSV artifact."""

    path.write_text(render_power_effect_size_grid_tsv(report), encoding="utf-8")


def _pooled_variance(
    *,
    observed_values_by_condition: dict[str, list[float]],
    all_observed_values: tuple[float, ...],
    minimum_condition_replicates_for_variance: int,
) -> tuple[float, int, bool]:
    weighted_variance_sum = 0.0
    total_degrees_of_freedom = 0
    contributing_condition_count = 0
    for values in observed_values_by_condition.values():
        if len(values) < minimum_condition_replicates_for_variance:
            continue
        variance = float(np.var(np.array(values, dtype=float), ddof=1))
        degrees_of_freedom = len(values) - 1
        weighted_variance_sum += variance * degrees_of_freedom
        total_degrees_of_freedom += degrees_of_freedom
        contributing_condition_count += 1
    if total_degrees_of_freedom > 0:
        return (
            weighted_variance_sum / total_degrees_of_freedom,
            contributing_condition_count,
            False,
        )
    fallback_variance = float(np.var(np.array(all_observed_values, dtype=float), ddof=1))
    return fallback_variance, 0, True


def _detectable_log2_fold_change(
    *,
    pooled_log2_stddev: float,
    effective_replicates_per_condition: float,
    fdr_target: float,
    target_power: float,
) -> float:
    if pooled_log2_stddev <= 0.0:
        return 0.0
    if effective_replicates_per_condition <= 0.0:
        return float("inf")
    z_alpha = _inverse_standard_normal_cdf(1.0 - (fdr_target / 2.0))
    z_beta = _inverse_standard_normal_cdf(target_power)
    return (z_alpha + z_beta) * pooled_log2_stddev * math.sqrt(
        2.0 / effective_replicates_per_condition
    )


def _inverse_standard_normal_cdf(probability: float) -> float:
    """Approximate the inverse standard normal CDF with Acklam's method."""

    if not 0.0 < probability < 1.0:
        raise ValueError("probability must lie strictly between zero and one")
    a = (
        -3.969683028665376e01,
        2.209460984245205e02,
        -2.759285104469687e02,
        1.383577518672690e02,
        -3.066479806614716e01,
        2.506628277459239e00,
    )
    b = (
        -5.447609879822406e01,
        1.615858368580409e02,
        -1.556989798598866e02,
        6.680131188771972e01,
        -1.328068155288572e01,
    )
    c = (
        -7.784894002430293e-03,
        -3.223964580411365e-01,
        -2.400758277161838e00,
        -2.549732539343734e00,
        4.374664141464968e00,
        2.938163982698783e00,
    )
    d = (
        7.784695709041462e-03,
        3.224671290700398e-01,
        2.445134137142996e00,
        3.754408661907416e00,
    )
    lower_tail = 0.02425
    upper_tail = 1.0 - lower_tail
    if probability < lower_tail:
        q = math.sqrt(-2.0 * math.log(probability))
        return (
            (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5])
            / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
        )
    if probability > upper_tail:
        q = math.sqrt(-2.0 * math.log(1.0 - probability))
        return -(
            (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5])
            / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
        )
    q = probability - 0.5
    r = q * q
    return (
        (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q
    ) / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1.0)


__all__ = [
    "PowerEffectSizeGridEntry",
    "PowerEstimationPolicy",
    "PowerEstimationReport",
    "PowerEstimationSummary",
    "PowerVarianceEntry",
    "build_power_estimation_report",
    "export_power_effect_size_grid_tsv",
    "export_power_estimation_summary_tsv",
    "export_power_variance_tsv",
    "render_power_effect_size_grid_tsv",
    "render_power_estimation_summary_tsv",
    "render_power_variance_tsv",
]
