# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""HTML tables for scientific claim and hypothesis report sections."""

from __future__ import annotations

from html import escape

from ..biological_report_bundle_contracts import (
    BiologicalResultReportBundle,
)


def _render_biological_claim_validation_table_html(
    report: BiologicalResultReportBundle,
) -> str:
    if report.claim_validation_report is None:
        return "<p>No biological claim validation report was generated.</p>"
    headers = (
        "Claim",
        "Kind",
        "Direction",
        "Reason",
        "Source IDs",
    )
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = "".join(
        (
            "<tr>"
            f"<td>{escape(entry.claim_text)}</td>"
            f"<td>{escape(entry.claim_kind.value)}</td>"
            f"<td>{escape(entry.asserted_direction.value)}</td>"
            f"<td>{escape(entry.validation_note)}</td>"
            f"<td><code>{escape('; '.join(entry.source_ids))}</code></td>"
            "</tr>"
        )
        for entry in report.claim_validation_report.supported_claims
    )
    summary = report.claim_validation_report.summary
    return (
        "<p>"
        f"<strong>Supported claims</strong>: {summary.supported_claim_count} | "
        f"<strong>Rejected claims</strong>: {summary.rejected_claim_count}"
        "</p>"
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        "</table>"
    )


def _render_biological_hypothesis_table_html(
    report: BiologicalResultReportBundle,
) -> str:
    if report.biological_hypothesis_report is None:
        return "<p>No biological hypothesis report was generated.</p>"
    headers = (
        "Claim",
        "Kind",
        "Supporting proteins",
        "Supporting sites",
        "Opposing evidence",
        "Evidence node IDs",
        "Confidence",
        "Next experiment",
    )
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = "".join(
        (
            "<tr>"
            f"<td>{escape(entry.claim)}</td>"
            f"<td>{escape(entry.hypothesis_kind.value)}</td>"
            f"<td>{escape('; '.join(entry.supporting_protein_refs) or '-')}</td>"
            f"<td>{escape('; '.join(entry.supporting_site_keys) or '-')}</td>"
            f"<td>{escape('; '.join(entry.opposing_evidence) or '-')}</td>"
            f"<td><code>{escape('; '.join(entry.evidence_node_ids))}</code></td>"
            f"<td>{entry.confidence_score:.3f} ({escape(entry.confidence_tier.value)})</td>"
            f"<td>{escape(entry.next_experiment_suggestion)}</td>"
            "</tr>"
        )
        for entry in report.biological_hypothesis_report.hypotheses
    )
    summary = report.biological_hypothesis_report.summary
    return (
        "<p>"
        f"<strong>Hypotheses</strong>: {summary.hypothesis_count} | "
        f"<strong>Rejected candidates</strong>: {summary.rejected_candidate_count} | "
        f"<strong>High confidence</strong>: {summary.high_confidence_hypothesis_count}"
        "</p>"
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        "</table>"
    )
