# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""HTML tables for drug-target interpretation report sections."""

from __future__ import annotations

from html import escape

from ..biological_report_bundle_contracts import (
    BiologicalResultReportBundle,
)


def _render_drug_target_table_html(report: BiologicalResultReportBundle) -> str:
    drug_target_report = report.drug_target_report
    if drug_target_report is None:
        return "<p>No drug-target interpretation report was generated.</p>"
    headers = (
        "Drug",
        "Protein",
        "Relationship",
        "Evidence tier",
        "Effect",
        "Pathways",
    )
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = "".join(
        (
            "<tr>"
            f"<td>{escape(entry.drug_name or entry.drug_id)}</td>"
            f"<td>{escape(entry.protein_ref)}</td>"
            f"<td>{escape(entry.relationship.value)}</td>"
            f"<td>{escape(entry.evidence_tier.value)}</td>"
            f"<td>{escape(entry.effect_direction.value)} ({entry.log2_fold_change:.3f})</td>"
            f"<td>{escape('; '.join(entry.supporting_pathway_ids))}</td>"
            "</tr>"
        )
        for entry in drug_target_report.entries[:10]
    )
    return (
        "<p>"
        f"<strong>Drugs</strong>: {drug_target_report.summary.drug_count} | "
        f"<strong>Direct targets</strong>: "
        f"{drug_target_report.summary.direct_target_entry_count} | "
        f"<strong>Indirect pathway neighbors</strong>: "
        f"{drug_target_report.summary.indirect_pathway_neighbor_entry_count}"
        "</p>"
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        "</table>"
    )


__all__ = ["_render_drug_target_table_html"]
