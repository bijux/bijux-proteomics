# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned sample-level exploratory analysis over governed quantification tables."""

from __future__ import annotations

from bijux_proteomics._output_tables import write_output_table_tsv

from collections.abc import Sequence
import csv
from dataclasses import dataclass
from io import StringIO
import math
from pathlib import Path

import numpy as np
from pydantic import ConfigDict, Field

from bijux_proteomics.domain.records import QuantMatrix as CanonicalQuantMatrix
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.io.stable_outputs import sort_rows_by_fields, sort_strings
from bijux_proteomics.quantification.contracts import (
    ConditionClusteringReport,
    LabelFreeQuantTable,
    QuantEntityLevel,
    QuantMeasureKind,
    QuantRollupMethod,
    SamplePcaEntry,
    SamplePcaReport,
    _condition_lookup,
    _matrix_value_index,
    coerce_label_free_quant_table,
)
from bijux_proteomics_foundation import JsonModel


@dataclass(frozen=True)
class _SampleSpaceDecomposition:
    sample_ids: tuple[str, ...]
    feature_count: int
    condition_by_sample: dict[str, str]
    batch_by_sample: dict[str, str | None]
    matrix: np.ndarray
    centered_matrix: np.ndarray
    scores: np.ndarray
    eigenvalues: np.ndarray
    total_variance: float


@dataclass(frozen=True)
class _SampleClusterState:
    member_indexes: tuple[int, ...]


class SamplePcaVarianceEntry(JsonModel):
    """Explained-variance payload for one principal component."""

    model_config = ConfigDict(extra="forbid")

    component_index: int = Field(..., ge=1)
    component_label: str = Field(..., min_length=1)
    explained_variance_ratio: float = Field(..., ge=0.0, le=1.0)
    cumulative_explained_variance_ratio: float = Field(..., ge=0.0, le=1.0)


class SamplePcaVarianceReport(JsonModel):
    """Explained-variance report over one sample PCA decomposition."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    entries: tuple[SamplePcaVarianceEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class SampleDistanceEntry(JsonModel):
    """One pairwise sample distance in centered feature space."""

    model_config = ConfigDict(extra="forbid")

    sample_id_a: str = Field(..., min_length=1)
    sample_id_b: str = Field(..., min_length=1)
    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    batch_a: str | None = None
    batch_b: str | None = None
    euclidean_distance: float = Field(..., ge=0.0)
    same_condition: bool
    same_batch: bool


class SampleDistanceReport(JsonModel):
    """Pairwise sample-distance report over one quantification table."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    sample_count: int = Field(..., ge=0)
    entries: tuple[SampleDistanceEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class SampleCorrelationEntry(JsonModel):
    """One pairwise sample correlation across the filled feature matrix."""

    model_config = ConfigDict(extra="forbid")

    sample_id_a: str = Field(..., min_length=1)
    sample_id_b: str = Field(..., min_length=1)
    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    batch_a: str | None = None
    batch_b: str | None = None
    pearson_correlation: float = Field(..., ge=-1.0, le=1.0)
    same_condition: bool
    same_batch: bool


class SampleCorrelationReport(JsonModel):
    """Pairwise sample-correlation report over one quantification table."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    sample_count: int = Field(..., ge=0)
    entries: tuple[SampleCorrelationEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class SampleClusterEntry(JsonModel):
    """One average-linkage merge row in a deterministic sample cluster table."""

    model_config = ConfigDict(extra="forbid")

    merge_order: int = Field(..., ge=1)
    member_sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    left_sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    right_sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    member_conditions: tuple[str, ...] = Field(default_factory=tuple)
    member_batches: tuple[str, ...] = Field(default_factory=tuple)
    member_count: int = Field(..., ge=2)
    average_linkage_distance: float = Field(..., ge=0.0)


class SampleClusterReport(JsonModel):
    """Deterministic average-linkage cluster table over study samples."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    sample_count: int = Field(..., ge=0)
    entries: tuple[SampleClusterEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class SampleOutlierEntry(JsonModel):
    """One outlier sample with the metric labels that triggered it."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    condition: str = Field(..., min_length=1)
    batch: str | None = None
    outlier_reasons: tuple[str, ...] = Field(default_factory=tuple)
    distance_from_global_centroid: float = Field(..., ge=0.0)
    distance_from_condition_centroid: float = Field(..., ge=0.0)


class SampleOutlierReport(JsonModel):
    """Explicit outlier ledger over the sample exploration space."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    entries: tuple[SampleOutlierEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class SampleExplorationSummary(JsonModel):
    """Compact study-space summary for one sample exploration run."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    measure_kind: QuantMeasureKind
    aggregation_method: QuantRollupMethod
    normalization_method: str = Field(..., min_length=1)
    sample_count: int = Field(..., ge=0)
    feature_count: int = Field(..., ge=0)
    pairwise_correlation_count: int = Field(..., ge=0)
    pairwise_distance_count: int = Field(..., ge=0)
    cluster_merge_count: int = Field(..., ge=0)
    outlier_sample_count: int = Field(..., ge=0)
    clustered_by_condition: bool


class SampleExplorationReport(JsonModel):
    """Integrated sample-level exploratory analysis over one quant table."""

    model_config = ConfigDict(extra="forbid")

    summary: SampleExplorationSummary
    sample_pca_report: SamplePcaReport
    explained_variance_report: SamplePcaVarianceReport
    condition_clustering_report: ConditionClusteringReport
    sample_correlation_report: SampleCorrelationReport
    sample_distance_report: SampleDistanceReport
    sample_cluster_report: SampleClusterReport
    sample_outlier_report: SampleOutlierReport
    note: str = Field(..., min_length=1)


def build_sample_pca_report(
    table: LabelFreeQuantTable | CanonicalQuantMatrix,
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> SamplePcaReport:
    """Project samples into a compact principal-component exploratory space."""

    table = coerce_label_free_quant_table(table)
    decomposition = _build_sample_space_decomposition(table, design_entries)
    if decomposition.centered_matrix.shape[0] < 2 or decomposition.feature_count == 0:
        return SamplePcaReport(
            entity_level=table.entity_level,
            explained_variance_ratio_pc1=0.0,
            explained_variance_ratio_pc2=0.0,
            entries=tuple(
                SamplePcaEntry(
                    sample_id=sample_id,
                    condition=decomposition.condition_by_sample.get(sample_id, "unknown"),
                batch=decomposition.batch_by_sample.get(sample_id),
                pc1=0.0,
                pc2=0.0,
                distance_from_global_centroid=0.0,
                distance_from_condition_centroid=0.0,
                global_centroid_outlier=False,
                condition_centroid_outlier=False,
                outlier_reasons=(),
                outlier=False,
            )
            for sample_id in decomposition.sample_ids
            ),
            note=(
                "pca was not informative because fewer than two samples or features were available"
            ),
        )
    pc1 = (
        decomposition.scores[:, 0]
        if decomposition.scores.shape[1] >= 1
        else np.zeros(len(decomposition.sample_ids))
    )
    pc2 = (
        decomposition.scores[:, 1]
        if decomposition.scores.shape[1] >= 2
        else np.zeros(len(decomposition.sample_ids))
    )
    coordinates = np.column_stack((pc1, pc2))
    global_distances = np.linalg.norm(coordinates, axis=1)
    global_threshold = distance_outlier_threshold(global_distances)
    condition_thresholds: dict[str, float] = {}
    condition_distances_by_sample: dict[str, float] = {}
    entries: list[SamplePcaEntry] = []
    for condition in sorted(set(decomposition.condition_by_sample.values())):
        same_condition_indexes = np.array(
            [
                index
                for index, sample_id in enumerate(decomposition.sample_ids)
                if decomposition.condition_by_sample.get(sample_id, "unknown")
                == condition
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
            condition_distances_by_sample[decomposition.sample_ids[sample_index]] = (
                float(condition_distances[offset])
            )
    for index, sample_id in enumerate(decomposition.sample_ids):
        condition = decomposition.condition_by_sample.get(sample_id, "unknown")
        condition_distance = condition_distances_by_sample.get(sample_id, 0.0)
        global_outlier = float(global_distances[index]) > global_threshold
        condition_outlier = (
            condition_distance > condition_thresholds.get(condition, 0.0)
        )
        outlier_reasons = tuple(
            reason
            for reason, triggered in (
                ("distance_from_global_centroid", global_outlier),
                ("distance_from_condition_centroid", condition_outlier),
            )
            if triggered
        )
        outlier = bool(outlier_reasons)
        entries.append(
            SamplePcaEntry(
                sample_id=sample_id,
                condition=condition,
                batch=decomposition.batch_by_sample.get(sample_id),
                pc1=float(pc1[index]),
                pc2=float(pc2[index]),
                distance_from_global_centroid=float(global_distances[index]),
                distance_from_condition_centroid=condition_distance,
                global_centroid_outlier=global_outlier,
                condition_centroid_outlier=condition_outlier,
                outlier_reasons=outlier_reasons,
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
            float(decomposition.eigenvalues[0] / decomposition.total_variance)
            if decomposition.total_variance > 0.0
            and decomposition.eigenvalues.size >= 1
            else 0.0
        ),
        explained_variance_ratio_pc2=(
            float(decomposition.eigenvalues[1] / decomposition.total_variance)
            if decomposition.total_variance > 0.0
            and decomposition.eigenvalues.size >= 2
            else 0.0
        ),
        entries=tuple(entries),
        note=note,
    )


def build_sample_pca_variance_report(
    table: LabelFreeQuantTable | CanonicalQuantMatrix,
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> SamplePcaVarianceReport:
    """Summarize explained variance across the PCA decomposition."""

    table = coerce_label_free_quant_table(table)
    decomposition = _build_sample_space_decomposition(table, design_entries)
    if decomposition.total_variance <= 0.0 or decomposition.eigenvalues.size == 0:
        return SamplePcaVarianceReport(
            entity_level=table.entity_level,
            entries=(),
            note=(
                "explained variance was not informative because fewer than two samples or features were available"
            ),
        )
    cumulative = 0.0
    entries: list[SamplePcaVarianceEntry] = []
    for index, eigenvalue in enumerate(decomposition.eigenvalues, start=1):
        explained = float(eigenvalue / decomposition.total_variance)
        cumulative = min(1.0, cumulative + explained)
        entries.append(
            SamplePcaVarianceEntry(
                component_index=index,
                component_label=f"PC{index}",
                explained_variance_ratio=explained,
                cumulative_explained_variance_ratio=cumulative,
            )
        )
    return SamplePcaVarianceReport(
        entity_level=table.entity_level,
        entries=tuple(entries),
        note=(
            "explained variance preserves the contribution of each principal component to the centered study space"
        ),
    )


def build_condition_clustering_report(
    table: LabelFreeQuantTable | CanonicalQuantMatrix,
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> ConditionClusteringReport:
    """Summarize whether nearby samples cluster by biological condition."""

    table = coerce_label_free_quant_table(table)
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


def build_sample_distance_report(
    table: LabelFreeQuantTable | CanonicalQuantMatrix,
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> SampleDistanceReport:
    """Compute pairwise sample distances in centered feature space."""

    table = coerce_label_free_quant_table(table)
    decomposition = _build_sample_space_decomposition(table, design_entries)
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
    decomposition = _build_sample_space_decomposition(table, design_entries)
    entries: list[SampleCorrelationEntry] = []
    for left_index in range(len(decomposition.sample_ids)):
        for right_index in range(left_index + 1, len(decomposition.sample_ids)):
            left_sample_id = decomposition.sample_ids[left_index]
            right_sample_id = decomposition.sample_ids[right_index]
            correlation = _safe_sample_correlation(
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
    decomposition = _build_sample_space_decomposition(table, design_entries)
    if len(decomposition.sample_ids) < 2:
        return SampleClusterReport(
            entity_level=table.entity_level,
            sample_count=len(decomposition.sample_ids),
            entries=(),
            note=(
                "sample clustering was not informative because fewer than two samples were available"
            ),
        )
    distance_matrix = _pairwise_distance_matrix(decomposition.centered_matrix)
    active_clusters = [
        _SampleClusterState(member_indexes=(index,))
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
                distance = _average_linkage_distance(
                    distance_matrix,
                    left_cluster.member_indexes,
                    right_cluster.member_indexes,
                )
                left_key = _cluster_member_key(
                    decomposition.sample_ids,
                    left_cluster.member_indexes,
                )
                right_key = _cluster_member_key(
                    decomposition.sample_ids,
                    right_cluster.member_indexes,
                )
                candidate_key = (left_key, right_key)
                if (
                    best_distance is None
                    or distance < best_distance
                    or (
                        math.isclose(distance, best_distance, rel_tol=0.0, abs_tol=1e-12)
                        and candidate_key < (best_key or ("", ""))
                    )
                ):
                    best_pair = (left_index, right_index)
                    best_distance = distance
                    best_key = candidate_key
        assert best_pair is not None  # sample_count >= 2 guarantees one merge
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
        next_clusters: list[_SampleClusterState] = []
        for index, cluster in enumerate(active_clusters):
            if index not in best_pair:
                next_clusters.append(cluster)
        next_clusters.append(_SampleClusterState(member_indexes=merged_indexes))
        active_clusters = sorted(
            next_clusters,
            key=lambda cluster: _cluster_member_key(
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


def build_sample_exploration_report(
    table: LabelFreeQuantTable | CanonicalQuantMatrix,
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> SampleExplorationReport:
    """Assemble one owned report for PCA, distances, and sample clustering."""

    table = coerce_label_free_quant_table(table)
    decomposition = _build_sample_space_decomposition(table, design_entries)
    pca_report = build_sample_pca_report(table, design_entries)
    variance_report = build_sample_pca_variance_report(table, design_entries)
    condition_clustering_report = build_condition_clustering_report(
        table,
        design_entries,
    )
    correlation_report = build_sample_correlation_report(table, design_entries)
    distance_report = build_sample_distance_report(table, design_entries)
    cluster_report = build_sample_cluster_report(table, design_entries)
    outlier_entries = tuple(
        SampleOutlierEntry(
            sample_id=entry.sample_id,
            condition=entry.condition,
            batch=entry.batch,
            outlier_reasons=entry.outlier_reasons,
            distance_from_global_centroid=entry.distance_from_global_centroid,
            distance_from_condition_centroid=entry.distance_from_condition_centroid,
        )
        for entry in pca_report.entries
        if entry.outlier
    )
    outlier_report = SampleOutlierReport(
        entity_level=table.entity_level,
        entries=outlier_entries,
        note=(
            "outlier labels preserve the distance metric that triggered each sample-level exploratory flag"
            if outlier_entries
            else "sample exploration did not detect outliers under the current distance metrics"
        ),
    )
    return SampleExplorationReport(
        summary=SampleExplorationSummary(
            entity_level=table.entity_level,
            measure_kind=table.measure_kind,
            aggregation_method=table.aggregation_method,
            normalization_method=table.normalization_method.value,
            sample_count=len(decomposition.sample_ids),
            feature_count=decomposition.feature_count,
            pairwise_correlation_count=len(correlation_report.entries),
            pairwise_distance_count=len(distance_report.entries),
            cluster_merge_count=len(cluster_report.entries),
            outlier_sample_count=sum(entry.outlier for entry in pca_report.entries),
            clustered_by_condition=condition_clustering_report.clustered_by_condition,
        ),
        sample_pca_report=pca_report,
        explained_variance_report=variance_report,
        condition_clustering_report=condition_clustering_report,
        sample_correlation_report=correlation_report,
        sample_distance_report=distance_report,
        sample_cluster_report=cluster_report,
        sample_outlier_report=outlier_report,
        note=(
            "sample exploration assembles pca, explained variance, pairwise correlations, pairwise distances, average-linkage clustering, and metric-labeled outlier review over one governed quantification table"
        ),
    )


def render_sample_exploration_summary_tsv(report: SampleExplorationReport) -> str:
    """Render one compact sample-exploration summary as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "entity_level",
            "measure_kind",
            "aggregation_method",
            "normalization_method",
            "sample_count",
            "feature_count",
            "pairwise_correlation_count",
            "pairwise_distance_count",
            "cluster_merge_count",
            "outlier_sample_count",
            "clustered_by_condition",
        )
    )
    writer.writerow(
        (
            report.summary.entity_level.value,
            report.summary.measure_kind.value,
            report.summary.aggregation_method.value,
            report.summary.normalization_method,
            report.summary.sample_count,
            report.summary.feature_count,
            report.summary.pairwise_correlation_count,
            report.summary.pairwise_distance_count,
            report.summary.cluster_merge_count,
            report.summary.outlier_sample_count,
            str(report.summary.clustered_by_condition).lower(),
        )
    )
    return handle.getvalue()


def render_sample_pca_scores_tsv(report: SampleExplorationReport) -> str:
    """Render one sample-level PCA score table as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "sample_id",
            "condition",
            "batch",
            "pc1",
            "pc2",
            "distance_from_global_centroid",
            "distance_from_condition_centroid",
            "global_centroid_outlier",
            "condition_centroid_outlier",
            "outlier_reasons",
            "outlier",
        )
    )
    for entry in sort_rows_by_fields(report.sample_pca_report.entries, "sample_id"):
        writer.writerow(
            (
                entry.sample_id,
                entry.condition,
                entry.batch or "",
                f"{entry.pc1:g}",
                f"{entry.pc2:g}",
                f"{entry.distance_from_global_centroid:g}",
                f"{entry.distance_from_condition_centroid:g}",
                str(entry.global_centroid_outlier).lower(),
                str(entry.condition_centroid_outlier).lower(),
                ";".join(sort_strings(entry.outlier_reasons)),
                str(entry.outlier).lower(),
            )
        )
    return handle.getvalue()


def render_sample_correlation_tsv(report: SampleExplorationReport) -> str:
    """Render pairwise sample correlations as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "sample_id_a",
            "sample_id_b",
            "condition_a",
            "condition_b",
            "batch_a",
            "batch_b",
            "pearson_correlation",
            "same_condition",
            "same_batch",
        )
    )
    for entry in sort_rows_by_fields(
        report.sample_correlation_report.entries,
        "sample_id_a",
        "sample_id_b",
    ):
        writer.writerow(
            (
                entry.sample_id_a,
                entry.sample_id_b,
                entry.condition_a,
                entry.condition_b,
                entry.batch_a or "",
                entry.batch_b or "",
                f"{entry.pearson_correlation:g}",
                str(entry.same_condition).lower(),
                str(entry.same_batch).lower(),
            )
        )
    return handle.getvalue()


def render_sample_pca_variance_tsv(report: SampleExplorationReport) -> str:
    """Render explained variance across principal components as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "component_index",
            "component_label",
            "explained_variance_ratio",
            "cumulative_explained_variance_ratio",
        )
    )
    for entry in sort_rows_by_fields(
        report.explained_variance_report.entries,
        "component_index",
    ):
        writer.writerow(
            (
                entry.component_index,
                entry.component_label,
                f"{entry.explained_variance_ratio:g}",
                f"{entry.cumulative_explained_variance_ratio:g}",
            )
        )
    return handle.getvalue()


def render_sample_distance_tsv(report: SampleExplorationReport) -> str:
    """Render pairwise sample distances as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "sample_id_a",
            "sample_id_b",
            "condition_a",
            "condition_b",
            "batch_a",
            "batch_b",
            "euclidean_distance",
            "same_condition",
            "same_batch",
        )
    )
    for entry in sort_rows_by_fields(
        report.sample_distance_report.entries,
        "sample_id_a",
        "sample_id_b",
    ):
        writer.writerow(
            (
                entry.sample_id_a,
                entry.sample_id_b,
                entry.condition_a,
                entry.condition_b,
                entry.batch_a or "",
                entry.batch_b or "",
                f"{entry.euclidean_distance:g}",
                str(entry.same_condition).lower(),
                str(entry.same_batch).lower(),
            )
        )
    return handle.getvalue()


def render_sample_outlier_tsv(report: SampleExplorationReport) -> str:
    """Render metric-labeled outlier rows as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "sample_id",
            "condition",
            "batch",
            "outlier_reasons",
            "distance_from_global_centroid",
            "distance_from_condition_centroid",
        )
    )
    for entry in sort_rows_by_fields(
        report.sample_outlier_report.entries,
        "sample_id",
    ):
        writer.writerow(
            (
                entry.sample_id,
                entry.condition,
                entry.batch or "",
                ";".join(sort_strings(entry.outlier_reasons)),
                f"{entry.distance_from_global_centroid:g}",
                f"{entry.distance_from_condition_centroid:g}",
            )
        )
    return handle.getvalue()


def render_sample_cluster_tsv(report: SampleExplorationReport) -> str:
    """Render the deterministic average-linkage cluster table as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "merge_order",
            "member_sample_ids",
            "left_sample_ids",
            "right_sample_ids",
            "member_conditions",
            "member_batches",
            "member_count",
            "average_linkage_distance",
        )
    )
    for entry in sort_rows_by_fields(report.sample_cluster_report.entries, "merge_order"):
        writer.writerow(
            (
                entry.merge_order,
                ";".join(sort_strings(entry.member_sample_ids)),
                ";".join(sort_strings(entry.left_sample_ids)),
                ";".join(sort_strings(entry.right_sample_ids)),
                ";".join(sort_strings(entry.member_conditions)),
                ";".join(sort_strings(entry.member_batches)),
                entry.member_count,
                f"{entry.average_linkage_distance:g}",
            )
        )
    return handle.getvalue()


def export_sample_exploration_summary_tsv(
    report: SampleExplorationReport, path: Path
) -> None:
    """Write one compact sample-exploration summary to a stable TSV artifact."""

    write_output_table_tsv(path, render_sample_exploration_summary_tsv(report))


def export_sample_pca_scores_tsv(report: SampleExplorationReport, path: Path) -> None:
    """Write one sample-level PCA score table to a stable TSV artifact."""

    write_output_table_tsv(path, render_sample_pca_scores_tsv(report))


def export_sample_correlation_tsv(report: SampleExplorationReport, path: Path) -> None:
    """Write pairwise sample correlations to a stable TSV artifact."""

    write_output_table_tsv(path, render_sample_correlation_tsv(report))


def export_sample_pca_variance_tsv(
    report: SampleExplorationReport, path: Path
) -> None:
    """Write PCA explained-variance rows to a stable TSV artifact."""

    write_output_table_tsv(path, render_sample_pca_variance_tsv(report))


def export_sample_distance_tsv(report: SampleExplorationReport, path: Path) -> None:
    """Write pairwise sample distances to a stable TSV artifact."""

    write_output_table_tsv(path, render_sample_distance_tsv(report))


def export_sample_outlier_tsv(report: SampleExplorationReport, path: Path) -> None:
    """Write metric-labeled sample outliers to a stable TSV artifact."""

    write_output_table_tsv(path, render_sample_outlier_tsv(report))


def export_sample_cluster_tsv(report: SampleExplorationReport, path: Path) -> None:
    """Write the deterministic cluster table to a stable TSV artifact."""

    write_output_table_tsv(path, render_sample_cluster_tsv(report))


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


def _build_sample_space_decomposition(
    table: LabelFreeQuantTable | CanonicalQuantMatrix,
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> _SampleSpaceDecomposition:
    table = coerce_label_free_quant_table(table)
    matrix = build_sample_feature_matrix(table)
    centered = matrix - np.mean(matrix, axis=0, keepdims=True)
    feature_count = int(centered.shape[1])
    if centered.shape[0] < 2 or feature_count == 0:
        scores = np.zeros((centered.shape[0], 0), dtype=float)
        eigenvalues = np.zeros((0,), dtype=float)
        total_variance = 0.0
    else:
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
    return _SampleSpaceDecomposition(
        sample_ids=table.sample_ids,
        feature_count=feature_count,
        condition_by_sample=_condition_lookup(design_entries),
        batch_by_sample={entry.sample_id: entry.batch for entry in design_entries},
        matrix=matrix,
        centered_matrix=centered,
        scores=scores,
        eigenvalues=eigenvalues,
        total_variance=total_variance,
    )


def _pairwise_distance_matrix(matrix: np.ndarray) -> np.ndarray:
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


def _safe_sample_correlation(left: np.ndarray, right: np.ndarray) -> float:
    left_std = float(np.std(left))
    right_std = float(np.std(right))
    if left_std <= 0.0 or right_std <= 0.0:
        return 1.0 if np.allclose(left, right) else 0.0
    correlation = float(np.corrcoef(left, right)[0, 1])
    if not math.isfinite(correlation):
        return 0.0
    return max(-1.0, min(1.0, correlation))


def _average_linkage_distance(
    distance_matrix: np.ndarray,
    left_indexes: Sequence[int],
    right_indexes: Sequence[int],
) -> float:
    distances = [
        float(distance_matrix[left_index, right_index])
        for left_index in left_indexes
        for right_index in right_indexes
    ]
    return float(np.mean(distances)) if distances else 0.0


def _cluster_member_key(sample_ids: tuple[str, ...], member_indexes: Sequence[int]) -> str:
    return ";".join(sample_ids[index] for index in member_indexes)


__all__ = [
    "ConditionClusteringReport",
    "SampleClusterEntry",
    "SampleClusterReport",
    "SampleCorrelationEntry",
    "SampleCorrelationReport",
    "SampleDistanceEntry",
    "SampleDistanceReport",
    "SampleExplorationReport",
    "SampleExplorationSummary",
    "SampleOutlierEntry",
    "SampleOutlierReport",
    "SamplePcaEntry",
    "SamplePcaReport",
    "SamplePcaVarianceEntry",
    "SamplePcaVarianceReport",
    "build_condition_clustering_report",
    "build_sample_cluster_report",
    "build_sample_correlation_report",
    "build_sample_distance_report",
    "build_sample_exploration_report",
    "build_sample_feature_matrix",
    "build_sample_pca_report",
    "build_sample_pca_variance_report",
    "distance_outlier_threshold",
    "export_sample_cluster_tsv",
    "export_sample_correlation_tsv",
    "export_sample_distance_tsv",
    "export_sample_exploration_summary_tsv",
    "export_sample_outlier_tsv",
    "export_sample_pca_scores_tsv",
    "export_sample_pca_variance_tsv",
    "render_sample_cluster_tsv",
    "render_sample_correlation_tsv",
    "render_sample_distance_tsv",
    "render_sample_exploration_summary_tsv",
    "render_sample_outlier_tsv",
    "render_sample_pca_scores_tsv",
    "render_sample_pca_variance_tsv",
]
