# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""HTML tables for complex activity report sections."""

from __future__ import annotations

from html import escape

from ..biological_report_bundle_contracts import (
    BiologicalResultReportBundle,
)
from .support import (
    _format_optional_float,
)


def _render_complex_activity_table_html(report: BiologicalResultReportBundle) -> str:
    complex_activity_report = report.complex_activity_report
    if complex_activity_report is None:
        return "<p>No complex activity report was generated.</p>"
    headers = (
        "Complex",
        "Condition A",
        "Condition B",
        "Delta",
        "Limiting members",
        "Comparison confidence",
    )
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = "".join(
        (
            "<tr>"
            f"<td>{escape(entry.complex_name or entry.complex_id)}</td>"
            f"<td>{escape(entry.condition_a)}</td>"
            f"<td>{escape(entry.condition_b)}</td>"
            f"<td>{_format_optional_float(entry.activity_score_delta)}</td>"
            f"<td>{escape('; '.join(entry.condition_b_limiting_member_ids))}</td>"
            f"<td>{escape(entry.comparison_confidence_status.value)}</td>"
            "</tr>"
        )
        for entry in complex_activity_report.condition_comparisons[:10]
    )
    return (
        "<p>"
        f"<strong>Complexes</strong>: {complex_activity_report.summary.complex_count} | "
        f"<strong>Low-confidence sample scores</strong>: "
        f"{complex_activity_report.summary.low_confidence_sample_score_count} | "
        f"<strong>Unresolved members</strong>: "
        f"{complex_activity_report.summary.unresolved_member_count}"
        "</p>"
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        "</table>"
    )


__all__ = ["_render_complex_activity_table_html"]
