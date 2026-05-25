# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""HTML rendering for biological report bundles."""
from __future__ import annotations

from html import escape

from bijux_proteomics.workflow.biological_report_html_support import (
    _format_optional_float,
    _render_biological_report_section_confidence_table_html,
    _render_section_heading_html,
)
from bijux_proteomics.workflow.biological_report_models import (
    BiologicalReportSectionKey,
    BiologicalResultReportArtifactPaths,
    BiologicalResultReportBundle,
)

def _render_biological_result_report_html(
    report: BiologicalResultReportBundle,
    artifacts: BiologicalResultReportArtifactPaths,
) -> str:
    sections = [
        ("Differential proteins", artifacts.differential_tsv),
        ("Protein card summary", artifacts.protein_card_summary_tsv),
        ("Protein cards", artifacts.protein_card_tsv),
        ("Protein mechanism card summary", artifacts.protein_mechanism_card_summary_tsv),
        ("Protein mechanism cards", artifacts.protein_mechanism_card_tsv),
        (
            "Experiment confidence summary",
            artifacts.experiment_confidence_summary_tsv,
        ),
        (
            "Experiment confidence components",
            artifacts.experiment_confidence_components_tsv,
        ),
        (
            "Report section confidence",
            artifacts.section_confidence_tsv,
        ),
        (
            "Evidence-aware ranking",
            artifacts.evidence_aware_ranking_tsv,
        ),
        (
            "Claim validation summary",
            artifacts.claim_validation_summary_tsv,
        ),
        (
            "Supported biological claims",
            artifacts.supported_claim_tsv,
        ),
        (
            "Rejected biological claims",
            artifacts.rejected_claim_tsv,
        ),
        (
            "Biological hypothesis summary",
            artifacts.biological_hypothesis_summary_tsv,
        ),
        (
            "Biological hypotheses",
            artifacts.biological_hypothesis_tsv,
        ),
        (
            "Rejected hypothesis candidates",
            artifacts.rejected_hypothesis_candidate_tsv,
        ),
        (
            "Enrichment foreground/background summary",
            artifacts.foreground_background_summary_tsv,
        ),
        (
            "Enrichment foreground/background entries",
            artifacts.foreground_background_entry_tsv,
        ),
        (
            "Enrichment foreground/background issues",
            artifacts.foreground_background_issue_tsv,
        ),
        (
            "Regulator inference summary",
            artifacts.regulator_inference_summary_tsv,
        ),
        (
            "Regulator inference",
            artifacts.regulator_inference_tsv,
        ),
        (
            "Regulator inference unresolved targets",
            artifacts.regulator_inference_unresolved_tsv,
        ),
        (
            "Regulator evidence rejected rows",
            artifacts.regulator_evidence_rejected_tsv,
        ),
        ("Annotation summary", artifacts.annotation_summary_tsv),
        ("Annotated proteins", artifacts.annotation_tsv),
        ("Unmapped annotations", artifacts.annotation_unmapped_tsv),
        (
            "Biological context summary",
            artifacts.context_summary_tsv,
        ),
        (
            "Biological context mappings",
            artifacts.context_mapping_tsv,
        ),
        (
            "Biological context terms",
            artifacts.context_term_tsv,
        ),
        (
            "Biological context unmapped",
            artifacts.context_unmapped_tsv,
        ),
        (
            "Biological context rejected rows",
            artifacts.context_rejected_tsv,
        ),
        (
            "Cohort stratification summary",
            artifacts.cohort_stratification_summary_tsv,
        ),
        (
            "Cohort strata",
            artifacts.cohort_stratum_tsv,
        ),
        (
            "Cohort subgroup effects",
            artifacts.cohort_subgroup_effect_tsv,
        ),
        (
            "Cohort interaction candidates",
            artifacts.cohort_interaction_candidate_tsv,
        ),
        (
            "Tissue and cell-type context summary",
            artifacts.tissue_context_summary_tsv,
        ),
        (
            "Tissue and cell-type sample consistency",
            artifacts.tissue_context_sample_consistency_tsv,
        ),
        (
            "Tissue and cell-type unexpected signals",
            artifacts.tissue_context_unexpected_signal_tsv,
        ),
        (
            "Tissue and cell-type interpretations",
            artifacts.tissue_context_interpretation_tsv,
        ),
        (
            "Compartment biology summary",
            artifacts.compartment_biology_summary_tsv,
        ),
        (
            "Compartment enrichment",
            artifacts.compartment_enrichment_tsv,
        ),
        (
            "Compartment activity matrix",
            artifacts.compartment_activity_matrix_tsv,
        ),
        (
            "Compartment activity sample scores",
            artifacts.compartment_activity_sample_score_tsv,
        ),
        (
            "Compartment activity condition scores",
            artifacts.compartment_activity_condition_score_tsv,
        ),
        (
            "Compartment activity condition comparisons",
            artifacts.compartment_activity_condition_comparison_tsv,
        ),
        (
            "Compartment activity unresolved members",
            artifacts.compartment_activity_unresolved_member_tsv,
        ),
        (
            "Compartment unknown localization",
            artifacts.compartment_unknown_localization_tsv,
        ),
        (
            "Pathway activity summary",
            artifacts.pathway_activity_summary_tsv,
        ),
        (
            "Pathway activity matrix",
            artifacts.pathway_activity_matrix_tsv,
        ),
        (
            "Pathway activity sample scores",
            artifacts.pathway_activity_sample_score_tsv,
        ),
        (
            "Pathway activity condition scores",
            artifacts.pathway_activity_condition_score_tsv,
        ),
        (
            "Pathway activity condition comparisons",
            artifacts.pathway_activity_condition_comparison_tsv,
        ),
        (
            "Pathway activity member contributions",
            artifacts.pathway_activity_member_contribution_tsv,
        ),
        (
            "Pathway activity unresolved members",
            artifacts.pathway_activity_unresolved_member_tsv,
        ),
        (
            "Complex activity summary",
            artifacts.complex_activity_summary_tsv,
        ),
        (
            "Complex activity matrix",
            artifacts.complex_activity_matrix_tsv,
        ),
        (
            "Complex activity sample scores",
            artifacts.complex_activity_sample_score_tsv,
        ),
        (
            "Complex activity condition scores",
            artifacts.complex_activity_condition_score_tsv,
        ),
        (
            "Complex activity condition comparisons",
            artifacts.complex_activity_condition_comparison_tsv,
        ),
        (
            "Complex activity member contributions",
            artifacts.complex_activity_member_contribution_tsv,
        ),
        (
            "Complex activity unresolved members",
            artifacts.complex_activity_unresolved_member_tsv,
        ),
        ("Volcano TSV", artifacts.volcano_tsv),
        ("Volcano JSON", artifacts.volcano_json),
        ("Volcano SVG", artifacts.volcano_svg),
        ("Volcano HTML", artifacts.volcano_html),
        ("Heatmap summary", artifacts.heatmap_summary_tsv),
        ("Heatmap matrix", artifacts.heatmap_matrix_tsv),
        ("Sample PCA scores", artifacts.sample_pca_scores_tsv),
        ("Sample distances", artifacts.sample_distance_tsv),
        ("Sample clusters", artifacts.sample_cluster_tsv),
    ]
    if artifacts.go_term_tsv is not None:
        sections.append(("GO enrichment", artifacts.go_term_tsv))
    if artifacts.pathway_entry_tsv is not None:
        sections.append(("Pathway enrichment", artifacts.pathway_entry_tsv))
    if artifacts.complex_entry_tsv is not None:
        sections.append(("Complex enrichment", artifacts.complex_entry_tsv))
    if artifacts.drug_target_tsv is not None:
        sections.append(("Drug-target interpretation", artifacts.drug_target_tsv))
    if artifacts.disease_phenotype_term_tsv is not None:
        sections.append(
            (
                "Disease and phenotype interpretation",
                artifacts.disease_phenotype_term_tsv,
            )
        )
    section_html = "".join(
        f"<li><strong>{escape(label)}</strong>: <code>{escape(path)}</code></li>"
        for label, path in sections
        if path is not None
    )
    confidence_table_html = _render_experiment_confidence_table_html(report)
    ranking_table_html = _render_evidence_aware_ranking_table_html(report)
    claim_validation_html = _render_biological_claim_validation_table_html(report)
    hypothesis_html = _render_biological_hypothesis_table_html(report)
    foreground_background_html = _render_foreground_background_model_table_html(report)
    regulator_inference_html = _render_regulator_inference_table_html(report)
    drug_target_html = _render_drug_target_table_html(report)
    disease_phenotype_html = _render_disease_phenotype_table_html(report)
    cohort_stratification_html = _render_cohort_stratification_table_html(report)
    tissue_context_html = _render_tissue_cell_type_context_table_html(report)
    compartment_biology_html = _render_compartment_biology_table_html(report)
    pathway_activity_html = _render_pathway_activity_table_html(report)
    complex_activity_html = _render_complex_activity_table_html(report)
    card_table_html = _render_protein_mechanism_card_table_html(report)
    section_confidence_html = _render_biological_report_section_confidence_table_html(
        report
    )
    return (
        "<html><head><title>Bijux Proteomics Biological Report</title></head><body>"
        "<h1>Biological result report</h1>"
        f"<p><strong>Contrast</strong>: {escape(report.volcano_review.condition_a)} vs {escape(report.volcano_review.condition_b)}</p>"
        f"<p><strong>Proteins</strong>: {report.summary.protein_count} | "
        f"<strong>Significant</strong>: {report.summary.significant_protein_count} | "
        f"<strong>Protein cards</strong>: {report.summary.protein_card_count} | "
        f"<strong>Experiment confidence</strong>: {report.summary.experiment_confidence_score:.2f} "
        f"({escape(report.summary.experiment_confidence_tier)}) | "
        f"<strong>Cohort interaction candidates</strong>: "
        f"{report.summary.cohort_interaction_candidate_count} | "
        f"<strong>Tissue mismatch warnings</strong>: "
        f"{report.summary.tissue_mismatch_warning_count} | "
        f"<strong>Invalid sections</strong>: {report.summary.invalid_section_count} | "
        f"<strong>Annotated</strong>: {report.summary.annotation_entry_count} | "
        f"<strong>Heatmap rows</strong>: {report.summary.heatmap_entity_count}</p>"
        "<h2>Section confidence</h2>"
        f"{section_confidence_html}"
        f"{_render_section_heading_html(report, BiologicalReportSectionKey.EXPERIMENT_CONFIDENCE)}"
        f"{confidence_table_html}"
        f"{_render_section_heading_html(report, BiologicalReportSectionKey.EVIDENCE_AWARE_RANKING)}"
        f"{ranking_table_html}"
        f"{_render_section_heading_html(report, BiologicalReportSectionKey.VALIDATED_BIOLOGICAL_CLAIMS)}"
        f"{claim_validation_html}"
        f"{_render_section_heading_html(report, BiologicalReportSectionKey.BIOLOGICAL_HYPOTHESES)}"
        f"{hypothesis_html}"
        f"{_render_section_heading_html(report, BiologicalReportSectionKey.ENRICHMENT_FOREGROUND_BACKGROUND)}"
        f"{foreground_background_html}"
        f"{_render_section_heading_html(report, BiologicalReportSectionKey.REGULATOR_INFERENCE)}"
        f"{regulator_inference_html}"
        f"{_render_section_heading_html(report, BiologicalReportSectionKey.DRUG_TARGET_INTERPRETATION)}"
        f"{drug_target_html}"
        f"{_render_section_heading_html(report, BiologicalReportSectionKey.DISEASE_PHENOTYPE_INTERPRETATION)}"
        f"{disease_phenotype_html}"
        f"{_render_section_heading_html(report, BiologicalReportSectionKey.COHORT_STRATIFICATION)}"
        f"{cohort_stratification_html}"
        f"{_render_section_heading_html(report, BiologicalReportSectionKey.TISSUE_CELL_TYPE_CONTEXT)}"
        f"{tissue_context_html}"
        f"{_render_section_heading_html(report, BiologicalReportSectionKey.COMPARTMENT_BIOLOGY)}"
        f"{compartment_biology_html}"
        f"{_render_section_heading_html(report, BiologicalReportSectionKey.PATHWAY_ACTIVITY)}"
        f"{pathway_activity_html}"
        f"{_render_section_heading_html(report, BiologicalReportSectionKey.COMPLEX_ACTIVITY)}"
        f"{complex_activity_html}"
        f"{_render_section_heading_html(report, BiologicalReportSectionKey.PROTEIN_MECHANISM_CARDS)}"
        f"{card_table_html}"
        "<h2>Artifacts</h2>"
        f"<ul>{section_html}</ul>"
        f"<p>{escape(report.note)}</p>"
        "</body></html>\n"
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


def _render_protein_mechanism_card_table_html(report: BiologicalResultReportBundle) -> str:
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
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        "</table>"
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
        else "; ".join(
            f"{issue.severity.value}:{issue.code}" for issue in model.issues
        )
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


def _render_tissue_cell_type_context_table_html(
    report: BiologicalResultReportBundle,
) -> str:
    tissue_context_report = report.tissue_cell_type_context_report
    if tissue_context_report is None:
        return "<p>No tissue or cell-type context report was generated.</p>"
    headers = (
        "Sample",
        "Label",
        "Expected score",
        "Unexpected context",
        "Unexpected score",
        "QC warning",
        "Status",
    )
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = "".join(
        (
            "<tr>"
            f"<td>{escape(entry.sample_id)}</td>"
            f"<td>{escape(entry.tissue_or_cell_type or '-')}</td>"
            f"<td>{_format_optional_float(entry.expected_marker_score)}</td>"
            f"<td>{escape(entry.highest_unexpected_context_name or entry.highest_unexpected_context_id or '-')}</td>"
            f"<td>{_format_optional_float(entry.highest_unexpected_marker_score)}</td>"
            f"<td>{escape(str(entry.qc_warning).lower())}</td>"
            f"<td>{escape(entry.status.value)}</td>"
            "</tr>"
        )
        for entry in tissue_context_report.sample_consistency_entries[:10]
    )
    summary = tissue_context_report.summary
    return (
        "<p>"
        f"<strong>Samples</strong>: {summary.sample_count} | "
        f"<strong>Labeled</strong>: {summary.labeled_sample_count} | "
        f"<strong>Marker contexts</strong>: {summary.marker_context_count} | "
        f"<strong>QC warnings</strong>: {summary.mismatch_warning_count} | "
        f"<strong>Unexpected signals</strong>: {summary.unexpected_signal_count}"
        "</p>"
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        "</table>"
    )


def _render_cohort_stratification_table_html(
    report: BiologicalResultReportBundle,
) -> str:
    cohort_report = report.cohort_stratification_report
    if cohort_report is None:
        return "<p>No cohort stratification report was generated.</p>"
    headers = (
        "Field",
        "Left subgroup",
        "Right subgroup",
        "Entity",
        "Kind",
        "Delta",
    )
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = "".join(
        (
            "<tr>"
            f"<td>{escape(entry.field_name.value)}</td>"
            f"<td>{escape(entry.left_subgroup_value)}</td>"
            f"<td>{escape(entry.right_subgroup_value)}</td>"
            f"<td>{escape(entry.entity_id)}</td>"
            f"<td>{escape(entry.candidate_kind.value)}</td>"
            f"<td>{entry.interaction_delta:.4f}</td>"
            "</tr>"
        )
        for entry in cohort_report.interaction_candidates[:10]
    )
    summary = cohort_report.summary
    return (
        "<p>"
        f"<strong>Fields</strong>: {summary.field_count} | "
        f"<strong>Supported strata</strong>: {summary.supported_stratum_count} | "
        f"<strong>Blocked strata</strong>: {summary.blocked_stratum_count} | "
        f"<strong>Subgroup effects</strong>: {summary.subgroup_effect_count} | "
        f"<strong>Interaction candidates</strong>: {summary.interaction_candidate_count}"
        "</p>"
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        "</table>"
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
        for entry in compartment_biology_report.activity_report.condition_comparisons[:10]
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


def _render_pathway_activity_table_html(report: BiologicalResultReportBundle) -> str:
    pathway_activity_report = report.pathway_activity_report
    if pathway_activity_report is None:
        return "<p>No pathway activity report was generated.</p>"
    headers = (
        "Pathway",
        "Condition A",
        "Condition B",
        "Delta",
        "Comparison confidence",
    )
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = "".join(
        (
            "<tr>"
            f"<td>{escape(entry.pathway_name or entry.pathway_id)}</td>"
            f"<td>{escape(entry.condition_a)}</td>"
            f"<td>{escape(entry.condition_b)}</td>"
            f"<td>{_format_optional_float(entry.activity_score_delta)}</td>"
            f"<td>{escape(entry.comparison_confidence_status.value)}</td>"
            "</tr>"
        )
        for entry in pathway_activity_report.condition_comparisons[:10]
    )
    return (
        "<p>"
        f"<strong>Pathways</strong>: {pathway_activity_report.summary.pathway_count} | "
        f"<strong>Low-confidence sample scores</strong>: "
        f"{pathway_activity_report.summary.low_confidence_sample_score_count} | "
        f"<strong>Unresolved members</strong>: "
        f"{pathway_activity_report.summary.unresolved_member_count}"
        "</p>"
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        "</table>"
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


__all__ = ["_render_biological_result_report_html"]
