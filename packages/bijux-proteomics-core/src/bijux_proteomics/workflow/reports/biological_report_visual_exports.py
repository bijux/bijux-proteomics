# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Visual and exploratory artifact export for biological report bundles."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.quantification.provenance import (
    export_heatmap_column_metadata_tsv,
    export_heatmap_matrix_tsv,
    export_heatmap_row_metadata_tsv,
    export_heatmap_summary_tsv,
    export_sample_cluster_tsv,
    export_sample_distance_tsv,
    export_sample_exploration_summary_tsv,
    export_sample_pca_scores_tsv,
    export_sample_pca_variance_tsv,
)
from bijux_proteomics.review.explanations.volcano_plots import (
    export_volcano_review_html,
    export_volcano_review_json,
    export_volcano_review_svg,
    render_volcano_review_tsv,
)
from bijux_proteomics.workflow.cards.sample_evidence_cards import (
    render_sample_evidence_card_tsv,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportBundle,
)


@dataclass(frozen=True)
class BiologicalVisualExportNames:
    """Artifact names emitted for report visuals and exploratory outputs."""

    volcano_tsv_name: str
    volcano_json_name: str
    volcano_svg_name: str
    volcano_html_name: str
    heatmap_summary_name: str
    heatmap_matrix_name: str
    heatmap_row_name: str
    heatmap_column_name: str
    sample_summary_name: str
    sample_scores_name: str
    sample_variance_name: str
    sample_distance_name: str
    sample_cluster_name: str
    sample_card_name: str
    report_html_name: str


def write_biological_visual_exports(
    report: BiologicalResultReportBundle,
    output_dir: Path,
) -> BiologicalVisualExportNames:
    """Write volcano, heatmap, and sample exploration artifacts."""

    volcano_tsv_name = "biological_volcano.tsv"
    volcano_json_name = "biological_volcano.json"
    volcano_svg_name = "biological_volcano.svg"
    volcano_html_name = "biological_volcano.html"
    heatmap_summary_name = "biological_heatmap_summary.tsv"
    heatmap_matrix_name = "biological_heatmap_matrix.tsv"
    heatmap_row_name = "biological_heatmap_rows.tsv"
    heatmap_column_name = "biological_heatmap_columns.tsv"
    sample_summary_name = "biological_sample_exploration_summary.tsv"
    sample_scores_name = "biological_sample_pca_scores.tsv"
    sample_variance_name = "biological_sample_pca_variance.tsv"
    sample_distance_name = "biological_sample_distances.tsv"
    sample_cluster_name = "biological_sample_clusters.tsv"
    sample_card_name = "biological_sample_cards.tsv"
    report_html_name = "biological_report.html"

    write_output_table_tsv(
        output_dir / volcano_tsv_name,
        render_volcano_review_tsv(report.volcano_review),
    )
    export_volcano_review_json(report.volcano_review, output_dir / volcano_json_name)
    export_volcano_review_svg(report.volcano_review, output_dir / volcano_svg_name)
    export_volcano_review_html(report.volcano_review, output_dir / volcano_html_name)
    export_heatmap_summary_tsv(report.heatmap_report, output_dir / heatmap_summary_name)
    export_heatmap_matrix_tsv(report.heatmap_report, output_dir / heatmap_matrix_name)
    export_heatmap_row_metadata_tsv(report.heatmap_report, output_dir / heatmap_row_name)
    export_heatmap_column_metadata_tsv(
        report.heatmap_report,
        output_dir / heatmap_column_name,
    )
    export_sample_exploration_summary_tsv(
        report.sample_exploration_report,
        output_dir / sample_summary_name,
    )
    export_sample_pca_scores_tsv(
        report.sample_exploration_report,
        output_dir / sample_scores_name,
    )
    export_sample_pca_variance_tsv(
        report.sample_exploration_report,
        output_dir / sample_variance_name,
    )
    export_sample_distance_tsv(
        report.sample_exploration_report,
        output_dir / sample_distance_name,
    )
    export_sample_cluster_tsv(
        report.sample_exploration_report,
        output_dir / sample_cluster_name,
    )
    write_output_table_tsv(
        output_dir / sample_card_name,
        render_sample_evidence_card_tsv(report.sample_exploration_report),
    )

    return BiologicalVisualExportNames(
        volcano_tsv_name=volcano_tsv_name,
        volcano_json_name=volcano_json_name,
        volcano_svg_name=volcano_svg_name,
        volcano_html_name=volcano_html_name,
        heatmap_summary_name=heatmap_summary_name,
        heatmap_matrix_name=heatmap_matrix_name,
        heatmap_row_name=heatmap_row_name,
        heatmap_column_name=heatmap_column_name,
        sample_summary_name=sample_summary_name,
        sample_scores_name=sample_scores_name,
        sample_variance_name=sample_variance_name,
        sample_distance_name=sample_distance_name,
        sample_cluster_name=sample_cluster_name,
        sample_card_name=sample_card_name,
        report_html_name=report_html_name,
    )
