# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned missingness analysis for quantitative proteomics tables."""

from __future__ import annotations

import math

import numpy as np

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
)


def build_missingness_entity_summary_report(
    table: LabelFreeQuantTable,
    *,
    policy: MissingValueSummaryPolicy | None = None,
) -> MissingnessEntitySummaryReport:
    """Summarize missingness per quantified entity across all samples."""
    active_policy = policy or MissingValueSummaryPolicy()
    lookup = _matrix_value_index(table)
    entries: list[MissingnessEntitySummaryEntry] = []
    for entity_id in table.entity_ids:
        counts = {
            MissingValueKind.OBSERVED: 0,
            MissingValueKind.ZERO: 0,
            MissingValueKind.NOT_OBSERVED: 0,
            MissingValueKind.FILTERED: 0,
        }
        for sample_id in table.sample_ids:
            kind = _apply_missing_value_summary_policy(
                lookup[(entity_id, sample_id)].missing_value_kind,
                policy=active_policy,
            )
            counts[kind] += 1
        missing_count = (
            counts[MissingValueKind.NOT_OBSERVED] + counts[MissingValueKind.FILTERED]
        )
        entries.append(
            MissingnessEntitySummaryEntry(
                entity_id=entity_id,
                observed_sample_count=counts[MissingValueKind.OBSERVED],
                zero_sample_count=counts[MissingValueKind.ZERO],
                not_observed_sample_count=counts[MissingValueKind.NOT_OBSERVED],
                filtered_sample_count=counts[MissingValueKind.FILTERED],
                missing_fraction=(
                    float(missing_count / len(table.sample_ids)) if table.sample_ids else 0.0
                ),
            )
        )
    return MissingnessEntitySummaryReport(
        entity_level=table.entity_level,
        entries=tuple(entries),
    )


def build_missingness_condition_summary_report(
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
                kind in (MissingValueKind.OBSERVED, MissingValueKind.ZERO)
                for kind in condition_kinds
            ):
                observed_conditions.add(condition)
            if all(
                kind in (MissingValueKind.NOT_OBSERVED, MissingValueKind.FILTERED)
                for kind in condition_kinds
            ):
                missing_conditions.add(condition)
        observed_conditions_by_entity[entity_id] = observed_conditions
        missing_conditions_by_entity[entity_id] = missing_conditions

    entries: list[MissingnessConditionSummaryEntry] = []
    for condition, sample_ids in sorted(sample_ids_by_condition.items()):
        counts = {
            MissingValueKind.OBSERVED: 0,
            MissingValueKind.ZERO: 0,
            MissingValueKind.NOT_OBSERVED: 0,
            MissingValueKind.FILTERED: 0,
        }
        for entity_id in table.entity_ids:
            for sample_id in sample_ids:
                kind = _apply_missing_value_summary_policy(
                    lookup[(entity_id, sample_id)].missing_value_kind,
                    policy=active_policy,
                )
                counts[kind] += 1
        total_values = len(table.entity_ids) * len(sample_ids)
        missing_count = (
            counts[MissingValueKind.NOT_OBSERVED] + counts[MissingValueKind.FILTERED]
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


def build_missingness_intensity_dependence_report(
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
            in (MissingValueKind.OBSERVED, MissingValueKind.ZERO)
        ]
        if not observed_abundances:
            continue
        missing_count = sum(
            1
            for sample_id in table.sample_ids
            if _apply_missing_value_summary_policy(
                lookup[(entity_id, sample_id)].missing_value_kind,
                policy=active_policy,
            )
            in (MissingValueKind.NOT_OBSERVED, MissingValueKind.FILTERED)
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
        groups = np.array_split(np.array(ordered_points, dtype=object), active_bin_count)
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
            in (MissingValueKind.OBSERVED, MissingValueKind.ZERO)
        )
        if observed_samples < active_policy.min_observed_samples_per_entity:
            excluded_entity_ids.append(entity_id)
            continue
        included_entity_ids.append(entity_id)

    entries: list[MissingValueSummaryEntry] = []
    for sample_id in table.sample_ids:
        counts = {
            MissingValueKind.OBSERVED: 0,
            MissingValueKind.ZERO: 0,
            MissingValueKind.NOT_OBSERVED: 0,
            MissingValueKind.FILTERED: 0,
        }
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
            )
        )
    return MissingValueSummaryReport(
        entity_level=table.entity_level,
        policy=active_policy,
        entries=tuple(entries),
        included_entity_ids=tuple(included_entity_ids),
        excluded_entity_ids=tuple(excluded_entity_ids),
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
    sample_ids_by_condition: dict[str, tuple[str, ...]] = {}
    for entry in design_entries:
        sample_ids_by_condition.setdefault(entry.condition, [])
        sample_ids_by_condition[entry.condition].append(entry.sample_id)
    sample_ids_by_condition = {
        condition: tuple(sample_ids)
        for condition, sample_ids in sample_ids_by_condition.items()
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
            ):
                observed_conditions.add(condition)
                observed_samples.append(sample_id)
                continue
            missing_samples.append(sample_id)
            missing_conditions.add(condition)
        for condition, sample_ids in sample_ids_by_condition.items():
            condition_kinds = {
                lookup[(entity_id, sample_id)].missing_value_kind for sample_id in sample_ids
            }
            if condition_kinds and condition_kinds <= {
                MissingValueKind.NOT_OBSERVED,
                MissingValueKind.FILTERED,
            }:
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
                missing_conditions=tuple(sorted(fully_missing_conditions or missing_conditions)),
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


__all__ = [
    "build_missingness_condition_summary_report",
    "build_missingness_classifier_report",
    "build_missing_data_mechanism_report",
    "build_missingness_entity_summary_report",
    "build_missingness_intensity_dependence_report",
    "summarize_missing_values",
]
