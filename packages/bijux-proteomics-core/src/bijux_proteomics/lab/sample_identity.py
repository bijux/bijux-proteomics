# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Laboratory-facing sample-identity and swap-suspicion surfaces."""

from __future__ import annotations

import csv
from io import StringIO

import numpy as np
from pydantic import ConfigDict, Field

from bijux_proteomics.domain.records import MissingValueState, QuantMatrix
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics_foundation import JsonModel


class SampleSwapSuspicionEntry(JsonModel):
    """One sample-level sample-swap suspicion row."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    expected_group: str = Field(..., min_length=1)
    nearest_neighbor_sample: str = Field(..., min_length=1)
    nearest_neighbor_group: str = Field(..., min_length=1)
    swap_suspicion_score: float = Field(..., ge=0.0, le=1.0)


def detect_sample_swaps(
    matrix: QuantMatrix,
    metadata: tuple[ExperimentalDesignEntry, ...],
    *,
    minimum_shared_entities: int = 3,
) -> tuple[SampleSwapSuspicionEntry, ...]:
    """Report sample-swap suspicion from declared groups and nearest neighbors."""

    if len(matrix.sample_ids) < 2:
        raise ValueError("sample swap detection requires at least two samples")
    if minimum_shared_entities < 2:
        raise ValueError("minimum_shared_entities must be at least two")

    metadata_by_sample: dict[str, ExperimentalDesignEntry] = {}
    for entry in metadata:
        if entry.sample_id in metadata_by_sample:
            raise ValueError(
                "sample swap detection requires unique metadata sample_id rows"
            )
        metadata_by_sample[entry.sample_id] = entry
    missing_metadata = tuple(
        sample_id
        for sample_id in matrix.sample_ids
        if sample_id not in metadata_by_sample
    )
    if missing_metadata:
        raise ValueError(
            "sample swap detection requires metadata for all matrix.sample_ids: "
            + ", ".join(missing_metadata)
        )

    rows: list[SampleSwapSuspicionEntry] = []
    for sample_id in sorted(matrix.sample_ids):
        nearest_neighbor_sample, similarity = _nearest_neighbor(
            matrix,
            sample_id=sample_id,
            minimum_shared_entities=minimum_shared_entities,
        )
        expected_group = metadata_by_sample[sample_id].condition
        nearest_neighbor_group = metadata_by_sample[nearest_neighbor_sample].condition
        rows.append(
            SampleSwapSuspicionEntry(
                sample_id=sample_id,
                expected_group=expected_group,
                nearest_neighbor_sample=nearest_neighbor_sample,
                nearest_neighbor_group=nearest_neighbor_group,
                swap_suspicion_score=round(
                    _swap_suspicion_score(
                        expected_group=expected_group,
                        nearest_neighbor_group=nearest_neighbor_group,
                        similarity=similarity,
                    ),
                    4,
                ),
            )
        )
    return tuple(rows)


def render_sample_swap_suspicion_tsv(
    entries: tuple[SampleSwapSuspicionEntry, ...],
) -> str:
    """Render sample-swap suspicion rows as a stable TSV table."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "sample_id",
            "expected_group",
            "nearest_neighbor_sample",
            "nearest_neighbor_group",
            "swap_suspicion_score",
        )
    )
    for entry in entries:
        writer.writerow(
            (
                entry.sample_id,
                entry.expected_group,
                entry.nearest_neighbor_sample,
                entry.nearest_neighbor_group,
                f"{entry.swap_suspicion_score:.4f}",
            )
        )
    return buffer.getvalue()


def _nearest_neighbor(
    matrix: QuantMatrix,
    *,
    sample_id: str,
    minimum_shared_entities: int,
) -> tuple[str, float]:
    source_index = matrix.sample_ids.index(sample_id)
    best_neighbor: str | None = None
    best_similarity = float("-inf")
    for candidate_index, candidate_sample_id in enumerate(matrix.sample_ids):
        if candidate_sample_id == sample_id:
            continue
        similarity = _pairwise_similarity(
            matrix,
            left_index=source_index,
            right_index=candidate_index,
            minimum_shared_entities=minimum_shared_entities,
        )
        if (
            similarity > best_similarity
            or (
                similarity == best_similarity
                and best_neighbor is not None
                and candidate_sample_id < best_neighbor
            )
            or best_neighbor is None
        ):
            best_neighbor = candidate_sample_id
            best_similarity = similarity
    if best_neighbor is None:
        raise ValueError("sample swap detection requires at least two distinct samples")
    return best_neighbor, max(min(best_similarity, 1.0), -1.0)


def _pairwise_similarity(
    matrix: QuantMatrix,
    *,
    left_index: int,
    right_index: int,
    minimum_shared_entities: int,
) -> float:
    shared_left: list[float] = []
    shared_right: list[float] = []
    for entity_index in range(len(matrix.entity_ids)):
        left_value, left_observed = _observed_value(matrix, entity_index, left_index)
        right_value, right_observed = _observed_value(matrix, entity_index, right_index)
        if left_observed and right_observed:
            shared_left.append(left_value)
            shared_right.append(right_value)
    if len(shared_left) < minimum_shared_entities:
        return -1.0
    correlation = float(
        np.corrcoef(np.array(shared_left), np.array(shared_right))[0, 1]
    )
    if not np.isfinite(correlation):
        return -1.0
    return correlation


def _observed_value(
    matrix: QuantMatrix,
    entity_index: int,
    sample_index: int,
) -> tuple[float, bool]:
    state = matrix.missing_value_states[entity_index][sample_index]
    value = matrix.values[entity_index][sample_index]
    if state is MissingValueState.OBSERVED and value is not None:
        return float(value), True
    if state is MissingValueState.ZERO:
        return 0.0, True
    return 0.0, False


def _swap_suspicion_score(
    *,
    expected_group: str,
    nearest_neighbor_group: str,
    similarity: float,
) -> float:
    bounded_similarity = max(min(similarity, 1.0), -1.0)
    similarity_signal = (bounded_similarity + 1.0) / 2.0
    if nearest_neighbor_group == expected_group:
        return max(0.0, 0.35 * (1.0 - similarity_signal))
    return min(1.0, 0.55 + 0.45 * similarity_signal)


__all__ = [
    "SampleSwapSuspicionEntry",
    "detect_sample_swaps",
    "render_sample_swap_suspicion_tsv",
]
