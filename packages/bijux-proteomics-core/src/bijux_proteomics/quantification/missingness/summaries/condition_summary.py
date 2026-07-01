# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Condition-level missingness summaries."""

from __future__ import annotations

import numpy as np

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts.input_models import MissingValueKind
from bijux_proteomics.quantification.contracts.matrix_building import (
    _matrix_value_index,
)
from bijux_proteomics.quantification.contracts.matrix_models import LabelFreeQuantTable
from bijux_proteomics.quantification.contracts.missingness import (
    MissingnessConditionSummaryEntry,
    MissingnessConditionSummaryReport,
    MissingValueSummaryPolicy,
)
from bijux_proteomics.quantification.matrix import (
    build_dense_label_free_quant_table_view,
    missing_value_kind_to_code,
)
from bijux_proteomics.quantification.missingness.policy import (
    _MISSING_BURDEN_CODES,
    _MISSING_VALUE_KINDS,
    _OBSERVED_VALUE_CODES,
    apply_missing_value_summary_policy,
    apply_missing_value_summary_policy_codes,
    empty_missing_value_counts,
    is_missing_burden,
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
                apply_missing_value_summary_policy(
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
            if all(is_missing_burden(kind) for kind in condition_kinds):
                missing_conditions.add(condition)
        observed_conditions_by_entity[entity_id] = observed_conditions
        missing_conditions_by_entity[entity_id] = missing_conditions

    entries: list[MissingnessConditionSummaryEntry] = []
    for condition, sample_ids in sorted(sample_ids_by_condition.items()):
        counts = empty_missing_value_counts()
        for entity_id in table.entity_ids:
            for sample_id in sample_ids:
                kind = apply_missing_value_summary_policy(
                    lookup[(entity_id, sample_id)].missing_value_kind,
                    policy=active_policy,
                )
                counts[kind] += 1
        total_values = len(table.entity_ids) * len(sample_ids)
        missing_count = sum(
            count for kind, count in counts.items() if is_missing_burden(kind)
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
    missing_kind_codes = apply_missing_value_summary_policy_codes(
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


__all__ = [
    "_build_missingness_condition_summary_report_pure",
    "_build_missingness_condition_summary_report_vectorized",
    "build_missingness_condition_summary_report",
]
