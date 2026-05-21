# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned replicate-consistency and batch-aware QC surfaces."""

from __future__ import annotations

import math

import numpy as np

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import (
    ConditionClusteringReport,
    LabelFreeQuantTable,
    QcOutlierSampleEntry,
    ReplicateAndBatchQcReport,
    ReplicateCvConditionEntry,
    ReplicateCvReport,
    SamplePcaEntry,
    SamplePcaReport,
    build_batch_effect_advisory,
    build_replicate_correlation_report,
    _condition_lookup,
    _matrix_value_index,
)


def build_replicate_cv_report(
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    high_cv_threshold: float = 0.3,
) -> ReplicateCvReport:
    """Summarize within-condition replicate spread using entity-level CV."""
    condition_by_sample = _condition_lookup(design_entries)
    sample_ids_by_condition: dict[str, list[str]] = {}
    for sample_id in table.sample_ids:
        condition = condition_by_sample.get(sample_id)
        if condition:
            sample_ids_by_condition.setdefault(condition, []).append(sample_id)
    lookup = _matrix_value_index(table)
    entries: list[ReplicateCvConditionEntry] = []
    for condition in sorted(sample_ids_by_condition):
        sample_ids = tuple(sample_ids_by_condition[condition])
        entity_cvs: list[float] = []
        for entity_id in table.entity_ids:
            abundances = np.array(
                [
                    float(cell.abundance)
                    for sample_id in sample_ids
                    if (cell := lookup[(entity_id, sample_id)]).abundance is not None
                ],
                dtype=float,
            )
            if abundances.size < 2:
                continue
            mean_abundance = float(np.mean(abundances))
            if mean_abundance <= 0.0:
                continue
            cv = float(np.std(abundances, ddof=1) / mean_abundance)
            if math.isfinite(cv):
                entity_cvs.append(cv)
        high_cv_entity_count = sum(cv > high_cv_threshold for cv in entity_cvs)
        median_cv = float(np.median(entity_cvs)) if entity_cvs else None
        entries.append(
            ReplicateCvConditionEntry(
                condition=condition,
                replicate_count=len(sample_ids),
                evaluated_entity_count=len(entity_cvs),
                mean_entity_cv=float(np.mean(entity_cvs)) if entity_cvs else None,
                median_entity_cv=median_cv,
                high_cv_entity_count=high_cv_entity_count,
                flagged=(median_cv is not None and median_cv > high_cv_threshold),
            )
        )
    flagged_conditions = sum(entry.flagged for entry in entries)
    note = (
        "replicate cv indicates one or more conditions with unstable within-condition spread"
        if flagged_conditions > 0
        else "replicate cv did not detect unstable within-condition spread under the current threshold"
    )
    return ReplicateCvReport(
        entity_level=table.entity_level,
        high_cv_threshold=high_cv_threshold,
        entries=tuple(entries),
        note=note,
    )

def build_replicate_and_batch_qc_report(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    within_condition_warning_threshold: float = 0.8,
    batch_shift_threshold: float = 0.5,
) -> ReplicateAndBatchQcReport:
    """Build integrated replicate-correlation and batch-shift QC diagnostics."""
    replicate = build_replicate_correlation_report(table, design_entries)
    replicate_cv = build_replicate_cv_report(table, design_entries)
    sample_pca = build_sample_pca_report(table, design_entries)
    condition_clustering = build_condition_clustering_report(table, design_entries)
    batch = build_batch_effect_advisory(
        table,
        design_entries,
        shift_threshold=batch_shift_threshold,
    )
    design_by_sample = {entry.sample_id: entry for entry in design_entries}
    flagged_samples: dict[str, set[str]] = {}
    for entry in replicate.entries:
        if (
            entry.condition_a == entry.condition_b
            and entry.correlation < within_condition_warning_threshold
        ):
            flagged_samples.setdefault(entry.sample_a, set()).add(
                "low within-condition replicate correlation"
            )
            flagged_samples.setdefault(entry.sample_b, set()).add(
                "low within-condition replicate correlation"
            )
    batch_lookup = {
        batch_entry.batch_id: batch_entry
        for batch_entry in batch.batches
        if batch_entry.flagged
    }
    for sample_id, design in design_by_sample.items():
        if design.batch and design.batch in batch_lookup:
            flagged_samples.setdefault(sample_id, set()).add(
                "sample belongs to a batch with flagged global-abundance shift"
            )
    for entry in sample_pca.entries:
        if entry.outlier:
            flagged_samples.setdefault(entry.sample_id, set()).add(
                "principal-component profile lies far from the study centroid"
            )
    outliers = tuple(
        sorted(
            (
                QcOutlierSampleEntry(
                    sample_id=sample_id,
                    condition=design_by_sample[sample_id].condition,
                    batch=design_by_sample[sample_id].batch,
                    instrument=design_by_sample[sample_id].instrument,
                    spectra_file=design_by_sample[sample_id].spectra_file,
                    reasons=tuple(sorted(reasons)),
                )
                for sample_id, reasons in flagged_samples.items()
                if sample_id in design_by_sample
            ),
            key=lambda entry: entry.sample_id,
        )
    )
    note = (
        "replicate and batch qc detected one or more outlier samples requiring review"
        if outliers
        else "replicate and batch qc did not detect sample-level outlier signals under configured thresholds"
    )
    return ReplicateAndBatchQcReport(
        batch_effect_report=batch,
        replicate_correlation_report=replicate,
        replicate_cv_report=replicate_cv,
        replicate_correlation_count=len(replicate.entries),
        flagged_batch_count=sum(1 for entry in batch.batches if entry.flagged),
        sample_pca_report=sample_pca,
        condition_clustering_report=condition_clustering,
        outlier_samples=outliers,
        note=note,
    )


def build_sample_pca_report(
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> SamplePcaReport:
    """Project samples into a compact PCA space for replicate review."""
    sample_ids = tuple(table.sample_ids)
    condition_by_sample = _condition_lookup(design_entries)
    batch_by_sample = {entry.sample_id: entry.batch for entry in design_entries}
    matrix = _sample_feature_matrix(table)
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
            note="pca was not informative because fewer than two samples or features were available",
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
    global_threshold = _distance_outlier_threshold(global_distances)
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
        condition_thresholds[condition] = _distance_outlier_threshold(
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
            note="condition clustering was not informative because fewer than two samples were available",
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


def _sample_feature_matrix(table: LabelFreeQuantTable) -> np.ndarray:
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


def _distance_outlier_threshold(distances: np.ndarray) -> float:
    if distances.size == 0:
        return 0.0
    median = float(np.median(distances))
    mad = float(np.median(np.abs(distances - median)))
    if mad == 0.0:
        return median + 1e-6
    return median + 2.0 * mad


__all__ = [
    "build_condition_clustering_report",
    "build_replicate_and_batch_qc_report",
    "build_replicate_cv_report",
    "build_sample_pca_report",
]
