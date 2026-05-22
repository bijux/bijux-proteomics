# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned sample-level exploratory analysis over governed quantification tables."""

from __future__ import annotations

import math

import numpy as np

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import (
    ConditionClusteringReport,
    LabelFreeQuantTable,
    SamplePcaEntry,
    SamplePcaReport,
    _condition_lookup,
    _matrix_value_index,
)


def build_sample_pca_report(
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> SamplePcaReport:
    """Project samples into a compact principal-component exploratory space."""

    sample_ids = tuple(table.sample_ids)
    condition_by_sample = _condition_lookup(design_entries)
    batch_by_sample = {entry.sample_id: entry.batch for entry in design_entries}
    matrix = build_sample_feature_matrix(table)
    centered = matrix - np.mean(matrix, axis=0, keepdims=True)
    if centered.shape[0] < 2 or centered.shape[1] == 0:
        return SamplePcaReport(
            entity_level=table.entity_level,
            explained_variance_ratio_pc1=0.0,
            explained_variance_ratio_pc2=0.0,
            entries=tuple(
                SamplePcaEntry(
                    sample_id=sample_id,
                    condition=condition_by_sample.get(sample_id, "unknown"),
                    batch=batch_by_sample.get(sample_id),
                    pc1=0.0,
                    pc2=0.0,
                    distance_from_global_centroid=0.0,
                    distance_from_condition_centroid=0.0,
                    outlier=False,
                )
                for sample_id in sample_ids
            ),
            note=(
                "pca was not informative because fewer than two samples or features were available"
            ),
        )
    u, singular_values, _ = np.linalg.svd(centered, full_matrices=False)
    scores = u * singular_values
    eigenvalues = np.square(singular_values)
    total_variance = float(np.sum(eigenvalues))
    for component in range(min(2, scores.shape[1])):
        nonzero = next(
            (value for value in scores[:, component] if abs(float(value)) > 1e-12),
            None,
        )
        if nonzero is not None and nonzero < 0.0:
            scores[:, component] *= -1.0
    pc1 = scores[:, 0] if scores.shape[1] >= 1 else np.zeros(len(sample_ids))
    pc2 = scores[:, 1] if scores.shape[1] >= 2 else np.zeros(len(sample_ids))
    coordinates = np.column_stack((pc1, pc2))
    global_distances = np.linalg.norm(coordinates, axis=1)
    global_threshold = distance_outlier_threshold(global_distances)
    condition_thresholds: dict[str, float] = {}
    condition_distances_by_sample: dict[str, float] = {}
    entries: list[SamplePcaEntry] = []
    for condition in sorted(set(condition_by_sample.values())):
        same_condition_indexes = np.array(
            [
                index
                for index, sample_id in enumerate(sample_ids)
                if condition_by_sample.get(sample_id, "unknown") == condition
            ],
            dtype=int,
        )
        if same_condition_indexes.size <= 1:
            condition_thresholds[condition] = 0.0
            continue
        centroid = np.mean(coordinates[same_condition_indexes, :], axis=0)
        condition_distances = np.linalg.norm(
            coordinates[same_condition_indexes, :] - centroid,
            axis=1,
        )
        condition_thresholds[condition] = distance_outlier_threshold(
            condition_distances
        )
        for offset, sample_index in enumerate(same_condition_indexes):
            condition_distances_by_sample[sample_ids[sample_index]] = float(
                condition_distances[offset]
            )
    for index, sample_id in enumerate(sample_ids):
        condition = condition_by_sample.get(sample_id, "unknown")
        condition_distance = condition_distances_by_sample.get(sample_id, 0.0)
        outlier = (
            float(global_distances[index]) > global_threshold
            or condition_distance > condition_thresholds.get(condition, 0.0)
        )
        entries.append(
            SamplePcaEntry(
                sample_id=sample_id,
                condition=condition,
                batch=batch_by_sample.get(sample_id),
                pc1=float(pc1[index]),
                pc2=float(pc2[index]),
                distance_from_global_centroid=float(global_distances[index]),
                distance_from_condition_centroid=condition_distance,
                outlier=outlier,
            )
        )
    note = (
        "pca detected one or more sample profiles that sit far from the study centroid"
        if any(entry.outlier for entry in entries)
        else "pca did not detect sample profiles that sit far from the study centroid"
    )
    return SamplePcaReport(
        entity_level=table.entity_level,
        explained_variance_ratio_pc1=(
            float(eigenvalues[0] / total_variance)
            if total_variance > 0.0 and eigenvalues.size >= 1
            else 0.0
        ),
        explained_variance_ratio_pc2=(
            float(eigenvalues[1] / total_variance)
            if total_variance > 0.0 and eigenvalues.size >= 2
            else 0.0
        ),
        entries=tuple(entries),
        note=note,
    )


def build_condition_clustering_report(
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> ConditionClusteringReport:
    """Summarize whether nearby samples cluster by biological condition."""

    pca_report = build_sample_pca_report(table, design_entries)
    if len(pca_report.entries) < 2:
        return ConditionClusteringReport(
            entity_level=table.entity_level,
            condition_count=0,
            nearest_same_condition_fraction=0.0,
            mean_within_condition_distance=None,
            mean_between_condition_distance=None,
            clustered_by_condition=False,
            note=(
                "condition clustering was not informative because fewer than two samples were available"
            ),
        )
    within_distances: list[float] = []
    between_distances: list[float] = []
    nearest_same_condition_count = 0
    entries = list(pca_report.entries)
    for index, entry in enumerate(entries):
        nearest_distance: float | None = None
        nearest_same_condition = False
        for other_index, other_entry in enumerate(entries):
            if index == other_index:
                continue
            distance = float(
                np.linalg.norm(
                    np.array((entry.pc1, entry.pc2), dtype=float)
                    - np.array((other_entry.pc1, other_entry.pc2), dtype=float)
                )
            )
            if entry.condition == other_entry.condition:
                within_distances.append(distance)
            else:
                between_distances.append(distance)
            if nearest_distance is None or distance < nearest_distance:
                nearest_distance = distance
                nearest_same_condition = entry.condition == other_entry.condition
        nearest_same_condition_count += int(nearest_same_condition)
    condition_count = len({entry.condition for entry in entries})
    nearest_same_fraction = nearest_same_condition_count / len(entries)
    mean_within = float(np.mean(within_distances)) if within_distances else None
    mean_between = float(np.mean(between_distances)) if between_distances else None
    clustered = (
        mean_within is not None
        and mean_between is not None
        and mean_within < mean_between
        and nearest_same_fraction >= 0.75
    )
    note = (
        "sample neighborhoods cluster by biological condition in the current qc space"
        if clustered
        else "sample neighborhoods do not separate cleanly by biological condition in the current qc space"
    )
    return ConditionClusteringReport(
        entity_level=table.entity_level,
        condition_count=condition_count,
        nearest_same_condition_fraction=nearest_same_fraction,
        mean_within_condition_distance=mean_within,
        mean_between_condition_distance=mean_between,
        clustered_by_condition=clustered,
        note=note,
    )


def build_sample_feature_matrix(table: LabelFreeQuantTable) -> np.ndarray:
    """Build one log2 sample-by-feature matrix with median-filled missing cells."""

    lookup = _matrix_value_index(table)
    matrix = np.full((len(table.sample_ids), len(table.entity_ids)), np.nan, dtype=float)
    for sample_index, sample_id in enumerate(table.sample_ids):
        for entity_index, entity_id in enumerate(table.entity_ids):
            abundance = lookup[(entity_id, sample_id)].abundance
            if abundance is None:
                continue
            matrix[sample_index, entity_index] = math.log2(float(abundance) + 1.0)
    for entity_index in range(matrix.shape[1]):
        column = matrix[:, entity_index]
        finite = column[np.isfinite(column)]
        fill_value = float(np.median(finite)) if finite.size else 0.0
        missing = ~np.isfinite(column)
        column[missing] = fill_value
        matrix[:, entity_index] = column
    return matrix


def distance_outlier_threshold(distances: np.ndarray) -> float:
    """Derive a robust outlier threshold from one distance vector."""

    if distances.size == 0:
        return 0.0
    median = float(np.median(distances))
    mad = float(np.median(np.abs(distances - median)))
    if mad == 0.0:
        return median + 1e-6
    return median + 2.0 * mad


__all__ = [
    "build_condition_clustering_report",
    "build_sample_feature_matrix",
    "build_sample_pca_report",
    "distance_outlier_threshold",
]
