# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""HTML tables for regulator interpretation report sections."""

from __future__ import annotations

from html import escape

from bijux_proteomics.workflow.reports.biological_report_bundle_contracts import (
    BiologicalResultReportBundle,
)


def _render_regulator_inference_table_html(
    report: BiologicalResultReportBundle,
) -> str:
    regulator_report = report.regulator_inference_report
    if regulator_report is None:
        return "<p>No regulator inference report was generated.</p>"
    headers = (
        "Regulator",
        "Evidence type",
        "Signal surface",
        "Direction",
        "Score",
        "Supporting proteins",
        "Supporting sites",
    )
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = "".join(
        (
            "<tr>"
            f"<td>{escape(entry.regulator)}</td>"
            f"<td>{escape(entry.evidence_type.value)}</td>"
            f"<td>{escape(entry.signal_surface.value)}</td>"
            f"<td>{escape(entry.direction.value)}</td>"
            f"<td>{entry.score:.3f}</td>"
            f"<td>{escape('; '.join(entry.supporting_protein_refs))}</td>"
            f"<td>{escape('; '.join(entry.supporting_site_keys))}</td>"
            "</tr>"
        )
        for entry in regulator_report.entries[:10]
    )
    return (
        "<p>"
        f"<strong>Regulators</strong>: {regulator_report.summary.regulator_count} | "
        f"<strong>Entries</strong>: {regulator_report.summary.entry_count} | "
        f"<strong>Site support</strong>: "
        f"{regulator_report.summary.site_regulation_entry_count} | "
        f"<strong>Abundance support</strong>: "
        f"{regulator_report.summary.protein_abundance_entry_count} | "
        f"<strong>Unresolved targets</strong>: "
        f"{regulator_report.summary.unresolved_target_count}"
        "</p>"
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        "</table>"
    )


__all__ = ["_render_regulator_inference_table_html"]
