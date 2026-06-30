# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""HTML tables for core scientific biological report sections."""

from __future__ import annotations

from html import escape

from bijux_proteomics.workflow.reports.biological_report_html_support import (
    _format_optional_float,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportBundle,
)


def _render_experiment_confidence_table_html(
    report: BiologicalResultReportBundle,
) -> str:
    headers = ("Component", "Score", "Tier", "Reason codes", "Message")
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = "".join(
        (
            "<tr>"
            f"<td>{escape(component.component.value)}</td>"
            f"<td>{component.score:.3f}</td>"
            f"<td>{escape(component.tier.value)}</td>"
            f"<td>{escape('; '.join(component.reason_codes))}</td>"
            f"<td>{escape(component.message)}</td>"
            "</tr>"
        )
        for component in report.experiment_confidence_report.components
    )
    summary = report.experiment_confidence_report.summary
    return (
        "<p>"
        f"<strong>Overall score</strong>: {summary.overall_score:.3f} | "
        f"<strong>Tier</strong>: {escape(summary.overall_tier.value)} | "
        f"<strong>Low-confidence components</strong>: "
        f"{summary.low_confidence_component_count}"
        "</p>"
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        "</table>"
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


def _render_foreground_background_model_table_html(
    report: BiologicalResultReportBundle,
) -> str:
    model = report.foreground_background_model
    issue_summary = (
        "none"
        if not model.issues
        else "; ".join(f"{issue.severity.value}:{issue.code}" for issue in model.issues)
    )
    headers = ("Role", "Source kind", "Policy", "Protein count")
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = "".join(
        (
            "<tr>"
            f"<td>{escape(role)}</td>"
            f"<td>{escape(source_kind)}</td>"
            f"<td>{escape(policy_name)}</td>"
            f"<td>{count}</td>"
            "</tr>"
        )
        for role, source_kind, policy_name, count in (
            (
                "foreground",
                model.foreground_source_kind.value,
                model.foreground_policy.policy_name,
                model.summary.foreground_size,
            ),
            (
                "background",
                model.background_source_kind.value,
                model.background_policy.policy_name,
                model.summary.background_size,
            ),
        )
    )
    return (
        "<p>"
        f"<strong>Valid for enrichment</strong>: "
        f"{str(model.summary.valid_for_enrichment).lower()} | "
        f"<strong>Issues</strong>: {model.summary.issue_count} | "
        f"<strong>Issue summary</strong>: {escape(issue_summary)}"
        "</p>"
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        "</table>"
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
