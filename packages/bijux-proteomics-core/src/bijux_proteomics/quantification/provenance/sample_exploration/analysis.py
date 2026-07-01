# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned sample-level exploratory report assembly over governed tables."""

from __future__ import annotations

from bijux_proteomics.domain.records import QuantMatrix as CanonicalQuantMatrix
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts.matrix_building import (
    coerce_label_free_quant_table,
)
from bijux_proteomics.quantification.contracts.matrix_models import LabelFreeQuantTable
from bijux_proteomics.quantification.provenance.sample_exploration.models import (
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
    distance_outlier_threshold,
)
from bijux_proteomics.quantification.provenance.sample_exploration.sample_topology import (
    build_sample_cluster_report,
    build_sample_correlation_report,
    build_sample_distance_report,
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
]
