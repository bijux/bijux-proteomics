# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned missing-value imputation for quantitative proteomics tables."""

from __future__ import annotations

from itertools import combinations

import numpy as np

from bijux_proteomics.domain.semantic_ids import build_matrix_id
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts.differential import (
    DifferentialAbundanceEntry,
    DifferentialAbundanceReport,
    DifferentialAbundanceTestType,
    PairedDifferentialPolicy,
    build_differential_abundance_report,
)
from bijux_proteomics.quantification.contracts.input_models import (
    ImputationMethod,
    MissingValueKind,
    QuantMeasureKind,
)
from bijux_proteomics.quantification.contracts.matrix_models import (
    LabelFreeQuantTable,
    QuantCellImputationProvenance,
    QuantValue,
    QuantValueOrigin,
)
from bijux_proteomics.quantification.contracts.normalization_imputation import (
    ImputationDependentHitEntry,
    ImputationEntry,
    ImputationReport,
    ImputationSensitivityChangedSignificanceEntry,
    ImputationSensitivityEntry,
    ImputationSensitivityOverlapEntry,
    ImputationSensitivityReport,
)
from bijux_proteomics.quantification.matrix.core_matrix import (
    quant_matrix_to_dense_array,
    rebuild_quant_matrix_from_dense_array,
)
from bijux_proteomics.quantification.statistics.differential_imputation_dependence import (
    compare_imputation_policies,
)


def build_imputation_report(
    before: LabelFreeQuantTable,
    after: LabelFreeQuantTable,
) -> ImputationReport:
    """Build a stable ledger of values introduced by imputation."""
    _validate_imputation_pair(before, after)
    before_lookup = {
        (value.entity_id, value.sample_id): value for value in before.values
    }
    entries: list[ImputationEntry] = []
    for value in after.values:
        key = (value.entity_id, value.sample_id)
        prior = before_lookup[key]
        if prior.abundance is None and value.abundance is not None:
            if value.imputation_provenance is None:
                raise ValueError(
                    "imputed cells must carry explicit per-cell imputation provenance"
                )
            entries.append(
                ImputationEntry(
                    entity_id=value.entity_id,
                    sample_id=value.sample_id,
                    original_missing_value_kind=prior.missing_value_kind,
                    imputed_abundance=float(value.abundance),
                    neighbor_entity_ids=value.imputation_provenance.donor_entity_ids,
                    donor_sample_ids=value.imputation_provenance.donor_sample_ids,
                    reference_group=value.imputation_provenance.reference_group,
                    strategy=value.imputation_provenance.strategy,
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
    design_entries: tuple[ExperimentalDesignEntry, ...] = (),
) -> LabelFreeQuantTable:
    """Impute a label-free quant table under one explicit imputation policy."""
    if table.measure_kind is not QuantMeasureKind.INTENSITY:
        raise ValueError("imputation only applies to intensity-based quant tables")
    if method is ImputationMethod.NONE:
        quant_matrix = rebuild_quant_matrix_from_dense_array(
            table.to_quant_matrix(),
            quant_matrix_to_dense_array(table.to_quant_matrix()),
            transformation_step="imputation:none",
            metadata_updates={"imputation_method": method.value},
        ).model_copy(
            update={
                "matrix_id": build_matrix_id(
                    table.entity_level.value,
                    table.measure_kind.value,
                    aggregation_method=table.aggregation_method.value,
                    normalization_method=table.normalization_method.value,
                    imputation_method=method.value,
                )
            }
        )
        return table.model_copy(
            update={
                "quant_matrix": quant_matrix,
                "imputation_method": method,
            }
        )
    if method is ImputationMethod.LOW_INTENSITY:
        return _low_intensity_imputed_table(table)
    if method is ImputationMethod.GROUP_AWARE_LOW_INTENSITY:
        return _group_aware_low_intensity_imputed_table(
            table,
            design_entries=design_entries,
        )
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
    significance_threshold: float = 0.05,
) -> ImputationSensitivityReport:
    """Compare downstream differential behavior across imputation policies."""
    entries: list[ImputationSensitivityEntry] = []
    overlap_entries: list[ImputationSensitivityOverlapEntry] = []
    changed_significance_entries: list[
        ImputationSensitivityChangedSignificanceEntry
    ] = []
    imputation_dependent_hits: list[ImputationDependentHitEntry] = []
    primary_narratives: set[tuple[str | None, str | None]] = set()
    resolved_condition_a = condition_a
    resolved_condition_b = condition_b
    differential_by_method: dict[ImputationMethod, DifferentialAbundanceReport] = {}
    for method in methods:
        try:
            imputed = impute_label_free_table(
                table,
                method=method,
                design_entries=design_entries,
            )
            imputation_report = build_imputation_report(table, imputed)
            paired_policy = (
                PairedDifferentialPolicy()
                if all(entry.pair_id not in (None, "") for entry in design_entries)
                else None
            )
            differential = build_differential_abundance_report(
                imputed,
                design_entries,
                condition_a=condition_a,
                condition_b=condition_b,
                test_type=(
                    DifferentialAbundanceTestType.PAIRED_T_TEST
                    if paired_policy is not None
                    else DifferentialAbundanceTestType.WELCH_T_TEST
                ),
                paired_policy=paired_policy,
            )
            differential_by_method[method] = differential
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
                    significant_entity_count=sum(
                        1
                        for entry in differential.entries
                        if entry.adjusted_p_value is not None
                        and entry.adjusted_p_value <= significance_threshold
                    ),
                    top_entity_id=None if top_entry is None else top_entry.entity_id,
                    top_entity_direction=top_direction,
                    top_entity_effect_size=(
                        None if top_entry is None else top_entry.effect_size_cohens_d
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
                    significant_entity_count=0,
                    note=str(exc),
                )
            )
    if resolved_condition_a is None or resolved_condition_b is None:
        raise ValueError(
            "imputation sensitivity requires resolvable contrast conditions"
        )

    policy_comparison = None
    if (
        ImputationMethod.NONE in differential_by_method
        and len(differential_by_method) >= 2
    ):
        policy_comparison = compare_imputation_policies(
            differential_by_method,
            significance_threshold=significance_threshold,
        )

    supported_methods = tuple(
        entry.method
        for entry in entries
        if entry.supported and entry.method in differential_by_method
    )
    significant_entities_by_method: dict[ImputationMethod, set[str]] = {
        method: {
            entry.entity_id
            for entry in differential_by_method[method].entries
            if entry.adjusted_p_value is not None
            and entry.adjusted_p_value <= significance_threshold
        }
        for method in supported_methods
    }
    entry_lookup_by_method: dict[
        ImputationMethod, dict[str, DifferentialAbundanceEntry]
    ] = {
        method: {
            entry.entity_id: entry for entry in differential_by_method[method].entries
        }
        for method in supported_methods
    }

    for method_a, method_b in combinations(supported_methods, 2):
        significant_a = significant_entities_by_method[method_a]
        significant_b = significant_entities_by_method[method_b]
        overlap = significant_a & significant_b
        union = significant_a | significant_b
        overlap_entries.append(
            ImputationSensitivityOverlapEntry(
                method_a=method_a,
                method_b=method_b,
                significant_entity_count_a=len(significant_a),
                significant_entity_count_b=len(significant_b),
                overlapping_significant_entity_count=len(overlap),
                method_a_only_count=len(significant_a - significant_b),
                method_b_only_count=len(significant_b - significant_a),
                jaccard_index=(float(len(overlap) / len(union)) if union else 1.0),
            )
        )

    baseline_method = ImputationMethod.NONE
    if baseline_method in entry_lookup_by_method:
        baseline_lookup = entry_lookup_by_method[baseline_method]
        baseline_significant = significant_entities_by_method[baseline_method]
        for method in supported_methods:
            if method is baseline_method:
                continue
            compared_lookup = entry_lookup_by_method[method]
            compared_significant = significant_entities_by_method[method]
            for entity_id in sorted(set(baseline_lookup) | set(compared_lookup)):
                baseline_entry = baseline_lookup.get(entity_id)
                compared_entry = compared_lookup.get(entity_id)
                baseline_hit = entity_id in baseline_significant
                compared_hit = entity_id in compared_significant
                if baseline_hit == compared_hit:
                    continue
                changed_significance_entries.append(
                    ImputationSensitivityChangedSignificanceEntry(
                        entity_id=entity_id,
                        reference_method=baseline_method,
                        compared_method=method,
                        reference_significant=baseline_hit,
                        compared_significant=compared_hit,
                        reference_adjusted_p_value=(
                            None
                            if baseline_entry is None
                            else baseline_entry.adjusted_p_value
                        ),
                        compared_adjusted_p_value=(
                            None
                            if compared_entry is None
                            else compared_entry.adjusted_p_value
                        ),
                        reference_log2_fold_change=(
                            None
                            if baseline_entry is None
                            else baseline_entry.log2_fold_change
                        ),
                        compared_log2_fold_change=(
                            None
                            if compared_entry is None
                            else compared_entry.log2_fold_change
                        ),
                        note=(
                            "entity is significant only after imputation"
                            if compared_hit and not baseline_hit
                            else "entity loses significance after imputation comparison"
                        ),
                    )
                )
        imputation_only_entities: tuple[str, ...] = ()
        if policy_comparison is not None:
            imputation_only_entities = tuple(
                entry.entity_id
                for entry in policy_comparison.entries
                if entry.imputation_dependent
            )
        for entity_id in imputation_only_entities:
            supporting_methods = tuple(
                method
                for method in supported_methods
                if method is not baseline_method
                and entity_id in significant_entities_by_method[method]
            )
            best_method = min(
                supporting_methods,
                key=lambda method: (
                    entry_lookup_by_method[method][entity_id].adjusted_p_value
                    if entry_lookup_by_method[method][entity_id].adjusted_p_value
                    is not None
                    else 1.0,
                    -abs(entry_lookup_by_method[method][entity_id].log2_fold_change),
                    method.value,
                ),
            )
            baseline_entry = baseline_lookup.get(entity_id)
            best_entry = entry_lookup_by_method[best_method][entity_id]
            imputation_dependent_hits.append(
                ImputationDependentHitEntry(
                    entity_id=entity_id,
                    baseline_method=baseline_method,
                    imputation_methods=supporting_methods,
                    baseline_adjusted_p_value=(
                        None
                        if baseline_entry is None
                        else baseline_entry.adjusted_p_value
                    ),
                    best_imputation_method=best_method,
                    best_imputation_adjusted_p_value=best_entry.adjusted_p_value,
                    best_imputation_log2_fold_change=best_entry.log2_fold_change,
                    note="entity reaches significance only under one or more imputation policies",
                )
            )

    return ImputationSensitivityReport(
        condition_a=resolved_condition_a,
        condition_b=resolved_condition_b,
        baseline_method=baseline_method,
        significance_threshold=significance_threshold,
        entries=tuple(entries),
        overlap_entries=tuple(overlap_entries),
        changed_significance_entries=tuple(changed_significance_entries),
        imputation_dependent_hits=tuple(imputation_dependent_hits),
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
        provenance_lookup={
            (value.entity_id, value.sample_id): QuantCellImputationProvenance(
                method=ImputationMethod.LOW_INTENSITY,
                original_missing_value_kind=value.missing_value_kind,
                strategy="sample_low_intensity_floor",
                donor_sample_ids=(value.sample_id,),
            )
            for value in table.values
            if value.abundance is None
            and value.missing_value_kind
            in {MissingValueKind.NOT_OBSERVED, MissingValueKind.FILTERED}
        },
        method=ImputationMethod.LOW_INTENSITY,
    )


def _group_aware_low_intensity_imputed_table(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> LabelFreeQuantTable:
    """Impute with condition-aware low-intensity floors and explicit fallback scope."""
    if not design_entries:
        raise ValueError(
            "group-aware low-intensity imputation requires experimental design entries"
        )
    (
        matrix,
        sample_ids,
        _entity_ids,
        sample_index,
        _entity_index,
    ) = _table_grid(table)
    design_by_sample = {entry.sample_id: entry for entry in design_entries}
    missing_samples = set(table.sample_ids) - set(design_by_sample)
    if missing_samples:
        missing = ", ".join(sorted(missing_samples))
        raise ValueError(
            f"group-aware low-intensity imputation requires design rows for all samples: {missing}"
        )
    sample_fill_values = _sample_low_intensity_fill_values(
        matrix,
        sample_ids,
        sample_index,
    )
    condition_sample_id_lists: dict[str, list[str]] = {}
    for entry in design_entries:
        condition_sample_id_lists.setdefault(entry.condition, [])
        condition_sample_id_lists[entry.condition].append(entry.sample_id)
    condition_sample_ids: dict[str, tuple[str, ...]] = {
        condition: tuple(sample_ids)
        for condition, sample_ids in condition_sample_id_lists.items()
    }
    condition_fill_values = _condition_low_intensity_fill_values(
        matrix,
        condition_sample_ids=condition_sample_ids,
        sample_index=sample_index,
    )
    fill_lookup: dict[tuple[str, str], float] = {}
    provenance_lookup: dict[tuple[str, str], QuantCellImputationProvenance] = {}
    for value in table.values:
        if value.abundance is not None or value.missing_value_kind not in {
            MissingValueKind.NOT_OBSERVED,
            MissingValueKind.FILTERED,
        }:
            continue
        condition = design_by_sample[value.sample_id].condition
        donor_sample_ids = condition_sample_ids[condition]
        strategy = "condition_low_intensity_floor"
        fill_value = condition_fill_values[condition]
        condition_has_positive_signal = any(
            np.any(
                np.isfinite(matrix[:, sample_index[sample_id]])
                & (matrix[:, sample_index[sample_id]] > 0.0)
            )
            for sample_id in donor_sample_ids
        )
        if not condition_has_positive_signal:
            strategy = "sample_low_intensity_fallback"
            fill_value = sample_fill_values[value.sample_id]
            donor_sample_ids = (value.sample_id,)
        fill_lookup[(value.entity_id, value.sample_id)] = fill_value
        provenance_lookup[(value.entity_id, value.sample_id)] = (
            QuantCellImputationProvenance(
                method=ImputationMethod.GROUP_AWARE_LOW_INTENSITY,
                original_missing_value_kind=value.missing_value_kind,
                strategy=strategy,
                reference_group=condition,
                donor_sample_ids=tuple(sorted(donor_sample_ids)),
            )
        )
    return _rebuild_imputed_table(
        table,
        fill_lookup=fill_lookup,
        provenance_lookup=provenance_lookup,
        method=ImputationMethod.GROUP_AWARE_LOW_INTENSITY,
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
                [
                    matrix[entity_index[entity_id], col_index]
                    for entity_id, _ in neighbors
                ],
                dtype=float,
            )
            fill_lookup[(value.entity_id, value.sample_id)] = float(
                np.average(abundances, weights=weights)
            )
            continue
        fill_lookup[(value.entity_id, value.sample_id)] = sample_fill_values[
            value.sample_id
        ]
    provenance_lookup = {
        (value.entity_id, value.sample_id): _knn_cell_provenance(
            value=value,
            selected_neighbors=_select_knn_neighbors(
                matrix,
                entity_ids=entity_ids,
                target_row=entity_index[value.entity_id],
                target_col=sample_index[value.sample_id],
            ),
        )
        for value in table.values
        if value.abundance is None
        and value.missing_value_kind
        in {MissingValueKind.NOT_OBSERVED, MissingValueKind.FILTERED}
    }
    return _rebuild_imputed_table(
        table,
        fill_lookup=fill_lookup,
        provenance_lookup=provenance_lookup,
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


def _condition_low_intensity_fill_values(
    matrix: np.ndarray,
    *,
    condition_sample_ids: dict[str, tuple[str, ...]],
    sample_index: dict[str, int],
) -> dict[str, float]:
    finite_positive = matrix[np.isfinite(matrix) & (matrix > 0.0)]
    global_floor = (
        max(float(np.nanpercentile(finite_positive, 5.0)) * 0.5, 1e-6)
        if finite_positive.size
        else 1e-6
    )
    condition_fill_values: dict[str, float] = {}
    for condition, sample_ids in condition_sample_ids.items():
        columns = [matrix[:, sample_index[sample_id]] for sample_id in sample_ids]
        positives = np.concatenate(
            [column[np.isfinite(column) & (column > 0.0)] for column in columns]
        )
        if positives.size == 0:
            condition_fill_values[condition] = global_floor
            continue
        condition_fill_values[condition] = max(
            float(np.nanpercentile(positives, 5.0)) * 0.5,
            1e-6,
        )
    return condition_fill_values


def _rebuild_imputed_table(
    table: LabelFreeQuantTable,
    *,
    fill_lookup: dict[tuple[str, str], float],
    provenance_lookup: dict[tuple[str, str], QuantCellImputationProvenance],
    method: ImputationMethod,
) -> LabelFreeQuantTable:
    dense_matrix = quant_matrix_to_dense_array(table.to_quant_matrix())
    sample_index = {
        sample_id: index for index, sample_id in enumerate(table.sample_ids)
    }
    entity_index = {
        entity_id: index for index, entity_id in enumerate(table.entity_ids)
    }
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
        dense_matrix[
            entity_index[value.entity_id],
            sample_index[value.sample_id],
        ] = max(fill_value, 0.0)
        rebuilt_values.append(
            value.model_copy(
                update={
                    "abundance": max(fill_value, 0.0),
                    "missing_value_kind": MissingValueKind.IMPUTED,
                    "value_provenance": (
                        None
                        if value.value_provenance is None
                        else value.value_provenance.model_copy(
                            update={"value_origin": QuantValueOrigin.IMPUTED}
                        )
                    ),
                    "imputation_provenance": provenance_lookup[
                        (value.entity_id, value.sample_id)
                    ],
                }
            )
        )
    quant_matrix = rebuild_quant_matrix_from_dense_array(
        table.to_quant_matrix(),
        dense_matrix,
        transformation_step=f"imputation:{method.value}",
        metadata_updates={"imputation_method": method.value},
    ).model_copy(
        update={
            "matrix_id": build_matrix_id(
                table.entity_level.value,
                table.measure_kind.value,
                aggregation_method=table.aggregation_method.value,
                normalization_method=table.normalization_method.value,
                imputation_method=method.value,
            )
        }
    )
    return table.model_copy(
        update={
            "values": tuple(rebuilt_values),
            "quant_matrix": quant_matrix,
            "imputation_method": method,
        }
    )


def _knn_cell_provenance(
    *,
    value: QuantValue,
    selected_neighbors: tuple[tuple[str, float], ...],
) -> QuantCellImputationProvenance:
    if selected_neighbors:
        return QuantCellImputationProvenance(
            method=ImputationMethod.KNN,
            original_missing_value_kind=value.missing_value_kind,
            strategy="knn_profile_average",
            donor_sample_ids=(value.sample_id,),
            donor_entity_ids=tuple(entity_id for entity_id, _ in selected_neighbors),
        )
    return QuantCellImputationProvenance(
        method=ImputationMethod.KNN,
        original_missing_value_kind=value.missing_value_kind,
        strategy="sample_low_intensity_fallback",
        donor_sample_ids=(value.sample_id,),
    )


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
        raise ValueError(
            "before and after tables must cover the same sample/entity grid"
        )


__all__ = [
    "build_imputation_report",
    "build_imputation_sensitivity_report",
    "impute_label_free_table",
]
