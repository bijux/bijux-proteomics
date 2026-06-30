# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Report overview HTML for biological result documents."""

from __future__ import annotations

from html import escape

from bijux_proteomics.workflow.reports.biological_report_artifact_path_contracts import (
    BiologicalResultReportArtifactPaths,
)
from bijux_proteomics.workflow.reports.biological_report_bundle_contracts import (
    BiologicalResultReportBundle,
)
from bijux_proteomics.workflow.reports.biological_report_html_artifact_inventory import (
    _render_biological_report_artifact_inventory_html,
)


def _render_biological_report_summary_html(
    report: BiologicalResultReportBundle,
    artifacts: BiologicalResultReportArtifactPaths,
) -> str:
    artifact_inventory_html = _render_biological_report_artifact_inventory_html(
        artifacts
    )
    return (
        "<h1>Biological result report</h1>"
        f"<p><strong>Contrast</strong>: {escape(report.volcano_review.condition_a)} vs {escape(report.volcano_review.condition_b)}</p>"
        f"<p><strong>Proteins</strong>: {report.summary.protein_count} | "
        f"<strong>Significant</strong>: {report.summary.significant_protein_count} | "
        f"<strong>Protein cards</strong>: {report.summary.protein_card_count} | "
        f"<strong>Experiment confidence</strong>: {report.summary.experiment_confidence_score:.2f} "
        f"({escape(report.summary.experiment_confidence_tier)}) | "
        f"<strong>Cohort interaction candidates</strong>: "
        f"{report.summary.cohort_interaction_candidate_count} | "
        f"<strong>Tissue mismatch warnings</strong>: "
        f"{report.summary.tissue_mismatch_warning_count} | "
        f"<strong>Invalid sections</strong>: {report.summary.invalid_section_count} | "
        f"<strong>Annotated</strong>: {report.summary.annotation_entry_count} | "
        f"<strong>Heatmap rows</strong>: {report.summary.heatmap_entity_count}</p>"
        "<h2>Artifacts</h2>"
        f"<ul>{artifact_inventory_html}</ul>"
        f"<p>{escape(report.note)}</p>"
    )


__all__ = ["_render_biological_report_summary_html"]
