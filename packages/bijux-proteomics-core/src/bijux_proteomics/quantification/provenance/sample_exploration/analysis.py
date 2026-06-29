# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned sample-level exploratory analysis over governed quantification tables."""

from __future__ import annotations

from collections.abc import Sequence
import csv
from io import StringIO
import math
from pathlib import Path

import numpy as np

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.domain.records import QuantMatrix as CanonicalQuantMatrix
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.io.stable_outputs import sort_rows_by_fields, sort_strings
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
    SampleExplorationReport,
    SampleExplorationSummary,
    SampleOutlierEntry,
    SampleOutlierReport,
)
from bijux_proteomics.quantification.provenance.sample_exploration.sample_space import (
    build_condition_clustering_report,
    build_sample_feature_matrix,
    build_sample_pca_report,
    build_sample_pca_variance_report,
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
    distance_matrix = _pairwise_distance_matrix(decomposition.centered_matrix)
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
    decomposition = build_sample_space_decomposition(table, design_entries)
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
    for entry in sort_rows_by_fields(
        report.sample_cluster_report.entries, "merge_order"
    ):
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


def export_sample_pca_variance_tsv(report: SampleExplorationReport, path: Path) -> None:
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


def _cluster_member_key(
    sample_ids: tuple[str, ...], member_indexes: Sequence[int]
) -> str:
    return ";".join(sample_ids[index] for index in member_indexes)


__all__ = [
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
