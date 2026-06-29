# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable TSV rendering for sample exploration reports."""

from __future__ import annotations

import csv
from io import StringIO

from bijux_proteomics.io.stable_outputs import sort_rows_by_fields, sort_strings
from bijux_proteomics.quantification.provenance.sample_exploration.models import (
    SampleExplorationReport,
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


__all__ = [
    "render_sample_cluster_tsv",
    "render_sample_correlation_tsv",
    "render_sample_distance_tsv",
    "render_sample_exploration_summary_tsv",
    "render_sample_outlier_tsv",
    "render_sample_pca_scores_tsv",
    "render_sample_pca_variance_tsv",
]
