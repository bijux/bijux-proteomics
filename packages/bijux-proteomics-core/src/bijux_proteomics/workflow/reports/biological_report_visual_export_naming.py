# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Durable file naming for visual and exploratory biological report exports."""

from __future__ import annotations

from bijux_proteomics.workflow.reports.biological_report_visual_export_contracts import (
    BiologicalVisualExportNames,
)


def _build_biological_visual_export_names() -> BiologicalVisualExportNames:
    return BiologicalVisualExportNames(
        volcano_tsv_name="biological_volcano.tsv",
        volcano_json_name="biological_volcano.json",
        volcano_svg_name="biological_volcano.svg",
        volcano_html_name="biological_volcano.html",
        heatmap_summary_name="biological_heatmap_summary.tsv",
        heatmap_matrix_name="biological_heatmap_matrix.tsv",
        heatmap_row_name="biological_heatmap_rows.tsv",
        heatmap_column_name="biological_heatmap_columns.tsv",
        sample_summary_name="biological_sample_exploration_summary.tsv",
        sample_scores_name="biological_sample_pca_scores.tsv",
        sample_variance_name="biological_sample_pca_variance.tsv",
        sample_distance_name="biological_sample_distances.tsv",
        sample_cluster_name="biological_sample_clusters.tsv",
        sample_card_name="biological_sample_cards.tsv",
        report_html_name="biological_report.html",
    )


__all__ = ["_build_biological_visual_export_names"]
