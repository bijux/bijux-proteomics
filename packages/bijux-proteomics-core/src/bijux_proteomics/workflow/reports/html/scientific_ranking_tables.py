# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""HTML tables for scientific ranking and protein-card report sections."""

from __future__ import annotations

from html import escape

from .support import (
    _format_optional_float,
)
from ..biological_report_bundle_contracts import (
    BiologicalResultReportBundle,
)


def _render_protein_mechanism_card_table_html(
    report: BiologicalResultReportBundle,
) -> str:
    headers = (
        "Protein group",
        "Representative protein",
        "Graph claim",
        "Gene",
        "Identity",
        "Direction",
        "PTM sites",
        "Domains",
        "Pathways",
        "Complexes",
        "Peptide support",
        "Coverage",
        "Confidence tier",
        "Evidence tier",
        "log2FC",
        "Adjusted p-value",
        "Downgrade reasons",
        "Warnings",
        "Card ID",
    )
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = "".join(
        (
            "<tr>"
            f"<td>{escape(card.protein_group_id)}</td>"
            f"<td>{escape(card.representative_protein_ref)}</td>"
            f"<td><code>{escape(card.graph_claim_node_id)}</code></td>"
            f"<td>{escape('' if card.gene_symbol is None else card.gene_symbol)}</td>"
            f"<td>{escape(card.identity_level.value)}</td>"
            f"<td>{escape(card.abundance_change.direction.value)}</td>"
            f"<td>{escape('; '.join(ptm.site_key for ptm in card.ptms))}</td>"
            f"<td>{escape('; '.join(domain.label for domain in card.domains))}</td>"
            f"<td>{escape('; '.join(entry.entry_id for entry in card.pathways))}</td>"
            f"<td>{escape('; '.join(entry.entry_id for entry in card.complexes))}</td>"
            f"<td>{card.peptide_support.unique_peptide_count}/{card.peptide_support.peptide_count}</td>"
            f"<td>{card.peptide_support.coverage_fraction:.2%}</td>"
            f"<td>{escape(card.confidence_tier.value)}</td>"
            f"<td>{escape(card.evidence_tier.value)}</td>"
            f"<td>{card.abundance_change.log2_fold_change:.3f}</td>"
            f"<td>{_format_optional_float(card.abundance_change.adjusted_p_value)}</td>"
            f"<td>{escape('; '.join(reason.value for reason in card.downgrade_reasons))}</td>"
            f"<td>{escape('; '.join(code.value for code in card.warning_codes))}</td>"
            f"<td><code>{escape(card.card_id)}</code></td>"
            "</tr>"
        )
        for card in report.protein_mechanism_cards.cards
    )
    return (
        f"<table><thead><tr>{header_html}</tr></thead><tbody>{row_html}</tbody></table>"
    )


def _render_evidence_aware_ranking_table_html(
    report: BiologicalResultReportBundle,
) -> str:
    ranking_report = report.evidence_aware_ranking_report
    if ranking_report is None:
        return "<p>No evidence-aware ranking was generated.</p>"
    headers = (
        "Rank",
        "Kind",
        "Label",
        "Score",
        "Adjusted p-value",
        "Support",
        "Penalty codes",
        "Note",
    )
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = "".join(
        (
            "<tr>"
            f"<td>{entry.priority_rank}</td>"
            f"<td>{escape(entry.entity_kind.value)}</td>"
            f"<td>{escape(entry.display_label)}</td>"
            f"<td>{entry.decomposition.final_score:.3f}</td>"
            f"<td>{_format_optional_float(entry.adjusted_p_value)}</td>"
            f"<td>{entry.support_count}</td>"
            f"<td>{escape('; '.join(entry.penalty_codes))}</td>"
            f"<td>{escape(entry.ranking_note)}</td>"
            "</tr>"
        )
        for entry in ranking_report.entries[:15]
    )
    return (
        "<p>"
        f"<strong>Ranked findings</strong>: {ranking_report.summary.entry_count} | "
        f"<strong>Proteins</strong>: {ranking_report.summary.protein_entry_count} | "
        f"<strong>Pathways</strong>: {ranking_report.summary.pathway_entry_count}"
        "</p>"
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        "</table>"
    )
