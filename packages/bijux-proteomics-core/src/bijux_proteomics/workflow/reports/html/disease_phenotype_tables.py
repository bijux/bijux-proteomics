# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""HTML tables for disease and phenotype interpretation report sections."""

from __future__ import annotations

from html import escape

from .support import (
    _format_optional_float,
)
from ..biological_report_bundle_contracts import (
    BiologicalResultReportBundle,
)


def _render_disease_phenotype_table_html(report: BiologicalResultReportBundle) -> str:
    disease_phenotype_report = report.disease_phenotype_report
    if disease_phenotype_report is None:
        return "<p>No disease or phenotype interpretation report was generated.</p>"
    headers = (
        "Kind",
        "Term",
        "Source",
        "Foreground overlap",
        "Adjusted p-value",
        "Confidence",
        "Supporting proteins",
    )
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = "".join(
        (
            "<tr>"
            f"<td>{escape(entry.context_kind.value)}</td>"
            f"<td>{escape(entry.term_name or entry.term_id)}</td>"
            f"<td>{escape(entry.source_name or '')}</td>"
            f"<td>{entry.foreground_overlap_count}</td>"
            f"<td>{_format_optional_float(entry.adjusted_p_value)}</td>"
            f"<td>{escape(entry.confidence_status.value)}</td>"
            f"<td>{escape('; '.join(entry.supporting_protein_refs))}</td>"
            "</tr>"
        )
        for entry in disease_phenotype_report.entries[:10]
    )
    return (
        "<p>"
        f"<strong>Evaluated terms</strong>: "
        f"{disease_phenotype_report.summary.evaluated_term_count} | "
        f"<strong>Passing terms</strong>: "
        f"{disease_phenotype_report.summary.filter_passing_term_count} | "
        f"<strong>High-confidence terms</strong>: "
        f"{disease_phenotype_report.summary.high_confidence_term_count} | "
        f"<strong>Unknown foreground proteins</strong>: "
        f"{disease_phenotype_report.summary.unknown_foreground_protein_count} | "
        f"<strong>Unknown background proteins</strong>: "
        f"{disease_phenotype_report.summary.unknown_background_protein_count}"
        "</p>"
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        "</table>"
    )


__all__ = ["_render_disease_phenotype_table_html"]
