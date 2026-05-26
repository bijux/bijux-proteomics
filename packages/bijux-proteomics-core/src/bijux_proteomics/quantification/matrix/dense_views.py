# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Dense NumPy-backed views over governed quantification tables."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from bijux_proteomics.quantification.contracts import (
    LabelFreeQuantTable,
    MissingValueKind,
)

_MISSING_VALUE_KIND_ORDER = (
    MissingValueKind.OBSERVED,
    MissingValueKind.ZERO,
    MissingValueKind.NOT_OBSERVED,
    MissingValueKind.FILTERED,
    MissingValueKind.IMPUTED,
    MissingValueKind.CENSORED,
    MissingValueKind.EXCLUDED,
    MissingValueKind.NOT_APPLICABLE,
)
_MISSING_VALUE_KIND_TO_CODE = {
    kind: code for code, kind in enumerate(_MISSING_VALUE_KIND_ORDER)
}
_MISSING_VALUE_CODE_TO_KIND = {
    code: kind for kind, code in _MISSING_VALUE_KIND_TO_CODE.items()
}


@dataclass(frozen=True)
class DenseLabelFreeQuantTableView:
    """Dense abundance and missing-kind matrices over one quant table."""

    entity_ids: tuple[str, ...]
    sample_ids: tuple[str, ...]
    abundance_matrix: np.ndarray
    log2_abundance_matrix: np.ndarray
    missing_kind_codes: np.ndarray
    entity_index: dict[str, int]
    sample_index: dict[str, int]


def build_dense_label_free_quant_table_view(
    table: LabelFreeQuantTable,
) -> DenseLabelFreeQuantTableView:
    """Build dense abundance and missing-kind matrices for one quant table."""

    entity_ids = tuple(table.entity_ids)
    sample_ids = tuple(table.sample_ids)
    entity_index = {entity_id: index for index, entity_id in enumerate(entity_ids)}
    sample_index = {sample_id: index for index, sample_id in enumerate(sample_ids)}
    abundance_matrix = np.full((len(entity_ids), len(sample_ids)), np.nan, dtype=float)
    missing_kind_codes = np.full(
        (len(entity_ids), len(sample_ids)),
        missing_value_kind_to_code(MissingValueKind.NOT_OBSERVED),
        dtype=np.int8,
    )
    for value in table.values:
        row_index = entity_index[value.entity_id]
        column_index = sample_index[value.sample_id]
        abundance_matrix[row_index, column_index] = (
            np.nan if value.abundance is None else float(value.abundance)
        )
        missing_kind_codes[row_index, column_index] = missing_value_kind_to_code(
            value.missing_value_kind
        )

    nonnegative_abundance = np.where(
        np.isnan(abundance_matrix),
        np.nan,
        np.maximum(abundance_matrix, 0.0),
    )
    log2_abundance_matrix = np.log2(nonnegative_abundance + 1.0)
    return DenseLabelFreeQuantTableView(
        entity_ids=entity_ids,
        sample_ids=sample_ids,
        abundance_matrix=abundance_matrix,
        log2_abundance_matrix=log2_abundance_matrix,
        missing_kind_codes=missing_kind_codes,
        entity_index=entity_index,
        sample_index=sample_index,
    )


def missing_value_kind_to_code(kind: MissingValueKind) -> int:
    """Convert one missing-value kind into its stable dense-code representation."""

    return _MISSING_VALUE_KIND_TO_CODE[kind]


def missing_value_code_to_kind(code: int) -> MissingValueKind:
    """Convert one stable dense-code representation into its missing-value kind."""

    return _MISSING_VALUE_CODE_TO_KIND[int(code)]


__all__ = [
    "DenseLabelFreeQuantTableView",
    "build_dense_label_free_quant_table_view",
    "missing_value_code_to_kind",
    "missing_value_kind_to_code",
]
