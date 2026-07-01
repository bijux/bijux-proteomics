# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Contracts for visual and exploratory biological report exports."""

from __future__ import annotations

from dataclasses import dataclass


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


__all__ = ["BiologicalVisualExportNames"]
