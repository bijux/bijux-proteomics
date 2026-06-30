# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Visual and enrichment artifact-path assembly for biological report manifests."""

from __future__ import annotations

from bijux_proteomics.workflow.reports.biological_report_enrichment_exports import (
    BiologicalEnrichmentExportNames,
)
from bijux_proteomics.workflow.reports.biological_report_visual_exports import (
    BiologicalVisualExportNames,
)


def _build_biological_visual_artifact_path_fields(
    visual_export_names: BiologicalVisualExportNames,
) -> dict[str, str]:
    return {
        "volcano_tsv": visual_export_names.volcano_tsv_name,
        "volcano_json": visual_export_names.volcano_json_name,
        "volcano_svg": visual_export_names.volcano_svg_name,
        "volcano_html": visual_export_names.volcano_html_name,
        "heatmap_summary_tsv": visual_export_names.heatmap_summary_name,
        "heatmap_matrix_tsv": visual_export_names.heatmap_matrix_name,
        "heatmap_row_metadata_tsv": visual_export_names.heatmap_row_name,
        "heatmap_column_metadata_tsv": visual_export_names.heatmap_column_name,
        "sample_exploration_summary_tsv": visual_export_names.sample_summary_name,
        "sample_pca_scores_tsv": visual_export_names.sample_scores_name,
        "sample_pca_variance_tsv": visual_export_names.sample_variance_name,
        "sample_distance_tsv": visual_export_names.sample_distance_name,
        "sample_cluster_tsv": visual_export_names.sample_cluster_name,
        "sample_card_tsv": visual_export_names.sample_card_name,
        "report_html": visual_export_names.report_html_name,
    }


def _build_biological_enrichment_artifact_path_fields(
    enrichment_export_names: BiologicalEnrichmentExportNames,
) -> dict[str, str | None]:
    return {
        "go_summary_tsv": enrichment_export_names.go_summary_name,
        "go_term_tsv": enrichment_export_names.go_term_name,
        "go_unannotated_tsv": enrichment_export_names.go_unannotated_name,
        "pathway_summary_tsv": enrichment_export_names.pathway_summary_name,
        "pathway_entry_tsv": enrichment_export_names.pathway_entry_name,
        "pathway_unresolved_tsv": enrichment_export_names.pathway_unresolved_name,
        "complex_summary_tsv": enrichment_export_names.complex_summary_name,
        "complex_entry_tsv": enrichment_export_names.complex_entry_name,
        "complex_unresolved_tsv": enrichment_export_names.complex_unresolved_name,
    }
