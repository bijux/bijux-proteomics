# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Visual and exploratory artifact export for biological report bundles."""

from __future__ import annotations

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
from bijux_proteomics.workflow.reports.biological_report_bundle_contracts import (
    BiologicalVisualReportBundle,
)
from bijux_proteomics.workflow.reports.biological_report_visual_export_contracts import (
    BiologicalVisualExportNames,
)
from bijux_proteomics.workflow.reports.biological_report_visual_export_naming import (
    _build_biological_visual_export_names,
)


def write_biological_visual_exports(
    report: BiologicalVisualReportBundle,
    output_dir: Path,
) -> BiologicalVisualExportNames:
    """Write volcano, heatmap, and sample exploration artifacts."""
    export_names = _build_biological_visual_export_names()

    write_output_table_tsv(
        output_dir / export_names.volcano_tsv_name,
        render_volcano_review_tsv(report.volcano_review),
    )
    export_volcano_review_json(
        report.volcano_review,
        output_dir / export_names.volcano_json_name,
    )
    export_volcano_review_svg(
        report.volcano_review,
        output_dir / export_names.volcano_svg_name,
    )
    export_volcano_review_html(
        report.volcano_review,
        output_dir / export_names.volcano_html_name,
    )
    export_heatmap_summary_tsv(
        report.heatmap_report,
        output_dir / export_names.heatmap_summary_name,
    )
    export_heatmap_matrix_tsv(
        report.heatmap_report,
        output_dir / export_names.heatmap_matrix_name,
    )
    export_heatmap_row_metadata_tsv(
        report.heatmap_report,
        output_dir / export_names.heatmap_row_name,
    )
    export_heatmap_column_metadata_tsv(
        report.heatmap_report,
        output_dir / export_names.heatmap_column_name,
    )
    export_sample_exploration_summary_tsv(
        report.sample_exploration_report,
        output_dir / export_names.sample_summary_name,
    )
    export_sample_pca_scores_tsv(
        report.sample_exploration_report,
        output_dir / export_names.sample_scores_name,
    )
    export_sample_pca_variance_tsv(
        report.sample_exploration_report,
        output_dir / export_names.sample_variance_name,
    )
    export_sample_distance_tsv(
        report.sample_exploration_report,
        output_dir / export_names.sample_distance_name,
    )
    export_sample_cluster_tsv(
        report.sample_exploration_report,
        output_dir / export_names.sample_cluster_name,
    )
    write_output_table_tsv(
        output_dir / export_names.sample_card_name,
        render_sample_evidence_card_tsv(report.sample_exploration_report),
    )
    return export_names
