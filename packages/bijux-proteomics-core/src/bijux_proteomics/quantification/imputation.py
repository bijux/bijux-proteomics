# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned missing-value imputation for quantitative proteomics tables."""

from __future__ import annotations

import numpy as np

from bijux_proteomics.quantification.contracts import (
    ImputationEntry,
    ImputationMethod,
    ImputationReport,
    LabelFreeQuantTable,
    MissingValueKind,
    QuantMeasureKind,
    QuantValue,
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
            entries.append(
                ImputationEntry(
                    entity_id=value.entity_id,
                    sample_id=value.sample_id,
                    original_missing_value_kind=prior.missing_value_kind,
                    imputed_abundance=float(value.abundance),
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
    raise ValueError(f"unsupported imputation method: {method.value}")


def _low_intensity_imputed_table(table: LabelFreeQuantTable) -> LabelFreeQuantTable:
    """Impute absent low-signal intensities from the lower tail of each sample."""
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
        fill_value = sample_fill_values[value.sample_id]
        rebuilt_values.append(
            value.model_copy(update={"abundance": max(fill_value, 0.0)})
        )
    return table.model_copy(
        update={
            "values": tuple(rebuilt_values),
            "imputation_method": ImputationMethod.LOW_INTENSITY,
        }
    )


def _validate_imputation_pair(
    before: LabelFreeQuantTable,
    after: LabelFreeQuantTable,
) -> None:
    if before.sample_ids != after.sample_ids or before.entity_ids != after.entity_ids:
        raise ValueError("before and after tables must cover the same sample/entity grid")


__all__ = [
    "build_imputation_report",
    "impute_label_free_table",
]
