# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""HTML tables for compartment biology report sections."""

from __future__ import annotations

from html import escape

from bijux_proteomics.workflow.reports.biological_report_html_support import (
    _format_optional_float,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportBundle,
)


def _render_compartment_biology_table_html(
    report: BiologicalResultReportBundle,
) -> str:
    compartment_biology_report = report.compartment_biology_report
    if compartment_biology_report is None:
        return "<p>No compartment biology report was generated.</p>"
    headers = (
        "Compartment",
        "Condition A",
        "Condition B",
        "Delta",
        "Comparison confidence",
    )
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = "".join(
        (
            "<tr>"
            f"<td>{escape(entry.set_name or entry.set_id)}</td>"
            f"<td>{escape(entry.condition_a)}</td>"
            f"<td>{escape(entry.condition_b)}</td>"
            f"<td>{_format_optional_float(entry.activity_score_delta)}</td>"
            f"<td>{escape(entry.comparison_confidence_status.value)}</td>"
            "</tr>"
        )
        for entry in compartment_biology_report.activity_report.condition_comparisons[
            :10
        ]
    )
    return (
        "<p>"
        f"<strong>Compartments</strong>: {compartment_biology_report.summary.compartment_count} | "
        f"<strong>Enriched compartments</strong>: "
        f"{compartment_biology_report.summary.enriched_compartment_count} | "
        f"<strong>Low-confidence sample scores</strong>: "
        f"{compartment_biology_report.summary.low_confidence_sample_score_count} | "
        f"<strong>Unresolved members</strong>: "
        f"{compartment_biology_report.summary.unresolved_member_count} | "
        f"<strong>Unknown foreground proteins</strong>: "
        f"{compartment_biology_report.summary.unknown_foreground_protein_count} | "
        f"<strong>Unknown background proteins</strong>: "
        f"{compartment_biology_report.summary.unknown_background_protein_count}"
        "</p>"
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        "</table>"
    )


__all__ = ["_render_compartment_biology_table_html"]
