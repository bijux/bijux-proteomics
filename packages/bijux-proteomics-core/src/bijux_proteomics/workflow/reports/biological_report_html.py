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
from bijux_proteomics.workflow.reports.biological_report_html_artifact_inventory import (
    _render_biological_report_artifact_inventory_html,
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


__all__ = ["_render_biological_result_report_html"]
