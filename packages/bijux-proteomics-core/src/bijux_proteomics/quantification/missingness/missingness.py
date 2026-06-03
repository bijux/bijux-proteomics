# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned missingness analysis for quantitative proteomics tables."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
import math

import numpy as np
from pydantic import ConfigDict, Field

from bijux_proteomics.domain.records import QuantMatrix as CanonicalQuantMatrix
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import (
    LabelFreeQuantTable,
    MissingDataMechanism,
    MissingDataMechanismEntry,
    MissingDataMechanismReport,
    MissingnessClassifierReport,
    MissingnessConditionSummaryEntry,
    MissingnessConditionSummaryReport,
    MissingnessEntitySummaryEntry,
    MissingnessEntitySummaryReport,
    MissingnessIntensityBinEntry,
    MissingnessIntensityDependenceReport,
    MissingnessIntensityPoint,
    MissingValueCorrectionPolicy,
    MissingValueKind,
    MissingValueSummaryEntry,
    MissingValueSummaryPolicy,
    MissingValueSummaryReport,
    _condition_lookup,
    _matrix_value_index,
    coerce_label_free_quant_table,
)
from bijux_proteomics.quantification.matrix import (
    build_dense_label_free_quant_table_view,
    missing_value_kind_to_code,
)
from bijux_proteomics_foundation import JsonModel


class MissingnessLabel(StrEnum):
    """Owned entity-level missingness labels for downstream statistical handling."""

    RANDOM = "random"
    INTENSITY_CENSORED = "intensity_censored"
    CONDITION_SPECIFIC = "condition_specific"
    SAMPLE_FAILURE = "sample_failure"
    STRUCTURAL_ABSENCE = "structural_absence"


_MISSING_VALUE_KINDS = (
    MissingValueKind.OBSERVED,
    MissingValueKind.ZERO,
    MissingValueKind.NOT_OBSERVED,
    MissingValueKind.FILTERED,
    MissingValueKind.IMPUTED,
    MissingValueKind.CENSORED,
    MissingValueKind.EXCLUDED,
    MissingValueKind.NOT_APPLICABLE,
)
_OBSERVED_VALUE_CODES = np.array(
    [
        missing_value_kind_to_code(MissingValueKind.OBSERVED),
        missing_value_kind_to_code(MissingValueKind.ZERO),
        missing_value_kind_to_code(MissingValueKind.IMPUTED),
    ],
    dtype=np.int8,
)
_MISSING_BURDEN_CODES = np.array(
    [
        missing_value_kind_to_code(MissingValueKind.NOT_OBSERVED),
        missing_value_kind_to_code(MissingValueKind.FILTERED),
        missing_value_kind_to_code(MissingValueKind.CENSORED),
        missing_value_kind_to_code(MissingValueKind.EXCLUDED),
    ],
    dtype=np.int8,
)


def _empty_missing_value_counts() -> dict[MissingValueKind, int]:
    return dict.fromkeys(_MISSING_VALUE_KINDS, 0)


def _is_missing_burden(kind: MissingValueKind) -> bool:
    return kind in {
        MissingValueKind.NOT_OBSERVED,
        MissingValueKind.FILTERED,
        MissingValueKind.CENSORED,
        MissingValueKind.EXCLUDED,
    }


class MissingnessClassificationEntry(JsonModel):
    """One entity-level missingness classification row."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    label: MissingnessLabel
    observed_sample_count: int = Field(..., ge=0)
    missing_sample_count: int = Field(..., ge=0)
    missing_fraction: float = Field(..., ge=0.0, le=1.0)
    mean_log2_observed_abundance: float | None = None
    note: str = Field(..., min_length=1)


class MissingnessClassificationReport(JsonModel):
    """Five-label missingness classification over one quantitative matrix."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[MissingnessClassificationEntry, ...] = Field(default_factory=tuple)
    failed_sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


def build_missingness_entity_summary_report(
    table: LabelFreeQuantTable,
    *,
    policy: MissingValueSummaryPolicy | None = None,
) -> MissingnessEntitySummaryReport:
    return _build_missingness_entity_summary_report_vectorized(table, policy=policy)


def _build_missingness_entity_summary_report_pure(
    table: LabelFreeQuantTable,
    *,
    policy: MissingValueSummaryPolicy | None = None,
) -> MissingnessEntitySummaryReport:
    """Summarize missingness per quantified entity across all samples."""
    active_policy = policy or MissingValueSummaryPolicy()
    lookup = _matrix_value_index(table)
    entries: list[MissingnessEntitySummaryEntry] = []
    for entity_id in table.entity_ids:
        counts = _empty_missing_value_counts()
        for sample_id in table.sample_ids:
            kind = _apply_missing_value_summary_policy(
                lookup[(entity_id, sample_id)].missing_value_kind,
                policy=active_policy,
            )
            counts[kind] += 1
        missing_count = sum(
            count for kind, count in counts.items() if _is_missing_burden(kind)
        )
        entries.append(
            MissingnessEntitySummaryEntry(
                entity_id=entity_id,
                observed_sample_count=counts[MissingValueKind.OBSERVED],
                zero_sample_count=counts[MissingValueKind.ZERO],
                not_observed_sample_count=counts[MissingValueKind.NOT_OBSERVED],
                filtered_sample_count=counts[MissingValueKind.FILTERED],
                imputed_sample_count=counts[MissingValueKind.IMPUTED],
                censored_sample_count=counts[MissingValueKind.CENSORED],
                excluded_sample_count=counts[MissingValueKind.EXCLUDED],
                not_applicable_sample_count=counts[MissingValueKind.NOT_APPLICABLE],
                missing_fraction=(
                    float(missing_count / len(table.sample_ids))
                    if table.sample_ids
                    else 0.0
                ),
            )
        )
    return MissingnessEntitySummaryReport(
        entity_level=table.entity_level,
        entries=tuple(entries),
    )


def _build_missingness_entity_summary_report_vectorized(
    table: LabelFreeQuantTable,
    *,
    policy: MissingValueSummaryPolicy | None = None,
) -> MissingnessEntitySummaryReport:
    active_policy = policy or MissingValueSummaryPolicy()
    dense_view = build_dense_label_free_quant_table_view(table)
    missing_kind_codes = _apply_missing_value_summary_policy_codes(
        dense_view.missing_kind_codes,
        policy=active_policy,
    )
    counts_by_kind = {
        kind: np.sum(
            missing_kind_codes == missing_value_kind_to_code(kind),
            axis=1,
        )
        for kind in _MISSING_VALUE_KINDS
    }
    missing_counts = np.sum(
        np.isin(missing_kind_codes, _MISSING_BURDEN_CODES),
        axis=1,
    )
    sample_count = len(table.sample_ids)
    entries = tuple(
        MissingnessEntitySummaryEntry(
            entity_id=entity_id,
            observed_sample_count=int(
                counts_by_kind[MissingValueKind.OBSERVED][row_index]
            ),
            zero_sample_count=int(counts_by_kind[MissingValueKind.ZERO][row_index]),
            not_observed_sample_count=int(
                counts_by_kind[MissingValueKind.NOT_OBSERVED][row_index]
            ),
            filtered_sample_count=int(
                counts_by_kind[MissingValueKind.FILTERED][row_index]
            ),
            imputed_sample_count=int(
                counts_by_kind[MissingValueKind.IMPUTED][row_index]
            ),
            censored_sample_count=int(
                counts_by_kind[MissingValueKind.CENSORED][row_index]
            ),
            excluded_sample_count=int(
                counts_by_kind[MissingValueKind.EXCLUDED][row_index]
            ),
            not_applicable_sample_count=int(
                counts_by_kind[MissingValueKind.NOT_APPLICABLE][row_index]
            ),
            missing_fraction=float(missing_counts[row_index] / sample_count)
            if sample_count
            else 0.0,
        )
        for row_index, entity_id in enumerate(table.entity_ids)
    )
    return MissingnessEntitySummaryReport(
        entity_level=table.entity_level,
        entries=entries,
    )


def build_missingness_condition_summary_report(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    policy: MissingValueSummaryPolicy | None = None,
) -> MissingnessConditionSummaryReport:
    return _build_missingness_condition_summary_report_vectorized(
        table,
        design_entries=design_entries,
        policy=policy,
    )


def _build_missingness_condition_summary_report_pure(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    policy: MissingValueSummaryPolicy | None = None,
) -> MissingnessConditionSummaryReport:
    """Summarize missingness per condition and surface condition-specific absence."""
    active_policy = policy or MissingValueSummaryPolicy()
    lookup = _matrix_value_index(table)
    sample_ids_by_condition: dict[str, list[str]] = {}
    for entry in design_entries:
        sample_ids_by_condition.setdefault(entry.condition, []).append(entry.sample_id)

    observed_conditions_by_entity: dict[str, set[str]] = {}
    missing_conditions_by_entity: dict[str, set[str]] = {}
    for entity_id in table.entity_ids:
        observed_conditions: set[str] = set()
        missing_conditions: set[str] = set()
        for condition, sample_ids in sample_ids_by_condition.items():
            condition_kinds = [
                _apply_missing_value_summary_policy(
                    lookup[(entity_id, sample_id)].missing_value_kind,
                    policy=active_policy,
                )
                for sample_id in sample_ids
            ]
            if any(
                kind
                in (
                    MissingValueKind.OBSERVED,
                    MissingValueKind.ZERO,
                    MissingValueKind.IMPUTED,
                )
                for kind in condition_kinds
            ):
                observed_conditions.add(condition)
            if all(_is_missing_burden(kind) for kind in condition_kinds):
                missing_conditions.add(condition)
        observed_conditions_by_entity[entity_id] = observed_conditions
        missing_conditions_by_entity[entity_id] = missing_conditions

    entries: list[MissingnessConditionSummaryEntry] = []
    for condition, sample_ids in sorted(sample_ids_by_condition.items()):
        counts = _empty_missing_value_counts()
        for entity_id in table.entity_ids:
            for sample_id in sample_ids:
                kind = _apply_missing_value_summary_policy(
                    lookup[(entity_id, sample_id)].missing_value_kind,
                    policy=active_policy,
                )
                counts[kind] += 1
        total_values = len(table.entity_ids) * len(sample_ids)
        missing_count = sum(
            count for kind, count in counts.items() if _is_missing_burden(kind)
        )
        condition_specific_absence = tuple(
            sorted(
                entity_id
                for entity_id in table.entity_ids
                if condition in missing_conditions_by_entity[entity_id]
                and observed_conditions_by_entity[entity_id]
                and condition not in observed_conditions_by_entity[entity_id]
            )
        )
        entries.append(
            MissingnessConditionSummaryEntry(
                condition=condition,
                sample_ids=tuple(sample_ids),
                observed_value_count=counts[MissingValueKind.OBSERVED],
                zero_value_count=counts[MissingValueKind.ZERO],
                not_observed_value_count=counts[MissingValueKind.NOT_OBSERVED],
                filtered_value_count=counts[MissingValueKind.FILTERED],
                imputed_value_count=counts[MissingValueKind.IMPUTED],
                censored_value_count=counts[MissingValueKind.CENSORED],
                excluded_value_count=counts[MissingValueKind.EXCLUDED],
                not_applicable_value_count=counts[MissingValueKind.NOT_APPLICABLE],
                missing_fraction=(
                    float(missing_count / total_values) if total_values else 0.0
                ),
                condition_specific_absence_entity_ids=condition_specific_absence,
            )
        )
    return MissingnessConditionSummaryReport(
        entity_level=table.entity_level,
        entries=tuple(entries),
    )


def _build_missingness_condition_summary_report_vectorized(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    policy: MissingValueSummaryPolicy | None = None,
) -> MissingnessConditionSummaryReport:
    active_policy = policy or MissingValueSummaryPolicy()
    dense_view = build_dense_label_free_quant_table_view(table)
    missing_kind_codes = _apply_missing_value_summary_policy_codes(
        dense_view.missing_kind_codes,
        policy=active_policy,
    )
    sample_ids_by_condition: dict[str, list[str]] = {}
    for entry in design_entries:
        sample_ids_by_condition.setdefault(entry.condition, []).append(entry.sample_id)
    sample_indexes_by_condition = {
        condition: np.array(
            [dense_view.sample_index[sample_id] for sample_id in sample_ids],
            dtype=int,
        )
        for condition, sample_ids in sample_ids_by_condition.items()
    }
    observed_like_mask = np.isin(missing_kind_codes, _OBSERVED_VALUE_CODES)
    missing_burden_mask = np.isin(missing_kind_codes, _MISSING_BURDEN_CODES)
    observed_conditions_by_entity: dict[str, np.ndarray] = {}
    missing_conditions_by_entity: dict[str, np.ndarray] = {}
    for condition, sample_indexes in sample_indexes_by_condition.items():
        observed_conditions_by_entity[condition] = np.any(
            observed_like_mask[:, sample_indexes],
            axis=1,
        )
        missing_conditions_by_entity[condition] = np.all(
            missing_burden_mask[:, sample_indexes],
            axis=1,
        )

    counts_by_kind = {
        kind: missing_kind_codes == missing_value_kind_to_code(kind)
        for kind in _MISSING_VALUE_KINDS
    }
    entries: list[MissingnessConditionSummaryEntry] = []
    for condition, sample_ids in sorted(sample_ids_by_condition.items()):
        sample_indexes = sample_indexes_by_condition[condition]
        total_values = len(table.entity_ids) * len(sample_ids)
        observed_count = int(
            np.sum(counts_by_kind[MissingValueKind.OBSERVED][:, sample_indexes])
        )
        zero_count = int(
            np.sum(counts_by_kind[MissingValueKind.ZERO][:, sample_indexes])
        )
        not_observed_count = int(
            np.sum(counts_by_kind[MissingValueKind.NOT_OBSERVED][:, sample_indexes])
        )
        filtered_count = int(
            np.sum(counts_by_kind[MissingValueKind.FILTERED][:, sample_indexes])
        )
        imputed_count = int(
            np.sum(counts_by_kind[MissingValueKind.IMPUTED][:, sample_indexes])
        )
        censored_count = int(
            np.sum(counts_by_kind[MissingValueKind.CENSORED][:, sample_indexes])
        )
        excluded_count = int(
            np.sum(counts_by_kind[MissingValueKind.EXCLUDED][:, sample_indexes])
        )
        not_applicable_count = int(
            np.sum(counts_by_kind[MissingValueKind.NOT_APPLICABLE][:, sample_indexes])
        )
        missing_count = int(np.sum(missing_burden_mask[:, sample_indexes]))
        condition_specific_absence = tuple(
            sorted(
                entity_id
                for row_index, entity_id in enumerate(table.entity_ids)
                if missing_conditions_by_entity[condition][row_index]
                and any(
                    observed_conditions_by_entity[other_condition][row_index]
                    for other_condition in sample_indexes_by_condition
                    if other_condition != condition
                )
            )
        )
        entries.append(
            MissingnessConditionSummaryEntry(
                condition=condition,
                sample_ids=tuple(sample_ids),
                observed_value_count=observed_count,
                zero_value_count=zero_count,
                not_observed_value_count=not_observed_count,
                filtered_value_count=filtered_count,
                imputed_value_count=imputed_count,
                censored_value_count=censored_count,
                excluded_value_count=excluded_count,
                not_applicable_value_count=not_applicable_count,
                missing_fraction=float(missing_count / total_values)
                if total_values
                else 0.0,
                condition_specific_absence_entity_ids=condition_specific_absence,
            )
        )
    return MissingnessConditionSummaryReport(
        entity_level=table.entity_level,
        entries=tuple(entries),
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
            and _apply_missing_value_summary_policy(
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
            if _is_missing_burden(
                _apply_missing_value_summary_policy(
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

    trend_correlation: float | None = None
    if len(ordered_points) >= 2:
        x = np.array(
            [point.mean_log2_observed_abundance for point in ordered_points],
            dtype=float,
        )
        y = np.array([point.missing_fraction for point in ordered_points], dtype=float)
        if np.std(x) > 0.0 and np.std(y) > 0.0:
            correlation = float(np.corrcoef(x, y)[0, 1])
            trend_correlation = correlation if math.isfinite(correlation) else None
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
    missing_kind_codes = _apply_missing_value_summary_policy_codes(
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
    trend_correlation: float | None = None
    if len(ordered_points) >= 2:
        x = np.array(
            [point.mean_log2_observed_abundance for point in ordered_points],
            dtype=float,
        )
        y = np.array([point.missing_fraction for point in ordered_points], dtype=float)
        if np.std(x) > 0.0 and np.std(y) > 0.0:
            correlation = float(np.corrcoef(x, y)[0, 1])
            trend_correlation = correlation if math.isfinite(correlation) else None
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


def summarize_missing_values(
    table: LabelFreeQuantTable,
    *,
    policy: MissingValueSummaryPolicy | None = None,
) -> MissingValueSummaryReport:
    return _summarize_missing_values_vectorized(table, policy=policy)


def _summarize_missing_values_pure(
    table: LabelFreeQuantTable,
    *,
    policy: MissingValueSummaryPolicy | None = None,
) -> MissingValueSummaryReport:
    """Summarize missing values with explicit correction and sparse-entity filters."""
    active_policy = policy or MissingValueSummaryPolicy()
    lookup = _matrix_value_index(table)
    included_entity_ids: list[str] = []
    excluded_entity_ids: list[str] = []
    for entity_id in table.entity_ids:
        observed_samples = sum(
            1
            for sample_id in table.sample_ids
            if lookup[(entity_id, sample_id)].missing_value_kind
            in (
                MissingValueKind.OBSERVED,
                MissingValueKind.ZERO,
                MissingValueKind.IMPUTED,
            )
        )
        if observed_samples < active_policy.min_observed_samples_per_entity:
            excluded_entity_ids.append(entity_id)
            continue
        included_entity_ids.append(entity_id)

    entries: list[MissingValueSummaryEntry] = []
    for sample_id in table.sample_ids:
        counts = _empty_missing_value_counts()
        for entity_id in included_entity_ids:
            kind = _apply_missing_value_summary_policy(
                lookup[(entity_id, sample_id)].missing_value_kind,
                policy=active_policy,
            )
            counts[kind] += 1
        entries.append(
            MissingValueSummaryEntry(
                sample_id=sample_id,
                observed_count=counts[MissingValueKind.OBSERVED],
                zero_count=counts[MissingValueKind.ZERO],
                not_observed_count=counts[MissingValueKind.NOT_OBSERVED],
                filtered_count=counts[MissingValueKind.FILTERED],
                imputed_count=counts[MissingValueKind.IMPUTED],
                censored_count=counts[MissingValueKind.CENSORED],
                excluded_count=counts[MissingValueKind.EXCLUDED],
                not_applicable_count=counts[MissingValueKind.NOT_APPLICABLE],
            )
        )
    return MissingValueSummaryReport(
        entity_level=table.entity_level,
        policy=active_policy,
        entries=tuple(entries),
        included_entity_ids=tuple(included_entity_ids),
        excluded_entity_ids=tuple(excluded_entity_ids),
    )


def _summarize_missing_values_vectorized(
    table: LabelFreeQuantTable,
    *,
    policy: MissingValueSummaryPolicy | None = None,
) -> MissingValueSummaryReport:
    active_policy = policy or MissingValueSummaryPolicy()
    dense_view = build_dense_label_free_quant_table_view(table)
    missing_kind_codes = _apply_missing_value_summary_policy_codes(
        dense_view.missing_kind_codes,
        policy=active_policy,
    )
    observed_like_mask = np.isin(missing_kind_codes, _OBSERVED_VALUE_CODES)
    observed_sample_counts = np.sum(observed_like_mask, axis=1)
    included_mask = (
        observed_sample_counts >= active_policy.min_observed_samples_per_entity
    )
    included_entity_ids = tuple(
        entity_id
        for row_index, entity_id in enumerate(table.entity_ids)
        if included_mask[row_index]
    )
    excluded_entity_ids = tuple(
        entity_id
        for row_index, entity_id in enumerate(table.entity_ids)
        if not included_mask[row_index]
    )
    included_codes = missing_kind_codes[included_mask, :]
    counts_by_kind = {
        kind: np.sum(
            included_codes == missing_value_kind_to_code(kind),
            axis=0,
        )
        for kind in _MISSING_VALUE_KINDS
    }
    entries = tuple(
        MissingValueSummaryEntry(
            sample_id=sample_id,
            observed_count=int(counts_by_kind[MissingValueKind.OBSERVED][column_index]),
            zero_count=int(counts_by_kind[MissingValueKind.ZERO][column_index]),
            not_observed_count=int(
                counts_by_kind[MissingValueKind.NOT_OBSERVED][column_index]
            ),
            filtered_count=int(counts_by_kind[MissingValueKind.FILTERED][column_index]),
            imputed_count=int(counts_by_kind[MissingValueKind.IMPUTED][column_index]),
            censored_count=int(counts_by_kind[MissingValueKind.CENSORED][column_index]),
            excluded_count=int(counts_by_kind[MissingValueKind.EXCLUDED][column_index]),
            not_applicable_count=int(
                counts_by_kind[MissingValueKind.NOT_APPLICABLE][column_index]
            ),
        )
        for column_index, sample_id in enumerate(table.sample_ids)
    )
    return MissingValueSummaryReport(
        entity_level=table.entity_level,
        policy=active_policy,
        entries=entries,
        included_entity_ids=included_entity_ids,
        excluded_entity_ids=excluded_entity_ids,
    )


def build_missing_data_mechanism_report(
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> MissingDataMechanismReport:
    """Classify entity missingness with explicit condition and randomness labels."""
    lookup = _matrix_value_index(table)
    condition_by_sample = _condition_lookup(design_entries)
    batch_by_sample = {
        entry.sample_id: entry.batch for entry in design_entries if entry.batch
    }
    channel_by_sample = {
        entry.sample_id: (entry.multiplex_group, entry.multiplex_channel)
        for entry in design_entries
        if entry.multiplex_group and entry.multiplex_channel
    }
    sample_ids_by_condition_lists: dict[str, list[str]] = {}
    for entry in design_entries:
        sample_ids_by_condition_lists.setdefault(entry.condition, []).append(
            entry.sample_id
        )
    sample_ids_by_condition = {
        condition: tuple(sample_ids)
        for condition, sample_ids in sample_ids_by_condition_lists.items()
    }
    entries: list[MissingDataMechanismEntry] = []
    summary_counts = dict.fromkeys(MissingDataMechanism, 0)
    for entity_id in table.entity_ids:
        observed_conditions: set[str] = set()
        missing_samples: list[str] = []
        observed_samples: list[str] = []
        missing_conditions: set[str] = set()
        fully_missing_conditions: set[str] = set()
        for sample_id in table.sample_ids:
            cell = lookup[(entity_id, sample_id)]
            condition = condition_by_sample.get(sample_id, "unknown")
            if cell.missing_value_kind in (
                MissingValueKind.OBSERVED,
                MissingValueKind.ZERO,
                MissingValueKind.IMPUTED,
            ):
                observed_conditions.add(condition)
                observed_samples.append(sample_id)
                continue
            missing_samples.append(sample_id)
            missing_conditions.add(condition)
        for condition, sample_ids in sample_ids_by_condition.items():
            condition_kinds = {
                lookup[(entity_id, sample_id)].missing_value_kind
                for sample_id in sample_ids
            }
            if condition_kinds and all(
                _is_missing_burden(kind) for kind in condition_kinds
            ):
                fully_missing_conditions.add(condition)

        missing_batches = {
            batch_by_sample.get(sample_id)
            for sample_id in missing_samples
            if batch_by_sample.get(sample_id)
        }
        missing_channels = {
            channel_by_sample.get(sample_id)
            for sample_id in missing_samples
            if channel_by_sample.get(sample_id)
        }

        mechanism = MissingDataMechanism.MIXED_OR_UNRESOLVED
        note = (
            "missingness mixes structured and unstructured patterns or lacks enough "
            "metadata support"
        )
        if not missing_samples:
            mechanism = MissingDataMechanism.NO_MISSING_VALUES
            note = "entity is observed in every sample under the current table snapshot"
        elif fully_missing_conditions and observed_conditions:
            mechanism = MissingDataMechanism.CONDITION_SPECIFIC_ABSENCE
            note = (
                "one or more conditions are fully absent while another condition retains "
                "observed signal"
            )
        elif len(missing_samples) == 1 and len(observed_samples) >= 2:
            mechanism = MissingDataMechanism.LIKELY_TECHNICAL_FAILURE
            note = "one isolated missing sample breaks an otherwise observed pattern"
        elif len(missing_conditions) > 1:
            mechanism = MissingDataMechanism.MISSING_COMPLETELY_AT_RANDOM
            note = (
                "missing values are distributed across conditions without a condition-wide "
                "absence pattern"
            )
        elif len(missing_batches) == 1 or (
            len(missing_channels) == 1 and len(missing_samples) >= 2
        ):
            mechanism = MissingDataMechanism.BATCH_OR_CHANNEL_ISSUE
            note = "missingness aligns with one batch or one multiplex channel grouping"

        summary_counts[mechanism] += 1
        entries.append(
            MissingDataMechanismEntry(
                entity_id=entity_id,
                mechanism=mechanism,
                observed_conditions=tuple(sorted(observed_conditions)),
                missing_conditions=tuple(
                    sorted(fully_missing_conditions or missing_conditions)
                ),
                missing_samples=tuple(sorted(missing_samples)),
                note=note,
            )
        )
    return MissingDataMechanismReport(
        entity_level=table.entity_level,
        entries=tuple(entries),
        summary_counts=summary_counts,
    )


def build_missingness_classifier_report(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    policy: MissingValueSummaryPolicy | None = None,
    bin_count: int = 4,
) -> MissingnessClassifierReport:
    """Bundle owned missingness tables with explicit mechanism labels."""
    return MissingnessClassifierReport(
        sample_summary=summarize_missing_values(table, policy=policy),
        entity_summary=build_missingness_entity_summary_report(table, policy=policy),
        condition_summary=build_missingness_condition_summary_report(
            table,
            design_entries=design_entries,
            policy=policy,
        ),
        intensity_dependence=build_missingness_intensity_dependence_report(
            table,
            bin_count=bin_count,
            policy=policy,
        ),
        mechanism_report=build_missing_data_mechanism_report(
            table,
            design_entries,
        ),
    )


def classify_missingness(
    matrix: LabelFreeQuantTable | CanonicalQuantMatrix,
    design: tuple[ExperimentalDesignEntry, ...],
) -> MissingnessClassificationReport:
    """Classify entity-level missingness into five downstream statistical labels."""

    table = coerce_label_free_quant_table(matrix)
    if not design:
        raise ValueError("design must not be empty")

    sample_summary = summarize_missing_values(table)
    condition_summary = build_missingness_condition_summary_report(
        table,
        design_entries=design,
    )
    intensity_dependence = build_missingness_intensity_dependence_report(table)
    condition_by_sample = _condition_lookup(design)
    lookup = _matrix_value_index(table)

    failed_sample_ids = _failed_sample_ids(sample_summary)
    intensity_lookup = {
        point.entity_id: point.mean_log2_observed_abundance
        for point in intensity_dependence.plot_points
    }
    condition_specific_entity_ids = {
        entity_id
        for entry in condition_summary.entries
        for entity_id in entry.condition_specific_absence_entity_ids
    }
    low_intensity_cutoff = _low_intensity_cutoff(intensity_dependence)

    entries: list[MissingnessClassificationEntry] = []
    for entity_id in table.entity_ids:
        missing_samples = [
            sample_id
            for sample_id in table.sample_ids
            if lookup[(entity_id, sample_id)].missing_value_kind
            in (MissingValueKind.NOT_OBSERVED, MissingValueKind.FILTERED)
        ]
        observed_samples = [
            sample_id
            for sample_id in table.sample_ids
            if lookup[(entity_id, sample_id)].missing_value_kind
            in (MissingValueKind.OBSERVED, MissingValueKind.ZERO)
        ]
        missing_fraction = (
            float(len(missing_samples) / len(table.sample_ids))
            if table.sample_ids
            else 0.0
        )
        observed_conditions = {
            condition_by_sample[sample_id]
            for sample_id in observed_samples
            if sample_id in condition_by_sample
        }
        missing_conditions = {
            condition_by_sample[sample_id]
            for sample_id in missing_samples
            if sample_id in condition_by_sample
        }
        mean_log2_observed_abundance = intensity_lookup.get(entity_id)

        label = MissingnessLabel.RANDOM
        note = "missing values are distributed without stronger structural evidence"
        if not observed_samples:
            label = MissingnessLabel.STRUCTURAL_ABSENCE
            note = "entity is missing in every sample under the current study design"
        elif entity_id in condition_specific_entity_ids:
            label = MissingnessLabel.CONDITION_SPECIFIC
            note = (
                "at least one condition is fully missing while another condition retains "
                "observed signal, so this pattern must not be treated as random"
            )
        elif missing_samples and set(missing_samples) <= set(failed_sample_ids):
            label = MissingnessLabel.SAMPLE_FAILURE
            note = "all missing values land in globally failure-prone samples"
        elif (
            intensity_dependence.intensity_dependent_missingness_detected
            and missing_fraction > 0.0
            and mean_log2_observed_abundance is not None
            and mean_log2_observed_abundance <= low_intensity_cutoff
            and len(observed_conditions | missing_conditions) > 1
        ):
            label = MissingnessLabel.INTENSITY_CENSORED
            note = "low observed abundance plus study-wide intensity dependence supports censoring"

        entries.append(
            MissingnessClassificationEntry(
                entity_id=entity_id,
                label=label,
                observed_sample_count=len(observed_samples),
                missing_sample_count=len(missing_samples),
                missing_fraction=missing_fraction,
                mean_log2_observed_abundance=mean_log2_observed_abundance,
                note=note,
            )
        )

    return MissingnessClassificationReport(
        entries=tuple(sorted(entries, key=lambda entry: entry.entity_id)),
        failed_sample_ids=tuple(sorted(failed_sample_ids)),
        note=(
            "missingness classification separates random loss from intensity censoring, "
            "condition-specific absence, sample failure, and structural absence so "
            "downstream statistics can react to mechanism instead of treating every "
            "missing cell the same way"
        ),
    )


def render_missingness_classification_tsv(
    report: MissingnessClassificationReport,
) -> str:
    """Render five-label missingness classifications as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "entity_id",
            "label",
            "observed_sample_count",
            "missing_sample_count",
            "missing_fraction",
            "mean_log2_observed_abundance",
            "note",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.entity_id,
                entry.label.value,
                str(entry.observed_sample_count),
                str(entry.missing_sample_count),
                f"{entry.missing_fraction:.6f}",
                ""
                if entry.mean_log2_observed_abundance is None
                else f"{entry.mean_log2_observed_abundance:.6f}",
                entry.note,
            )
        )
    return buffer.getvalue()


def _apply_missing_value_summary_policy(
    kind: MissingValueKind,
    *,
    policy: MissingValueSummaryPolicy,
) -> MissingValueKind:
    if (
        kind is MissingValueKind.ZERO
        and policy.zero_policy is MissingValueCorrectionPolicy.TREAT_AS_NOT_OBSERVED
    ):
        return MissingValueKind.NOT_OBSERVED
    if (
        kind is MissingValueKind.FILTERED
        and policy.filtered_policy is MissingValueCorrectionPolicy.TREAT_AS_NOT_OBSERVED
    ):
        return MissingValueKind.NOT_OBSERVED
    return kind


def _apply_missing_value_summary_policy_codes(
    missing_kind_codes: np.ndarray,
    *,
    policy: MissingValueSummaryPolicy,
) -> np.ndarray:
    adjusted = missing_kind_codes.copy()
    if policy.zero_policy is MissingValueCorrectionPolicy.TREAT_AS_NOT_OBSERVED:
        adjusted[adjusted == missing_value_kind_to_code(MissingValueKind.ZERO)] = (
            missing_value_kind_to_code(MissingValueKind.NOT_OBSERVED)
        )
    if policy.filtered_policy is MissingValueCorrectionPolicy.TREAT_AS_NOT_OBSERVED:
        adjusted[adjusted == missing_value_kind_to_code(MissingValueKind.FILTERED)] = (
            missing_value_kind_to_code(MissingValueKind.NOT_OBSERVED)
        )
    return adjusted


def _failed_sample_ids(
    sample_summary: MissingValueSummaryReport,
    *,
    minimum_missing_fraction: float = 0.6,
) -> tuple[str, ...]:
    failed: list[str] = []
    for entry in sample_summary.entries:
        total = (
            entry.observed_count
            + entry.zero_count
            + entry.not_observed_count
            + entry.filtered_count
        )
        if total <= 0:
            continue
        missing_fraction = float(
            (entry.not_observed_count + entry.filtered_count) / total
        )
        if missing_fraction >= minimum_missing_fraction:
            failed.append(entry.sample_id)
    return tuple(sorted(failed))


def _low_intensity_cutoff(
    report: MissingnessIntensityDependenceReport,
) -> float:
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


__all__ = [
    "MissingnessClassificationEntry",
    "MissingnessClassificationReport",
    "MissingnessLabel",
    "build_missingness_condition_summary_report",
    "build_missingness_classifier_report",
    "build_missing_data_mechanism_report",
    "build_missingness_entity_summary_report",
    "build_missingness_intensity_dependence_report",
    "classify_missingness",
    "render_missingness_classification_tsv",
    "summarize_missing_values",
]
