# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Biological report artifact-path and manifest assembly."""

from __future__ import annotations

from bijux_proteomics.workflow.reports.biological_report_activity_exports import (
    BiologicalActivityExportNames,
)
from bijux_proteomics.workflow.reports.biological_report_contextual_exports import (
    BiologicalContextualExportNames,
)
from bijux_proteomics.workflow.reports.biological_report_enrichment_exports import (
    BiologicalEnrichmentExportNames,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportArtifactPaths,
    BiologicalResultReportBundle,
    BiologicalResultReportExportManifest,
)
from bijux_proteomics.workflow.reports.biological_report_scientific_exports import (
    BiologicalScientificExportNames,
)
from bijux_proteomics.workflow.reports.biological_report_visual_exports import (
    BiologicalVisualExportNames,
)


def _build_biological_result_report_artifact_paths(
    scientific_export_names: BiologicalScientificExportNames,
    contextual_export_names: BiologicalContextualExportNames,
    activity_export_names: BiologicalActivityExportNames,
    enrichment_export_names: BiologicalEnrichmentExportNames,
    visual_export_names: BiologicalVisualExportNames,
) -> BiologicalResultReportArtifactPaths:
    return BiologicalResultReportArtifactPaths(
        summary_tsv=scientific_export_names.summary_name,
        differential_tsv=scientific_export_names.differential_name,
        protein_card_summary_tsv=scientific_export_names.protein_card_summary_name,
        protein_card_tsv=scientific_export_names.protein_card_name,
        pathway_card_tsv=activity_export_names.pathway_card_name,
        protein_mechanism_card_summary_tsv=(
            scientific_export_names.protein_mechanism_card_summary_name
        ),
        protein_mechanism_card_tsv=scientific_export_names.protein_mechanism_card_name,
        evidence_graph_nodes_tsv=scientific_export_names.evidence_graph_nodes_name,
        evidence_graph_edges_tsv=scientific_export_names.evidence_graph_edges_name,
        experiment_confidence_summary_tsv=(
            scientific_export_names.experiment_confidence_summary_name
        ),
        experiment_confidence_components_tsv=(
            scientific_export_names.experiment_confidence_components_name
        ),
        section_confidence_tsv=scientific_export_names.section_confidence_name,
        evidence_aware_ranking_tsv=scientific_export_names.evidence_aware_ranking_name,
        claim_validation_summary_tsv=(
            scientific_export_names.claim_validation_summary_name
        ),
        supported_claim_tsv=scientific_export_names.supported_claim_name,
        rejected_claim_tsv=scientific_export_names.rejected_claim_name,
        biological_hypothesis_summary_tsv=(
            scientific_export_names.biological_hypothesis_summary_name
        ),
        biological_hypothesis_tsv=scientific_export_names.biological_hypothesis_name,
        rejected_hypothesis_candidate_tsv=(
            scientific_export_names.rejected_hypothesis_candidate_name
        ),
        foreground_background_summary_tsv=(
            scientific_export_names.foreground_background_summary_name
        ),
        foreground_background_entry_tsv=(
            scientific_export_names.foreground_background_entry_name
        ),
        foreground_background_issue_tsv=(
            scientific_export_names.foreground_background_issue_name
        ),
        regulator_inference_summary_tsv=(
            scientific_export_names.regulator_inference_summary_name
        ),
        regulator_inference_tsv=scientific_export_names.regulator_inference_name,
        regulator_inference_unresolved_tsv=(
            scientific_export_names.regulator_unresolved_name
        ),
        regulator_evidence_rejected_tsv=scientific_export_names.regulator_rejected_name,
        annotation_summary_tsv=scientific_export_names.annotation_summary_name,
        annotation_tsv=scientific_export_names.annotation_name,
        annotation_unmapped_tsv=scientific_export_names.annotation_unmapped_name,
        context_summary_tsv=contextual_export_names.context_summary_name,
        context_mapping_tsv=contextual_export_names.context_mapping_name,
        context_term_tsv=contextual_export_names.context_term_name,
        context_unmapped_tsv=contextual_export_names.context_unmapped_name,
        context_rejected_tsv=contextual_export_names.context_rejected_name,
        cohort_stratification_summary_tsv=contextual_export_names.cohort_summary_name,
        cohort_stratum_tsv=contextual_export_names.cohort_stratum_name,
        cohort_subgroup_effect_tsv=contextual_export_names.cohort_effect_name,
        cohort_interaction_candidate_tsv=(
            contextual_export_names.cohort_interaction_name
        ),
        tissue_context_summary_tsv=contextual_export_names.tissue_context_summary_name,
        tissue_context_sample_consistency_tsv=(
            contextual_export_names.tissue_context_sample_name
        ),
        tissue_context_unexpected_signal_tsv=(
            contextual_export_names.tissue_context_unexpected_name
        ),
        tissue_context_interpretation_tsv=(
            contextual_export_names.tissue_context_interpretation_name
        ),
        drug_target_summary_tsv=contextual_export_names.drug_target_summary_name,
        drug_target_tsv=contextual_export_names.drug_target_name,
        disease_phenotype_summary_tsv=(
            contextual_export_names.disease_phenotype_summary_name
        ),
        disease_phenotype_term_tsv=contextual_export_names.disease_phenotype_term_name,
        disease_phenotype_unknown_annotation_tsv=(
            contextual_export_names.disease_phenotype_unknown_name
        ),
        compartment_biology_summary_tsv=activity_export_names.compartment_summary_name,
        compartment_enrichment_tsv=activity_export_names.compartment_enrichment_name,
        compartment_activity_matrix_tsv=(
            activity_export_names.compartment_activity_matrix_name
        ),
        compartment_activity_sample_score_tsv=(
            activity_export_names.compartment_activity_sample_name
        ),
        compartment_activity_condition_score_tsv=(
            activity_export_names.compartment_activity_condition_name
        ),
        compartment_activity_condition_comparison_tsv=(
            activity_export_names.compartment_activity_comparison_name
        ),
        compartment_activity_unresolved_member_tsv=(
            activity_export_names.compartment_activity_unresolved_name
        ),
        compartment_unknown_localization_tsv=(
            activity_export_names.compartment_unknown_name
        ),
        pathway_activity_summary_tsv=activity_export_names.pathway_activity_summary_name,
        pathway_activity_matrix_tsv=activity_export_names.pathway_activity_matrix_name,
        pathway_activity_sample_score_tsv=activity_export_names.pathway_activity_sample_name,
        pathway_activity_condition_score_tsv=(
            activity_export_names.pathway_activity_condition_name
        ),
        pathway_activity_condition_comparison_tsv=(
            activity_export_names.pathway_activity_comparison_name
        ),
        pathway_activity_member_contribution_tsv=(
            activity_export_names.pathway_activity_member_name
        ),
        pathway_activity_unresolved_member_tsv=(
            activity_export_names.pathway_activity_unresolved_name
        ),
        complex_activity_summary_tsv=activity_export_names.complex_activity_summary_name,
        complex_activity_matrix_tsv=activity_export_names.complex_activity_matrix_name,
        complex_activity_sample_score_tsv=activity_export_names.complex_activity_sample_name,
        complex_activity_condition_score_tsv=(
            activity_export_names.complex_activity_condition_name
        ),
        complex_activity_condition_comparison_tsv=(
            activity_export_names.complex_activity_comparison_name
        ),
        complex_activity_member_contribution_tsv=(
            activity_export_names.complex_activity_member_name
        ),
        complex_activity_unresolved_member_tsv=(
            activity_export_names.complex_activity_unresolved_name
        ),
        volcano_tsv=visual_export_names.volcano_tsv_name,
        volcano_json=visual_export_names.volcano_json_name,
        volcano_svg=visual_export_names.volcano_svg_name,
        volcano_html=visual_export_names.volcano_html_name,
        heatmap_summary_tsv=visual_export_names.heatmap_summary_name,
        heatmap_matrix_tsv=visual_export_names.heatmap_matrix_name,
        heatmap_row_metadata_tsv=visual_export_names.heatmap_row_name,
        heatmap_column_metadata_tsv=visual_export_names.heatmap_column_name,
        sample_exploration_summary_tsv=visual_export_names.sample_summary_name,
        sample_pca_scores_tsv=visual_export_names.sample_scores_name,
        sample_pca_variance_tsv=visual_export_names.sample_variance_name,
        sample_distance_tsv=visual_export_names.sample_distance_name,
        sample_cluster_tsv=visual_export_names.sample_cluster_name,
        sample_card_tsv=visual_export_names.sample_card_name,
        report_html=visual_export_names.report_html_name,
        go_summary_tsv=enrichment_export_names.go_summary_name,
        go_term_tsv=enrichment_export_names.go_term_name,
        go_unannotated_tsv=enrichment_export_names.go_unannotated_name,
        pathway_summary_tsv=enrichment_export_names.pathway_summary_name,
        pathway_entry_tsv=enrichment_export_names.pathway_entry_name,
        pathway_unresolved_tsv=enrichment_export_names.pathway_unresolved_name,
        complex_summary_tsv=enrichment_export_names.complex_summary_name,
        complex_entry_tsv=enrichment_export_names.complex_entry_name,
        complex_unresolved_tsv=enrichment_export_names.complex_unresolved_name,
    )


def _build_biological_result_report_export_manifest(
    report: BiologicalResultReportBundle,
    artifacts: BiologicalResultReportArtifactPaths,
) -> BiologicalResultReportExportManifest:
    return BiologicalResultReportExportManifest(
        summary=report.summary,
        artifacts=artifacts,
        claim_validation_included=report.claim_validation_report is not None,
        hypothesis_summary_included=report.biological_hypothesis_report is not None,
        context_summary_included=report.context_mapping_report is not None,
        cohort_stratification_summary_included=(
            report.cohort_stratification_report is not None
        ),
        tissue_context_summary_included=report.tissue_cell_type_context_report
        is not None,
        drug_target_summary_included=report.drug_target_report is not None,
        disease_phenotype_summary_included=report.disease_phenotype_report is not None,
        go_summary_included=report.go_enrichment_report is not None,
        pathway_summary_included=report.pathway_enrichment_report is not None,
        complex_summary_included=report.complex_enrichment_report is not None,
        note=(
            "biological report export writes stable differential, explicit "
            "foreground/background enrichment inputs, protein-card, "
            "protein-mechanism-card, annotation, optional biological hypotheses, "
            "optional biological context, optional cohort stratification, "
            "optional tissue and cell-type context, enrichment, volcano, heatmap, "
            "and sample exploration artifacts into one durable output directory"
        ),
    )


__all__ = [
    "_build_biological_result_report_artifact_paths",
    "_build_biological_result_report_export_manifest",
]
