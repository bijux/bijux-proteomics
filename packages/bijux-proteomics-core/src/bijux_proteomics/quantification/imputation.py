# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned missing-value imputation for quantitative proteomics tables."""

from __future__ import annotations

import numpy as np

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import (
    ImputationEntry,
    ImputationMethod,
    ImputationReport,
    ImputationSensitivityEntry,
    ImputationSensitivityReport,
    LabelFreeQuantTable,
    MissingValueKind,
    QuantMeasureKind,
    QuantValue,
    apply_benjamini_hochberg,
    build_differential_abundance_report,
)


def build_imputation_report(
    before: LabelFreeQuantTable,
    after: LabelFreeQuantTable,
) -> ImputationReport:
    """Build a stable ledger of values introduced by imputation."""
    _validate_imputation_pair(before, after)
    knn_neighbors = (
        _knn_neighbor_lookup(before)
        if after.imputation_method is ImputationMethod.KNN
        else {}
    )
    before_lookup = {
        (value.entity_id, value.sample_id): value for value in before.values
    }
    entries: list[ImputationEntry] = []
    for value in after.values:
        key = (value.entity_id, value.sample_id)
        prior = before_lookup[key]
        if prior.abundance is None and value.abundance is not None:
            entries.append(
                ImputationEntry(
                    entity_id=value.entity_id,
                    sample_id=value.sample_id,
                    original_missing_value_kind=prior.missing_value_kind,
                    imputed_abundance=float(value.abundance),
                    neighbor_entity_ids=knn_neighbors.get(key, ()),
                )
            )
    return ImputationReport(
        entity_level=after.entity_level,
        method=after.imputation_method,
        entries=tuple(entries),
        imputed_value_count=len(entries),
        note=(
            "no values were imputed under the current table pair"
            if not entries
            else "missing abundances were filled under one explicit imputation policy"
        ),
    )


def impute_label_free_table(
    table: LabelFreeQuantTable,
    *,
    method: ImputationMethod = ImputationMethod.NONE,
) -> LabelFreeQuantTable:
    """Impute a label-free quant table under one explicit imputation policy."""
    if table.measure_kind is not QuantMeasureKind.INTENSITY:
        raise ValueError("imputation only applies to intensity-based quant tables")
    if method is ImputationMethod.NONE:
        return table.model_copy(update={"imputation_method": method})
    if method is ImputationMethod.LOW_INTENSITY:
        return _low_intensity_imputed_table(table)
    if method is ImputationMethod.KNN:
        return _knn_imputed_table(table)
    raise ValueError(f"unsupported imputation method: {method.value}")


def build_imputation_sensitivity_report(
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    condition_a: str | None = None,
    condition_b: str | None = None,
    methods: tuple[ImputationMethod, ...] = (
        ImputationMethod.NONE,
        ImputationMethod.LOW_INTENSITY,
        ImputationMethod.KNN,
    ),
) -> ImputationSensitivityReport:
    """Compare downstream differential behavior across imputation policies."""
    entries: list[ImputationSensitivityEntry] = []
    primary_narratives: set[tuple[str | None, str | None]] = set()
    resolved_condition_a = condition_a
    resolved_condition_b = condition_b
    for method in methods:
        try:
            imputed = impute_label_free_table(table, method=method)
            imputation_report = build_imputation_report(table, imputed)
            differential = apply_benjamini_hochberg(
                build_differential_abundance_report(
                    imputed,
                    design_entries,
                    condition_a=condition_a,
                    condition_b=condition_b,
                )
            )
            resolved_condition_a = differential.condition_a
            resolved_condition_b = differential.condition_b
            top_entry = differential.entries[0] if differential.entries else None
            top_direction = (
                "up_in_condition_b"
                if top_entry is not None and top_entry.log2_fold_change > 0.0
                else "up_in_condition_a"
                if top_entry is not None and top_entry.log2_fold_change < 0.0
                else "neutral"
                if top_entry is not None
                else None
            )
            primary_narratives.add(
                (None if top_entry is None else top_entry.entity_id, top_direction)
            )
            entries.append(
                ImputationSensitivityEntry(
                    method=method,
                    supported=True,
                    imputed_value_count=imputation_report.imputed_value_count,
                    top_entity_id=None if top_entry is None else top_entry.entity_id,
                    top_entity_direction=top_direction,
                    top_entity_effect_size=(
                        None
                        if top_entry is None
                        else top_entry.effect_size_cohens_d
                    ),
                    note=(
                        "downstream differential abundance was recomputed under one explicit imputation policy"
                    ),
                )
            )
        except Exception as exc:  # noqa: BLE001
            entries.append(
                ImputationSensitivityEntry(
                    method=method,
                    supported=False,
                    imputed_value_count=0,
                    note=str(exc),
                )
            )
    if resolved_condition_a is None or resolved_condition_b is None:
        raise ValueError(
            "imputation sensitivity requires resolvable contrast conditions"
        )
    return ImputationSensitivityReport(
        condition_a=resolved_condition_a,
        condition_b=resolved_condition_b,
        entries=tuple(entries),
        primary_narrative_changed=len(primary_narratives) > 1,
    )


def _low_intensity_imputed_table(table: LabelFreeQuantTable) -> LabelFreeQuantTable:
    """Impute absent low-signal intensities from the lower tail of each sample."""
    matrix, sample_ids, _, sample_index, _ = _table_grid(table)
    sample_fill_values = _sample_low_intensity_fill_values(
        matrix,
        sample_ids,
        sample_index,
    )
    return _rebuild_imputed_table(
        table,
        fill_lookup={
            (value.entity_id, value.sample_id): sample_fill_values[value.sample_id]
            for value in table.values
            if value.abundance is None
            and value.missing_value_kind
            in {MissingValueKind.NOT_OBSERVED, MissingValueKind.FILTERED}
        },
        method=ImputationMethod.LOW_INTENSITY,
    )


def _knn_imputed_table(table: LabelFreeQuantTable) -> LabelFreeQuantTable:
    """Impute missing abundances from nearby entity profiles within each sample."""
    (
        matrix,
        sample_ids,
        entity_ids,
        sample_index,
        entity_index,
    ) = _table_grid(table)
    sample_fill_values = _sample_low_intensity_fill_values(
        matrix,
        sample_ids,
        sample_index,
    )
    fill_lookup: dict[tuple[str, str], float] = {}
    for value in table.values:
        if value.abundance is not None or value.missing_value_kind not in {
            MissingValueKind.NOT_OBSERVED,
            MissingValueKind.FILTERED,
        }:
            continue
        row_index = entity_index[value.entity_id]
        col_index = sample_index[value.sample_id]
        neighbors = _select_knn_neighbors(
            matrix,
            entity_ids=entity_ids,
            target_row=row_index,
            target_col=col_index,
        )
        if neighbors:
            weights = np.array(
                [1.0 / max(distance, 1e-6) for _, distance in neighbors],
                dtype=float,
            )
            abundances = np.array(
                [matrix[entity_index[entity_id], col_index] for entity_id, _ in neighbors],
                dtype=float,
            )
            fill_lookup[(value.entity_id, value.sample_id)] = float(
                np.average(abundances, weights=weights)
            )
            continue
        fill_lookup[(value.entity_id, value.sample_id)] = sample_fill_values[
            value.sample_id
        ]
    return _rebuild_imputed_table(
        table,
        fill_lookup=fill_lookup,
        method=ImputationMethod.KNN,
    )


def _table_grid(
    table: LabelFreeQuantTable,
) -> tuple[np.ndarray, list[str], list[str], dict[str, int], dict[str, int]]:
    sample_ids = list(table.sample_ids)
    entity_ids = list(table.entity_ids)
    sample_index = {sample_id: index for index, sample_id in enumerate(sample_ids)}
    entity_index = {entity_id: index for index, entity_id in enumerate(entity_ids)}
    matrix = np.full((len(entity_ids), len(sample_ids)), np.nan, dtype=float)
    for value in table.values:
        if value.abundance is None:
            continue
        matrix[entity_index[value.entity_id], sample_index[value.sample_id]] = float(
            value.abundance
        )
    return matrix, sample_ids, entity_ids, sample_index, entity_index


def _sample_low_intensity_fill_values(
    matrix: np.ndarray,
    sample_ids: list[str],
    sample_index: dict[str, int],
) -> dict[str, float]:
    sample_fill_values: dict[str, float] = {}
    finite_positive = matrix[np.isfinite(matrix) & (matrix > 0.0)]
    global_floor = (
        max(float(np.nanpercentile(finite_positive, 5.0)) * 0.5, 1e-6)
        if finite_positive.size
        else 1e-6
    )
    for sample_id in sample_ids:
        column = matrix[:, sample_index[sample_id]]
        positives = column[np.isfinite(column) & (column > 0.0)]
        if positives.size == 0:
            sample_fill_values[sample_id] = global_floor
            continue
        fill_value = max(float(np.nanpercentile(positives, 5.0)) * 0.5, 1e-6)
        sample_fill_values[sample_id] = fill_value
    return sample_fill_values


def _rebuild_imputed_table(
    table: LabelFreeQuantTable,
    *,
    fill_lookup: dict[tuple[str, str], float],
    method: ImputationMethod,
) -> LabelFreeQuantTable:
    rebuilt_values: list[QuantValue] = []
    for value in table.values:
        if value.abundance is not None:
            rebuilt_values.append(value)
            continue
        if value.missing_value_kind not in (
            MissingValueKind.NOT_OBSERVED,
            MissingValueKind.FILTERED,
        ):
            rebuilt_values.append(value)
            continue
        fill_value = fill_lookup[(value.entity_id, value.sample_id)]
        rebuilt_values.append(
            value.model_copy(update={"abundance": max(fill_value, 0.0)})
        )
    return table.model_copy(
        update={
            "values": tuple(rebuilt_values),
            "imputation_method": method,
        }
    )


def _knn_neighbor_lookup(
    table: LabelFreeQuantTable,
) -> dict[tuple[str, str], tuple[str, ...]]:
    matrix, _, entity_ids, sample_index, entity_index = _table_grid(table)
    neighbors: dict[tuple[str, str], tuple[str, ...]] = {}
    for value in table.values:
        if value.abundance is not None or value.missing_value_kind not in {
            MissingValueKind.NOT_OBSERVED,
            MissingValueKind.FILTERED,
        }:
            continue
        selected = _select_knn_neighbors(
            matrix,
            entity_ids=entity_ids,
            target_row=entity_index[value.entity_id],
            target_col=sample_index[value.sample_id],
        )
        neighbors[(value.entity_id, value.sample_id)] = tuple(
            entity_id for entity_id, _ in selected
        )
    return neighbors


def _select_knn_neighbors(
    matrix: np.ndarray,
    *,
    entity_ids: list[str],
    target_row: int,
    target_col: int,
    max_neighbors: int = 3,
) -> tuple[tuple[str, float], ...]:
    target_row_values = matrix[target_row, :]
    candidates: list[tuple[int, float, str]] = []
    for candidate_row, entity_id in enumerate(entity_ids):
        if candidate_row == target_row or np.isnan(matrix[candidate_row, target_col]):
            continue
        candidate_values = matrix[candidate_row, :]
        shared = np.isfinite(target_row_values) & np.isfinite(candidate_values)
        shared[target_col] = False
        overlap_count = int(np.count_nonzero(shared))
        if overlap_count > 0:
            distance = float(
                np.sqrt(
                    np.mean(
                        np.square(
                            np.log2(target_row_values[shared] + 1.0)
                            - np.log2(candidate_values[shared] + 1.0)
                        )
                    )
                )
            )
        else:
            target_profile = target_row_values[
                np.isfinite(target_row_values)
                & (np.arange(target_row_values.size) != target_col)
            ]
            candidate_profile = candidate_values[
                np.isfinite(candidate_values)
                & (np.arange(candidate_values.size) != target_col)
            ]
            if target_profile.size == 0 or candidate_profile.size == 0:
                continue
            distance = abs(
                float(np.median(np.log2(target_profile + 1.0)))
                - float(np.median(np.log2(candidate_profile + 1.0)))
            )
        candidates.append((overlap_count, distance, entity_id))
    if not candidates:
        return ()
    candidates.sort(
        key=lambda item: (0 if item[0] > 0 else 1, item[1], -item[0], item[2])
    )
    return tuple(
        (entity_id, distance)
        for overlap_count, distance, entity_id in candidates[:max_neighbors]
    )


def _validate_imputation_pair(
    before: LabelFreeQuantTable,
    after: LabelFreeQuantTable,
) -> None:
    if before.sample_ids != after.sample_ids or before.entity_ids != after.entity_ids:
        raise ValueError("before and after tables must cover the same sample/entity grid")


__all__ = [
    "build_imputation_report",
    "build_imputation_sensitivity_report",
    "impute_label_free_table",
]
