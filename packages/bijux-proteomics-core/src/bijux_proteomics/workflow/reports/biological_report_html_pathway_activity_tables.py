# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""HTML tables for pathway activity report sections."""

from __future__ import annotations

from html import escape

from bijux_proteomics.workflow.reports.biological_report_html_support import (
    _format_optional_float,
)
from bijux_proteomics.workflow.reports.biological_report_bundle_contracts import (
    BiologicalResultReportBundle,
)


def _render_pathway_activity_table_html(report: BiologicalResultReportBundle) -> str:
    pathway_activity_report = report.pathway_activity_report
    if pathway_activity_report is None:
        return "<p>No pathway activity report was generated.</p>"
    headers = (
        "Pathway",
        "Condition A",
        "Condition B",
        "Delta",
        "Comparison confidence",
    )
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = "".join(
        (
            "<tr>"
            f"<td>{escape(entry.pathway_name or entry.pathway_id)}</td>"
            f"<td>{escape(entry.condition_a)}</td>"
            f"<td>{escape(entry.condition_b)}</td>"
            f"<td>{_format_optional_float(entry.activity_score_delta)}</td>"
            f"<td>{escape(entry.comparison_confidence_status.value)}</td>"
            "</tr>"
        )
        for entry in pathway_activity_report.condition_comparisons[:10]
    )
    return (
        "<p>"
        f"<strong>Pathways</strong>: {pathway_activity_report.summary.pathway_count} | "
        f"<strong>Low-confidence sample scores</strong>: "
        f"{pathway_activity_report.summary.low_confidence_sample_score_count} | "
        f"<strong>Unresolved members</strong>: "
        f"{pathway_activity_report.summary.unresolved_member_count}"
        "</p>"
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        "</table>"
    )


__all__ = ["_render_pathway_activity_table_html"]
