# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Visual and enrichment artifact inventory sections for biological report HTML."""

from __future__ import annotations

from bijux_proteomics.workflow.reports.biological_report_artifact_path_contracts import (
    BiologicalResultReportArtifactPaths,
)


def _build_biological_visual_artifact_sections(
    artifacts: BiologicalResultReportArtifactPaths,
) -> list[tuple[str, str | None]]:
    return [
        ("GO enrichment", artifacts.go_term_tsv),
        ("Pathway enrichment", artifacts.pathway_entry_tsv),
        ("Complex enrichment", artifacts.complex_entry_tsv),
        ("Volcano TSV", artifacts.volcano_tsv),
        ("Volcano JSON", artifacts.volcano_json),
        ("Volcano SVG", artifacts.volcano_svg),
        ("Volcano HTML", artifacts.volcano_html),
        ("Heatmap summary", artifacts.heatmap_summary_tsv),
        ("Heatmap matrix", artifacts.heatmap_matrix_tsv),
        ("Sample PCA scores", artifacts.sample_pca_scores_tsv),
        ("Sample distances", artifacts.sample_distance_tsv),
        ("Sample clusters", artifacts.sample_cluster_tsv),
    ]
