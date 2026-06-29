# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Pairwise sample topology review over governed quantification tables."""

from __future__ import annotations

from collections.abc import Sequence
import math

import numpy as np

from bijux_proteomics.domain.records import QuantMatrix as CanonicalQuantMatrix
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts.matrix_building import (
    coerce_label_free_quant_table,
)
from bijux_proteomics.quantification.contracts.matrix_models import LabelFreeQuantTable
from bijux_proteomics.quantification.provenance.sample_exploration.models import (
    SampleClusterEntry,
    SampleClusterReport,
    SampleClusterState,
    SampleCorrelationEntry,
    SampleCorrelationReport,
    SampleDistanceEntry,
    SampleDistanceReport,
)
from bijux_proteomics.quantification.provenance.sample_exploration.sample_space import (
    build_sample_space_decomposition,
)


def build_sample_distance_report(
    table: LabelFreeQuantTable | CanonicalQuantMatrix,
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> SampleDistanceReport:
    """Compute pairwise sample distances in centered feature space."""

    table = coerce_label_free_quant_table(table)
    decomposition = build_sample_space_decomposition(table, design_entries)
    entries: list[SampleDistanceEntry] = []
    for left_index in range(len(decomposition.sample_ids)):
        for right_index in range(left_index + 1, len(decomposition.sample_ids)):
            left_sample_id = decomposition.sample_ids[left_index]
            right_sample_id = decomposition.sample_ids[right_index]
            entries.append(
                SampleDistanceEntry(
                    sample_id_a=left_sample_id,
                    sample_id_b=right_sample_id,
                    condition_a=decomposition.condition_by_sample.get(
                        left_sample_id, "unknown"
                    ),
                    condition_b=decomposition.condition_by_sample.get(
                        right_sample_id, "unknown"
                    ),
                    batch_a=decomposition.batch_by_sample.get(left_sample_id),
                    batch_b=decomposition.batch_by_sample.get(right_sample_id),
                    euclidean_distance=float(
                        np.linalg.norm(
                            decomposition.centered_matrix[left_index, :]
                            - decomposition.centered_matrix[right_index, :]
                        )
                    ),
                    same_condition=(
                        decomposition.condition_by_sample.get(left_sample_id, "unknown")
                        == decomposition.condition_by_sample.get(
                            right_sample_id, "unknown"
                        )
                    ),
                    same_batch=decomposition.batch_by_sample.get(left_sample_id)
                    == decomposition.batch_by_sample.get(right_sample_id),
                )
            )
    entries.sort(
        key=lambda entry: (
            entry.euclidean_distance,
            entry.sample_id_a,
            entry.sample_id_b,
        )
    )
    return SampleDistanceReport(
        entity_level=table.entity_level,
        sample_count=len(decomposition.sample_ids),
        entries=tuple(entries),
        note=(
            "sample distances preserve pairwise euclidean separation across the centered study feature space"
        ),
    )


def build_sample_correlation_report(
    table: LabelFreeQuantTable | CanonicalQuantMatrix,
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> SampleCorrelationReport:
    """Compute pairwise sample correlations across the filled feature matrix."""

    table = coerce_label_free_quant_table(table)
    decomposition = build_sample_space_decomposition(table, design_entries)
    entries: list[SampleCorrelationEntry] = []
    for left_index in range(len(decomposition.sample_ids)):
        for right_index in range(left_index + 1, len(decomposition.sample_ids)):
            left_sample_id = decomposition.sample_ids[left_index]
            right_sample_id = decomposition.sample_ids[right_index]
            correlation = safe_sample_correlation(
                decomposition.matrix[left_index, :],
                decomposition.matrix[right_index, :],
            )
            entries.append(
                SampleCorrelationEntry(
                    sample_id_a=left_sample_id,
                    sample_id_b=right_sample_id,
                    condition_a=decomposition.condition_by_sample.get(
                        left_sample_id, "unknown"
                    ),
                    condition_b=decomposition.condition_by_sample.get(
                        right_sample_id, "unknown"
                    ),
                    batch_a=decomposition.batch_by_sample.get(left_sample_id),
                    batch_b=decomposition.batch_by_sample.get(right_sample_id),
                    pearson_correlation=correlation,
                    same_condition=(
                        decomposition.condition_by_sample.get(left_sample_id, "unknown")
                        == decomposition.condition_by_sample.get(
                            right_sample_id, "unknown"
                        )
                    ),
                    same_batch=decomposition.batch_by_sample.get(left_sample_id)
                    == decomposition.batch_by_sample.get(right_sample_id),
                )
            )
    entries.sort(
        key=lambda entry: (
            -entry.pearson_correlation,
            entry.sample_id_a,
            entry.sample_id_b,
        )
    )
    return SampleCorrelationReport(
        entity_level=table.entity_level,
        sample_count=len(decomposition.sample_ids),
        entries=tuple(entries),
        note=(
            "sample correlations preserve pairwise pearson agreement across the filled study feature matrix"
        ),
    )


def build_sample_cluster_report(
    table: LabelFreeQuantTable | CanonicalQuantMatrix,
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> SampleClusterReport:
    """Build a deterministic average-linkage sample cluster table."""

    table = coerce_label_free_quant_table(table)
    decomposition = build_sample_space_decomposition(table, design_entries)
    if len(decomposition.sample_ids) < 2:
        return SampleClusterReport(
            entity_level=table.entity_level,
            sample_count=len(decomposition.sample_ids),
            entries=(),
            note=(
                "sample clustering was not informative because fewer than two samples were available"
            ),
        )
    distance_matrix = pairwise_distance_matrix(decomposition.centered_matrix)
    active_clusters = [
        SampleClusterState(member_indexes=(index,))
        for index in range(len(decomposition.sample_ids))
    ]
    entries: list[SampleClusterEntry] = []
    merge_order = 1
    while len(active_clusters) > 1:
        best_pair: tuple[int, int] | None = None
        best_distance: float | None = None
        best_key: tuple[str, str] | None = None
        for left_index in range(len(active_clusters)):
            for right_index in range(left_index + 1, len(active_clusters)):
                left_cluster = active_clusters[left_index]
                right_cluster = active_clusters[right_index]
                distance = average_linkage_distance(
                    distance_matrix,
                    left_cluster.member_indexes,
                    right_cluster.member_indexes,
                )
                left_key = cluster_member_key(
                    decomposition.sample_ids,
                    left_cluster.member_indexes,
                )
                right_key = cluster_member_key(
                    decomposition.sample_ids,
                    right_cluster.member_indexes,
                )
                candidate_key = (left_key, right_key)
                if (
                    best_distance is None
                    or distance < best_distance
                    or (
                        math.isclose(
                            distance, best_distance, rel_tol=0.0, abs_tol=1e-12
                        )
                        and candidate_key < (best_key or ("", ""))
                    )
                ):
                    best_pair = (left_index, right_index)
                    best_distance = distance
                    best_key = candidate_key
        if best_pair is None:
            raise RuntimeError(
                "sample exploration clustering could not select a pair despite multiple active clusters"
            )
        if best_distance is None:
            raise RuntimeError(
                "sample exploration clustering selected a pair without a linkage distance"
            )
        left_cluster = active_clusters[best_pair[0]]
        right_cluster = active_clusters[best_pair[1]]
        merged_indexes = tuple(
            sorted((*left_cluster.member_indexes, *right_cluster.member_indexes))
        )
        entries.append(
            SampleClusterEntry(
                merge_order=merge_order,
                member_sample_ids=tuple(
                    decomposition.sample_ids[index] for index in merged_indexes
                ),
                left_sample_ids=tuple(
                    decomposition.sample_ids[index]
                    for index in left_cluster.member_indexes
                ),
                right_sample_ids=tuple(
                    decomposition.sample_ids[index]
                    for index in right_cluster.member_indexes
                ),
                member_conditions=tuple(
                    sorted(
                        {
                            decomposition.condition_by_sample.get(
                                decomposition.sample_ids[index], "unknown"
                            )
                            for index in merged_indexes
                        }
                    )
                ),
                member_batches=tuple(
                    sorted(
                        {
                            batch
                            for batch in (
                                decomposition.batch_by_sample.get(
                                    decomposition.sample_ids[index]
                                )
                                for index in merged_indexes
                            )
                            if batch is not None
                        }
                    )
                ),
                member_count=len(merged_indexes),
                average_linkage_distance=float(best_distance),
            )
        )
        merge_order += 1
        next_clusters: list[SampleClusterState] = []
        for index, cluster in enumerate(active_clusters):
            if index not in best_pair:
                next_clusters.append(cluster)
        next_clusters.append(SampleClusterState(member_indexes=merged_indexes))
        active_clusters = sorted(
            next_clusters,
            key=lambda cluster: cluster_member_key(
                decomposition.sample_ids,
                cluster.member_indexes,
            ),
        )
    return SampleClusterReport(
        entity_level=table.entity_level,
        sample_count=len(decomposition.sample_ids),
        entries=tuple(entries),
        note=(
            "sample clustering preserves deterministic average-linkage merge steps over the centered study feature space"
        ),
    )


def pairwise_distance_matrix(matrix: np.ndarray) -> np.ndarray:
    """Build the symmetric pairwise distance matrix over one sample feature space."""

    sample_count = matrix.shape[0]
    distances = np.zeros((sample_count, sample_count), dtype=float)
    for left_index in range(sample_count):
        for right_index in range(left_index + 1, sample_count):
            distance = float(
                np.linalg.norm(matrix[left_index, :] - matrix[right_index, :])
            )
            distances[left_index, right_index] = distance
            distances[right_index, left_index] = distance
    return distances


def safe_sample_correlation(left: np.ndarray, right: np.ndarray) -> float:
    """Return one bounded correlation value even for degenerate sample vectors."""

    left_std = float(np.std(left))
    right_std = float(np.std(right))
    if left_std <= 0.0 or right_std <= 0.0:
        return 1.0 if np.allclose(left, right) else 0.0
    correlation = float(np.corrcoef(left, right)[0, 1])
    if not math.isfinite(correlation):
        return 0.0
    return max(-1.0, min(1.0, correlation))


def average_linkage_distance(
    distance_matrix: np.ndarray,
    left_indexes: Sequence[int],
    right_indexes: Sequence[int],
) -> float:
    """Compute mean between-cluster distance over two sample index groups."""

    distances = [
        float(distance_matrix[left_index, right_index])
        for left_index in left_indexes
        for right_index in right_indexes
    ]
    return float(np.mean(distances)) if distances else 0.0


def cluster_member_key(sample_ids: tuple[str, ...], member_indexes: Sequence[int]) -> str:
    """Build a deterministic cluster identity key from owned sample ordering."""

    return ";".join(sample_ids[index] for index in member_indexes)


__all__ = [
    "average_linkage_distance",
    "build_sample_cluster_report",
    "build_sample_correlation_report",
    "build_sample_distance_report",
    "cluster_member_key",
    "pairwise_distance_matrix",
    "safe_sample_correlation",
]
