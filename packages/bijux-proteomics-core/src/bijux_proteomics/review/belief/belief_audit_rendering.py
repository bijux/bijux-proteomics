# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Rendering for belief-audit reports."""

from __future__ import annotations

import csv
from html import escape
from io import StringIO

from bijux_proteomics.review.belief.belief_audit_models import (
    BeliefAuditReport,
    BeliefAuditSubjectKind,
)

_SECTION_TITLES = {
    BeliefAuditSubjectKind.PROTEIN: "Proteins",
    BeliefAuditSubjectKind.PTM_SITE: "PTM Sites",
    BeliefAuditSubjectKind.PATHWAY: "Pathways",
    BeliefAuditSubjectKind.REGULATOR: "Regulators",
    BeliefAuditSubjectKind.BIOMARKER: "Biomarkers",
    BeliefAuditSubjectKind.QC_DECISION: "QC Decisions",
}


def render_belief_audit_summary_tsv(report: BeliefAuditReport) -> str:
    """Render belief-audit summary counts as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    for field, value in (
        ("entry_count", report.summary.entry_count),
        ("protein_entry_count", report.summary.protein_entry_count),
        ("ptm_site_entry_count", report.summary.ptm_site_entry_count),
        ("pathway_entry_count", report.summary.pathway_entry_count),
        ("regulator_entry_count", report.summary.regulator_entry_count),
        ("biomarker_entry_count", report.summary.biomarker_entry_count),
        ("qc_decision_entry_count", report.summary.qc_decision_entry_count),
        ("note", report.note),
    ):
        writer.writerow((field, value))
    return buffer.getvalue()


def render_belief_audit_tsv(report: BeliefAuditReport) -> str:
    """Render belief-audit entries as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "audit_id",
            "subject_kind",
            "subject_id",
            "subject_label",
            "claim",
            "decision",
            "confidence",
            "why_believed",
            "what_weakens",
            "what_would_falsify",
            "result_surfaces",
            "result_row_ids",
            "graph_node_ids",
            "note",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.audit_id,
                entry.subject_kind.value,
                entry.subject_id,
                entry.subject_label,
                entry.claim,
                entry.decision,
                entry.confidence,
                entry.why_believed,
                entry.what_weakens,
                entry.what_would_falsify,
                ";".join(entry.result_surfaces),
                ";".join(entry.result_row_ids),
                ";".join(entry.graph_node_ids),
                entry.note,
            )
        )
    return buffer.getvalue()


def render_belief_audit_html(report: BeliefAuditReport) -> str:
    """Render the belief audit as a report section with grouped conclusion entries."""

    lines = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        "<title>Belief Audit</title>",
        "</head>",
        "<body>",
        "<section>",
        "<h1>Belief Audit</h1>",
        "<p>Each conclusion records why it was retained, what weakens it, and what would falsify it.</p>",
    ]
    for subject_kind in BeliefAuditSubjectKind:
        entries = [
            entry for entry in report.entries if entry.subject_kind is subject_kind
        ]
        if not entries:
            continue
        lines.append(f"<section><h2>{escape(_SECTION_TITLES[subject_kind])}</h2>")
        for entry in entries:
            lines.extend(
                (
                    "<article>",
                    (
                        "<h3>"
                        f"{escape(entry.subject_label)} "
                        f"[{escape(entry.confidence)}]"
                        "</h3>"
                    ),
                    f"<p><strong>Claim:</strong> {escape(entry.claim)}</p>",
                    f"<p><strong>Decision:</strong> {escape(entry.decision)}</p>",
                    f"<p><strong>Why believed:</strong> {escape(entry.why_believed)}</p>",
                    f"<p><strong>What weakens it:</strong> {escape(entry.what_weakens)}</p>",
                    (
                        "<p><strong>What would falsify it:</strong> "
                        f"{escape(entry.what_would_falsify)}</p>"
                    ),
                    (
                        "<p><strong>Citations:</strong> surfaces="
                        f"{escape(';'.join(entry.result_surfaces))}, rows="
                        f"{escape(';'.join(entry.result_row_ids))}, graph nodes="
                        f"{escape(';'.join(entry.graph_node_ids))}</p>"
                    ),
                    "</article>",
                )
            )
        lines.append("</section>")
    if not report.entries:
        lines.append(
            "<p>No governed conclusion artifacts were provided for belief auditing.</p>"
        )
    lines.extend(("</section>", "</body>", "</html>"))
    return "\n".join(lines) + "\n"


__all__ = [
    "render_belief_audit_html",
    "render_belief_audit_summary_tsv",
    "render_belief_audit_tsv",
]
