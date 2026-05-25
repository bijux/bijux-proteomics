# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""HTML support helpers for biological report rendering."""
from __future__ import annotations

from html import escape

from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalReportSectionKey,
    BiologicalResultReportBundle,
)

def _render_section_heading_html(
    report: BiologicalResultReportBundle,
    section_key: BiologicalReportSectionKey,
) -> str:
    by_key = {entry.section_key: entry for entry in report.section_confidence_entries}
    entry = by_key[section_key]
    return (
        f"<h2>{escape(entry.section_title)} [{escape(entry.confidence_label.value)}]</h2>"
        f"<p><strong>Rationale</strong>: {escape(entry.rationale)}</p>"
    )


def _render_biological_report_section_confidence_table_html(
    report: BiologicalResultReportBundle,
) -> str:
    headers = ("Section", "Confidence", "Rationale")
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = "".join(
        (
            "<tr>"
            f"<td>{escape(entry.section_title)}</td>"
            f"<td>{escape(entry.confidence_label.value)}</td>"
            f"<td>{escape(entry.rationale)}</td>"
            "</tr>"
        )
        for entry in report.section_confidence_entries
    )
    return (
        "<p>"
        f"<strong>High</strong>: {report.summary.high_confidence_section_count} | "
        f"<strong>Moderate</strong>: {report.summary.moderate_confidence_section_count} | "
        f"<strong>Weak</strong>: {report.summary.weak_confidence_section_count} | "
        f"<strong>Exploratory</strong>: {report.summary.exploratory_section_count} | "
        f"<strong>Invalid</strong>: {report.summary.invalid_section_count}"
        "</p>"
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        "</table>"
    )



def _format_optional_float(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.4g}"


__all__ = [
    "_format_optional_float",
    "_render_biological_report_section_confidence_table_html",
    "_render_section_heading_html",
]
