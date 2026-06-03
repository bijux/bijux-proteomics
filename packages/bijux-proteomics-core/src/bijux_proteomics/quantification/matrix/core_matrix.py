# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned helpers for canonical numeric quantification matrices."""

from __future__ import annotations

from collections.abc import Mapping
import math

import numpy as np

from bijux_proteomics.domain.records import (
    MissingValueState,
    QuantEntityKind,
    QuantMatrix,
    QuantMeasureKind,
    SampleMetadata,
)


def build_numeric_quant_matrix(
    *,
    matrix_id: str,
    entity_kind: QuantEntityKind,
    measure_kind: QuantMeasureKind,
    entity_ids: tuple[str, ...],
    sample_ids: tuple[str, ...],
    value_lookup: Mapping[tuple[str, str], float | None],
    missing_state_lookup: Mapping[tuple[str, str], MissingValueState],
    support_count_lookup: Mapping[tuple[str, str], int] | None = None,
    row_metadata_lookup: Mapping[str, Mapping[str, str]] | None = None,
    sample_metadata: tuple[SampleMetadata, ...] = (),
    transformation_history: tuple[str, ...] = (),
    metadata: Mapping[str, str] | None = None,
) -> QuantMatrix:
    """Build one canonical quant matrix from stable row/column lookups."""

    ordered_values: list[tuple[float | None, ...]] = []
    ordered_missing_states: list[tuple[MissingValueState, ...]] = []
    ordered_support_counts: list[tuple[int, ...]] = []
    ordered_row_metadata: list[dict[str, str]] = []
    for entity_id in entity_ids:
        row_values: list[float | None] = []
        row_states: list[MissingValueState] = []
        row_support_counts: list[int] = []
        for sample_id in sample_ids:
            key = (entity_id, sample_id)
            row_values.append(value_lookup.get(key))
            row_states.append(
                missing_state_lookup.get(key, MissingValueState.NOT_OBSERVED)
            )
            row_support_counts.append(
                0
                if support_count_lookup is None
                else int(support_count_lookup.get(key, 0))
            )
        ordered_values.append(tuple(row_values))
        ordered_missing_states.append(tuple(row_states))
        ordered_support_counts.append(tuple(row_support_counts))
        if row_metadata_lookup is not None:
            ordered_row_metadata.append(dict(row_metadata_lookup.get(entity_id, {})))
    return QuantMatrix(
        matrix_id=matrix_id,
        entity_kind=entity_kind,
        measure_kind=measure_kind,
        entity_ids=entity_ids,
        sample_ids=sample_ids,
        values=tuple(ordered_values),
        missing_value_states=tuple(ordered_missing_states),
        support_counts=tuple(ordered_support_counts),
        row_metadata=tuple(ordered_row_metadata),
        sample_metadata=sample_metadata,
        transformation_history=transformation_history,
        metadata={} if metadata is None else dict(metadata),
    )


def iter_quant_matrix_cells(
    matrix: QuantMatrix,
) -> tuple[tuple[str, str, float | None, MissingValueState], ...]:
    """Return one stable entity/sample traversal over all matrix cells."""

    rows: list[tuple[str, str, float | None, MissingValueState]] = []
    for row_index, entity_id in enumerate(matrix.entity_ids):
        for column_index, sample_id in enumerate(matrix.sample_ids):
            rows.append(
                (
                    entity_id,
                    sample_id,
                    matrix.values[row_index][column_index],
                    matrix.missing_value_states[row_index][column_index],
                )
            )
    return tuple(rows)


def quant_matrix_to_dense_array(matrix: QuantMatrix) -> np.ndarray:
    """Convert one canonical quant matrix into an `np.nan`-aware dense array."""

    return np.array(
        [
            [np.nan if value is None else float(value) for value in row_values]
            for row_values in matrix.values
        ],
        dtype=float,
    )


def rebuild_quant_matrix_from_dense_array(
    matrix: QuantMatrix,
    dense_values: np.ndarray,
    *,
    transformation_step: str | None = None,
    metadata_updates: Mapping[str, str] | None = None,
) -> QuantMatrix:
    """Rebuild one canonical matrix from a shape-aligned dense numeric array."""

    expected_shape = (len(matrix.entity_ids), len(matrix.sample_ids))
    if dense_values.shape != expected_shape:
        raise ValueError("dense_values shape must match the quant matrix grid")

    rebuilt_rows: list[tuple[float | None, ...]] = []
    for row_index in range(dense_values.shape[0]):
        rebuilt_row: list[float | None] = []
        for column_index in range(dense_values.shape[1]):
            value = float(dense_values[row_index, column_index])
            rebuilt_row.append(None if math.isnan(value) else value)
        rebuilt_rows.append(tuple(rebuilt_row))
    history = matrix.transformation_history
    if transformation_step:
        history = (*history, transformation_step)
    merged_metadata = dict(matrix.metadata)
    if metadata_updates:
        merged_metadata.update(metadata_updates)
    return matrix.model_copy(
        update={
            "values": tuple(rebuilt_rows),
            "transformation_history": history,
            "metadata": merged_metadata,
        }
    )


__all__ = [
    "build_numeric_quant_matrix",
    "iter_quant_matrix_cells",
    "quant_matrix_to_dense_array",
    "rebuild_quant_matrix_from_dense_array",
]
