# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Observation-vector collection for differential abundance analysis."""

from __future__ import annotations

from collections.abc import Mapping
import math

import numpy as np

from bijux_proteomics.quantification.contracts.input_models import MissingValueKind
from bijux_proteomics.quantification.contracts.matrix_models import QuantValue
from bijux_proteomics.quantification.matrix import missing_value_kind_to_code


def collect_condition_values(
    lookup: Mapping[tuple[str, str], QuantValue],
    entity_id: str,
    sample_ids: tuple[str, ...],
    *,
    sample_weights: dict[str, float] | None = None,
) -> tuple[np.ndarray, np.ndarray, dict[MissingValueKind, int]]:
    """Collect log2 values, weights, and missingness counts for one condition."""

    values: list[float] = []
    weights: list[float] = []
    counts = {
        MissingValueKind.ZERO: 0,
        MissingValueKind.NOT_OBSERVED: 0,
        MissingValueKind.FILTERED: 0,
    }
    for sample_id in sample_ids:
        cell = lookup.get((entity_id, sample_id))
        if cell is None:
            counts[MissingValueKind.NOT_OBSERVED] += 1
            continue
        if cell.missing_value_kind is MissingValueKind.ZERO:
            counts[MissingValueKind.ZERO] += 1
        elif cell.missing_value_kind is MissingValueKind.NOT_OBSERVED:
            counts[MissingValueKind.NOT_OBSERVED] += 1
        elif cell.missing_value_kind is MissingValueKind.FILTERED:
            counts[MissingValueKind.FILTERED] += 1
        if cell.abundance is not None:
            values.append(math.log2(cell.abundance + 1.0))
            weights.append(
                1.0
                if sample_weights is None
                else float(sample_weights.get(sample_id, 1.0))
            )
    return np.array(values, dtype=float), np.array(weights, dtype=float), counts


def collect_condition_values_vectorized(
    entity_log2_abundance: np.ndarray,
    entity_missing_kind_codes: np.ndarray,
    sample_indexes: np.ndarray,
    *,
    sample_weight_vector: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, dict[MissingValueKind, int]]:
    """Collect log2 values, weights, and missingness counts from dense vectors."""

    selected_log2_abundance = entity_log2_abundance[sample_indexes]
    selected_missing_kind_codes = entity_missing_kind_codes[sample_indexes]
    finite_mask = np.isfinite(selected_log2_abundance)
    counts = {
        MissingValueKind.ZERO: int(
            np.sum(
                selected_missing_kind_codes
                == missing_value_kind_to_code(MissingValueKind.ZERO)
            )
        ),
        MissingValueKind.NOT_OBSERVED: int(
            np.sum(
                selected_missing_kind_codes
                == missing_value_kind_to_code(MissingValueKind.NOT_OBSERVED)
            )
        ),
        MissingValueKind.FILTERED: int(
            np.sum(
                selected_missing_kind_codes
                == missing_value_kind_to_code(MissingValueKind.FILTERED)
            )
        ),
    }
    return (
        selected_log2_abundance[finite_mask],
        sample_weight_vector[sample_indexes][finite_mask],
        counts,
    )


__all__ = [
    "collect_condition_values",
    "collect_condition_values_vectorized",
]
