# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Biological report page orchestration and artifact inventory HTML."""

from __future__ import annotations

from html import escape

from bijux_proteomics.workflow.reports.biological_report_html_contextual_tables import (
    _render_cohort_stratification_table_html,
    _render_compartment_biology_table_html,
    _render_complex_activity_table_html,
    _render_disease_phenotype_table_html,
    _render_drug_target_table_html,
    _render_pathway_activity_table_html,
    _render_regulator_inference_table_html,
    _render_tissue_cell_type_context_table_html,
)
from bijux_proteomics.workflow.reports.biological_report_html_scientific_tables import (
    _render_biological_claim_validation_table_html,
    _render_biological_hypothesis_table_html,
    _render_evidence_aware_ranking_table_html,
    _render_experiment_confidence_table_html,
    _render_foreground_background_model_table_html,
    _render_protein_mechanism_card_table_html,
)
from bijux_proteomics.workflow.reports.biological_report_html_support import (
    _render_biological_report_section_confidence_table_html,
    _render_section_heading_html,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalReportSectionKey,
    BiologicalResultReportArtifactPaths,
    BiologicalResultReportBundle,
)


def _render_biological_result_report_html(
    report: BiologicalResultReportBundle,
    artifacts: BiologicalResultReportArtifactPaths,
) -> str:
    section_html = _render_biological_report_artifact_inventory_html(artifacts)
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


def _render_biological_report_artifact_inventory_html(
    artifacts: BiologicalResultReportArtifactPaths,
) -> str:
    sections = [
        ("Differential proteins", artifacts.differential_tsv),
        ("Protein card summary", artifacts.protein_card_summary_tsv),
        ("Protein cards", artifacts.protein_card_tsv),
        ("Pathway cards", artifacts.pathway_card_tsv),
        (
            "Protein mechanism card summary",
            artifacts.protein_mechanism_card_summary_tsv,
        ),
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
        ("Sample cards", artifacts.sample_card_tsv),
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
    return "".join(
        f"<li><strong>{escape(label)}</strong>: <code>{escape(path)}</code></li>"
        for label, path in sections
        if path is not None
    )
__all__ = ["_render_biological_result_report_html"]
