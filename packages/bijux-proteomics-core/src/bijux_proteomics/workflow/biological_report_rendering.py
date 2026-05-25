# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Biological report TSV rendering and artifact export."""
from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

from bijux_proteomics.interpretation import (
    render_biological_context_mapping_summary_tsv,
    render_biological_context_mapping_tsv,
    render_biological_context_term_tsv,
    render_biological_foreground_background_entry_tsv,
    render_biological_foreground_background_issue_tsv,
    render_biological_foreground_background_summary_tsv,
    render_complex_activity_condition_comparison_tsv,
    render_complex_activity_condition_score_tsv,
    render_complex_activity_matrix_tsv,
    render_complex_activity_sample_score_tsv,
    render_complex_activity_summary_tsv,
    render_complex_activity_unresolved_member_tsv,
    render_complex_enrichment_entry_tsv,
    render_complex_enrichment_summary_tsv,
    render_complex_member_contribution_tsv,
    render_complex_unresolved_member_tsv,
    render_drug_target_interpretation_summary_tsv,
    render_drug_target_interpretation_tsv,
    render_disease_phenotype_interpretation_summary_tsv,
    render_disease_phenotype_interpretation_tsv,
    render_go_enrichment_summary_tsv,
    render_go_enrichment_term_tsv,
    render_go_enrichment_unannotated_tsv,
    render_pathway_activity_condition_comparison_tsv,
    render_pathway_activity_condition_score_tsv,
    render_pathway_activity_matrix_tsv,
    render_pathway_activity_sample_score_tsv,
    render_pathway_activity_summary_tsv,
    render_pathway_activity_unresolved_member_tsv,
    render_pathway_enrichment_entry_tsv,
    render_pathway_enrichment_summary_tsv,
    render_pathway_member_contribution_tsv,
    render_pathway_unresolved_member_tsv,
    render_protein_annotation_summary_tsv,
    render_protein_annotation_tsv,
    render_rejected_biological_context_tsv,
    render_rejected_regulator_evidence_tsv,
    render_regulator_inference_summary_tsv,
    render_regulator_inference_tsv,
    render_tissue_cell_type_context_summary_tsv,
    render_tissue_cell_type_interpretation_tsv,
    render_tissue_cell_type_sample_consistency_tsv,
    render_tissue_cell_type_unexpected_signal_tsv,
    render_unknown_disease_phenotype_annotation_tsv,
    render_unmapped_biological_context_tsv,
    render_unmapped_protein_annotation_tsv,
    render_unresolved_regulator_target_tsv,
)
from bijux_proteomics.interpretation.compartment_biology import (
    render_compartment_activity_condition_comparison_tsv,
    render_compartment_activity_condition_score_tsv,
    render_compartment_activity_matrix_tsv,
    render_compartment_activity_sample_score_tsv,
    render_compartment_activity_unresolved_member_tsv,
    render_compartment_biology_summary_tsv,
    render_compartment_enrichment_tsv,
    render_unknown_compartment_localization_tsv,
)
from bijux_proteomics.quantification import (
    export_heatmap_column_metadata_tsv,
    export_heatmap_matrix_tsv,
    export_heatmap_row_metadata_tsv,
    export_heatmap_summary_tsv,
    export_sample_cluster_tsv,
    export_sample_distance_tsv,
    export_sample_exploration_summary_tsv,
    export_sample_pca_scores_tsv,
    export_sample_pca_variance_tsv,
    render_differential_abundance_tsv,
)
from bijux_proteomics.review import (
    export_proteomics_evidence_graph,
    export_volcano_review_html,
    export_volcano_review_json,
    export_volcano_review_svg,
    render_biological_claim_validation_summary_tsv,
    render_biological_hypothesis_summary_tsv,
    render_biological_hypothesis_tsv,
    render_evidence_aware_ranking_tsv,
    render_proteomics_evidence_graph_edges_tsv,
    render_proteomics_evidence_graph_nodes_tsv,
    render_rejected_biological_claim_tsv,
    render_rejected_biological_hypothesis_candidate_tsv,
    render_supported_biological_claim_tsv,
    render_volcano_review_tsv,
)
from bijux_proteomics.study import (
    render_experiment_confidence_component_tsv,
    render_experiment_confidence_summary_tsv,
)
from bijux_proteomics.workflow.biological_report_html import (
    _render_biological_result_report_html,
)
from bijux_proteomics.workflow.biological_report_models import (
    BiologicalResultReportArtifactPaths,
    BiologicalResultReportBundle,
    BiologicalResultReportExportManifest,
)
from bijux_proteomics.workflow.artifact_layout import synchronize_workflow_artifact_layout
from bijux_proteomics.workflow.cohort_stratification import (
    render_cohort_interaction_candidate_tsv,
    render_cohort_stratification_summary_tsv,
    render_cohort_stratum_tsv,
    render_cohort_subgroup_effect_tsv,
)
from bijux_proteomics.workflow.protein_evidence_cards import (
    render_protein_evidence_card_summary_tsv,
    render_protein_evidence_card_tsv,
)
from bijux_proteomics.workflow.protein_mechanism_cards import (
    render_protein_mechanism_card_summary_tsv,
    render_protein_mechanism_card_tsv,
)

def render_biological_result_report_summary_tsv(
    report: BiologicalResultReportBundle,
) -> str:
    """Render one biological result report summary as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    writer.writerow(("condition_a", report.volcano_review.condition_a))
    writer.writerow(("condition_b", report.volcano_review.condition_b))
    writer.writerow(("protein_count", report.summary.protein_count))
    writer.writerow(
        ("significant_protein_count", report.summary.significant_protein_count)
    )
    writer.writerow(("sample_count", report.summary.sample_count))
    writer.writerow(("annotation_entry_count", report.summary.annotation_entry_count))
    writer.writerow(
        ("annotation_unmapped_count", report.summary.annotation_unmapped_count)
    )
    writer.writerow(("protein_card_count", report.summary.protein_card_count))
    writer.writerow(("warning_card_count", report.summary.warning_card_count))
    writer.writerow(
        ("tissue_mismatch_warning_count", report.summary.tissue_mismatch_warning_count)
    )
    writer.writerow(
        ("cohort_blocked_stratum_count", report.summary.cohort_blocked_stratum_count)
    )
    writer.writerow(
        (
            "cohort_subgroup_effect_count",
            report.summary.cohort_subgroup_effect_count,
        )
    )
    writer.writerow(
        (
            "cohort_interaction_candidate_count",
            report.summary.cohort_interaction_candidate_count,
        )
    )
    writer.writerow(
        (
            "experiment_confidence_score",
            f"{report.summary.experiment_confidence_score:.4f}",
        )
    )
    writer.writerow(
        ("experiment_confidence_tier", report.summary.experiment_confidence_tier)
    )
    writer.writerow(
        (
            "low_confidence_component_count",
            report.summary.low_confidence_component_count,
        )
    )
    writer.writerow(
        (
            "high_confidence_section_count",
            report.summary.high_confidence_section_count,
        )
    )
    writer.writerow(
        (
            "moderate_confidence_section_count",
            report.summary.moderate_confidence_section_count,
        )
    )
    writer.writerow(
        (
            "weak_confidence_section_count",
            report.summary.weak_confidence_section_count,
        )
    )
    writer.writerow(
        (
            "exploratory_section_count",
            report.summary.exploratory_section_count,
        )
    )
    writer.writerow(
        (
            "invalid_section_count",
            report.summary.invalid_section_count,
        )
    )
    writer.writerow(("context_entry_count", report.summary.context_entry_count))
    writer.writerow(("context_unmapped_count", report.summary.context_unmapped_count))
    writer.writerow(("context_term_count", report.summary.context_term_count))
    writer.writerow(("go_enriched_term_count", report.summary.go_enriched_term_count))
    writer.writerow(
        ("pathway_enriched_entry_count", report.summary.pathway_enriched_entry_count)
    )
    writer.writerow(
        ("complex_enriched_entry_count", report.summary.complex_enriched_entry_count)
    )
    writer.writerow(("heatmap_entity_count", report.summary.heatmap_entity_count))
    writer.writerow(
        ("pca_outlier_sample_count", report.summary.pca_outlier_sample_count)
    )
    writer.writerow(("note", report.note))
    return handle.getvalue()


def render_biological_report_section_confidence_tsv(
    report: BiologicalResultReportBundle,
) -> str:
    """Render derived biological report section confidence labels as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("section_key", "section_title", "confidence_label", "rationale"))
    for entry in report.section_confidence_entries:
        writer.writerow(
            (
                entry.section_key.value,
                entry.section_title,
                entry.confidence_label.value,
                entry.rationale,
            )
        )
    return handle.getvalue()


def write_biological_result_report_bundle(
    report: BiologicalResultReportBundle,
    output_dir: Path,
) -> BiologicalResultReportExportManifest:
    """Write one biological result bundle into a stable output directory."""

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_name = "biological_report_summary.tsv"
    differential_name = "biological_differential.tsv"
    protein_card_summary_name = "biological_protein_card_summary.tsv"
    protein_card_name = "biological_protein_cards.tsv"
    protein_mechanism_card_summary_name = "biological_protein_mechanism_card_summary.tsv"
    protein_mechanism_card_name = "biological_protein_mechanism_cards.tsv"
    evidence_graph_nodes_name = "biological_evidence_graph_nodes.tsv"
    evidence_graph_edges_name = "biological_evidence_graph_edges.tsv"
    experiment_confidence_summary_name = "biological_experiment_confidence_summary.tsv"
    experiment_confidence_components_name = (
        "biological_experiment_confidence_components.tsv"
    )
    section_confidence_name = "biological_report_section_confidence.tsv"
    evidence_aware_ranking_name = None
    claim_validation_summary_name = None
    supported_claim_name = None
    rejected_claim_name = None
    foreground_background_summary_name = (
        "biological_enrichment_foreground_background_summary.tsv"
    )
    foreground_background_entry_name = (
        "biological_enrichment_foreground_background_entries.tsv"
    )
    foreground_background_issue_name = (
        "biological_enrichment_foreground_background_issues.tsv"
    )
    regulator_inference_summary_name = None
    regulator_inference_name = None
    regulator_unresolved_name = None
    regulator_rejected_name = None
    annotation_summary_name = "biological_annotation_summary.tsv"
    annotation_name = "biological_annotations.tsv"
    annotation_unmapped_name = "biological_annotation_unmapped.tsv"
    context_summary_name = None
    context_mapping_name = None
    context_term_name = None
    context_unmapped_name = None
    context_rejected_name = None
    drug_target_summary_name = None
    drug_target_name = None
    disease_phenotype_summary_name = None
    disease_phenotype_term_name = None
    disease_phenotype_unknown_name = None
    pathway_activity_summary_name = None
    pathway_activity_matrix_name = None
    pathway_activity_sample_name = None
    pathway_activity_condition_name = None
    pathway_activity_comparison_name = None
    pathway_activity_member_name = None
    pathway_activity_unresolved_name = None
    volcano_tsv_name = "biological_volcano.tsv"
    volcano_json_name = "biological_volcano.json"
    volcano_svg_name = "biological_volcano.svg"
    volcano_html_name = "biological_volcano.html"
    heatmap_summary_name = "biological_heatmap_summary.tsv"
    heatmap_matrix_name = "biological_heatmap_matrix.tsv"
    heatmap_row_name = "biological_heatmap_rows.tsv"
    heatmap_column_name = "biological_heatmap_columns.tsv"
    sample_summary_name = "biological_sample_exploration_summary.tsv"
    sample_scores_name = "biological_sample_pca_scores.tsv"
    sample_variance_name = "biological_sample_pca_variance.tsv"
    sample_distance_name = "biological_sample_distances.tsv"
    sample_cluster_name = "biological_sample_clusters.tsv"
    report_html_name = "biological_report.html"
    evidence_aware_ranking_name = None
    claim_validation_summary_name = None
    supported_claim_name = None
    rejected_claim_name = None
    biological_hypothesis_summary_name = None
    biological_hypothesis_name = None
    rejected_hypothesis_candidate_name = None

    (output_dir / summary_name).write_text(
        render_biological_result_report_summary_tsv(report),
        encoding="utf-8",
    )
    (output_dir / differential_name).write_text(
        render_differential_abundance_tsv(report.differential_report),
        encoding="utf-8",
    )
    (output_dir / protein_card_summary_name).write_text(
        render_protein_evidence_card_summary_tsv(report.protein_cards),
        encoding="utf-8",
    )
    (output_dir / protein_card_name).write_text(
        render_protein_evidence_card_tsv(report.protein_cards),
        encoding="utf-8",
    )
    (output_dir / protein_mechanism_card_summary_name).write_text(
        render_protein_mechanism_card_summary_tsv(report.protein_mechanism_cards),
        encoding="utf-8",
    )
    (output_dir / protein_mechanism_card_name).write_text(
        render_protein_mechanism_card_tsv(report.protein_mechanism_cards),
        encoding="utf-8",
    )
    graph_export = export_proteomics_evidence_graph(report.graph_report.graph)
    (output_dir / evidence_graph_nodes_name).write_text(
        render_proteomics_evidence_graph_nodes_tsv(graph_export),
        encoding="utf-8",
    )
    (output_dir / evidence_graph_edges_name).write_text(
        render_proteomics_evidence_graph_edges_tsv(graph_export),
        encoding="utf-8",
    )
    (output_dir / experiment_confidence_summary_name).write_text(
        render_experiment_confidence_summary_tsv(report.experiment_confidence_report),
        encoding="utf-8",
    )
    (output_dir / experiment_confidence_components_name).write_text(
        render_experiment_confidence_component_tsv(report.experiment_confidence_report),
        encoding="utf-8",
    )
    (output_dir / section_confidence_name).write_text(
        render_biological_report_section_confidence_tsv(report),
        encoding="utf-8",
    )
    if report.evidence_aware_ranking_report is not None:
        evidence_aware_ranking_name = "biological_evidence_aware_ranking.tsv"
        (output_dir / evidence_aware_ranking_name).write_text(
            render_evidence_aware_ranking_tsv(report.evidence_aware_ranking_report),
            encoding="utf-8",
        )
    if report.claim_validation_report is not None:
        claim_validation_summary_name = "biological_claim_validation_summary.tsv"
        supported_claim_name = "biological_supported_claims.tsv"
        rejected_claim_name = "biological_rejected_claims.tsv"
        (output_dir / claim_validation_summary_name).write_text(
            render_biological_claim_validation_summary_tsv(
                report.claim_validation_report
            ),
            encoding="utf-8",
        )
        (output_dir / supported_claim_name).write_text(
            render_supported_biological_claim_tsv(report.claim_validation_report),
            encoding="utf-8",
        )
        (output_dir / rejected_claim_name).write_text(
            render_rejected_biological_claim_tsv(report.claim_validation_report),
            encoding="utf-8",
        )
    if report.biological_hypothesis_report is not None:
        biological_hypothesis_summary_name = "biological_hypothesis_summary.tsv"
        biological_hypothesis_name = "biological_hypotheses.tsv"
        rejected_hypothesis_candidate_name = (
            "biological_rejected_hypothesis_candidates.tsv"
        )
        (output_dir / biological_hypothesis_summary_name).write_text(
            render_biological_hypothesis_summary_tsv(report.biological_hypothesis_report),
            encoding="utf-8",
        )
        (output_dir / biological_hypothesis_name).write_text(
            render_biological_hypothesis_tsv(report.biological_hypothesis_report),
            encoding="utf-8",
        )
        (output_dir / rejected_hypothesis_candidate_name).write_text(
            render_rejected_biological_hypothesis_candidate_tsv(
                report.biological_hypothesis_report
            ),
            encoding="utf-8",
        )
    (output_dir / foreground_background_summary_name).write_text(
        render_biological_foreground_background_summary_tsv(
            report.foreground_background_model
        ),
        encoding="utf-8",
    )
    (output_dir / foreground_background_entry_name).write_text(
        render_biological_foreground_background_entry_tsv(
            report.foreground_background_model
        ),
        encoding="utf-8",
    )
    (output_dir / foreground_background_issue_name).write_text(
        render_biological_foreground_background_issue_tsv(
            report.foreground_background_model
        ),
        encoding="utf-8",
    )
    if (
        report.regulator_evidence_import_report is not None
        and report.regulator_inference_report is not None
    ):
        regulator_inference_summary_name = "biological_regulator_inference_summary.tsv"
        regulator_inference_name = "biological_regulator_inference.tsv"
        regulator_unresolved_name = "biological_regulator_inference_unresolved.tsv"
        regulator_rejected_name = "biological_regulator_evidence_rejected.tsv"
        (output_dir / regulator_inference_summary_name).write_text(
            render_regulator_inference_summary_tsv(report.regulator_inference_report),
            encoding="utf-8",
        )
        (output_dir / regulator_inference_name).write_text(
            render_regulator_inference_tsv(report.regulator_inference_report),
            encoding="utf-8",
        )
        (output_dir / regulator_unresolved_name).write_text(
            render_unresolved_regulator_target_tsv(report.regulator_inference_report),
            encoding="utf-8",
        )
        (output_dir / regulator_rejected_name).write_text(
            render_rejected_regulator_evidence_tsv(
                report.regulator_evidence_import_report
            ),
            encoding="utf-8",
        )
    (output_dir / annotation_summary_name).write_text(
        render_protein_annotation_summary_tsv(report.annotation_report),
        encoding="utf-8",
    )
    (output_dir / annotation_name).write_text(
        render_protein_annotation_tsv(report.annotation_report),
        encoding="utf-8",
    )
    (output_dir / annotation_unmapped_name).write_text(
        render_unmapped_protein_annotation_tsv(report.annotation_report),
        encoding="utf-8",
    )
    if (
        report.context_import_report is not None
        and report.context_mapping_report is not None
    ):
        context_summary_name = "biological_context_summary.tsv"
        context_mapping_name = "biological_context_mappings.tsv"
        context_term_name = "biological_context_terms.tsv"
        context_unmapped_name = "biological_context_unmapped.tsv"
        context_rejected_name = "biological_context_rejected.tsv"
        (output_dir / context_summary_name).write_text(
            render_biological_context_mapping_summary_tsv(report.context_mapping_report),
            encoding="utf-8",
        )
        (output_dir / context_mapping_name).write_text(
            render_biological_context_mapping_tsv(report.context_mapping_report),
            encoding="utf-8",
        )
        (output_dir / context_term_name).write_text(
            render_biological_context_term_tsv(report.context_mapping_report),
            encoding="utf-8",
        )
        (output_dir / context_unmapped_name).write_text(
            render_unmapped_biological_context_tsv(report.context_mapping_report),
            encoding="utf-8",
        )
        (output_dir / context_rejected_name).write_text(
            render_rejected_biological_context_tsv(report.context_import_report),
            encoding="utf-8",
        )
    else:
        context_summary_name = None
        context_mapping_name = None
        context_term_name = None
        context_unmapped_name = None
        context_rejected_name = None
    if report.cohort_stratification_report is not None:
        cohort_summary_name = "biological_cohort_stratification_summary.tsv"
        cohort_stratum_name = "biological_cohort_strata.tsv"
        cohort_effect_name = "biological_cohort_subgroup_effects.tsv"
        cohort_interaction_name = "biological_cohort_interaction_candidates.tsv"
        (output_dir / cohort_summary_name).write_text(
            render_cohort_stratification_summary_tsv(
                report.cohort_stratification_report
            ),
            encoding="utf-8",
        )
        (output_dir / cohort_stratum_name).write_text(
            render_cohort_stratum_tsv(report.cohort_stratification_report),
            encoding="utf-8",
        )
        (output_dir / cohort_effect_name).write_text(
            render_cohort_subgroup_effect_tsv(report.cohort_stratification_report),
            encoding="utf-8",
        )
        (output_dir / cohort_interaction_name).write_text(
            render_cohort_interaction_candidate_tsv(
                report.cohort_stratification_report
            ),
            encoding="utf-8",
        )
    else:
        cohort_summary_name = None
        cohort_stratum_name = None
        cohort_effect_name = None
        cohort_interaction_name = None
    if report.tissue_cell_type_context_report is not None:
        tissue_context_summary_name = "biological_tissue_context_summary.tsv"
        tissue_context_sample_name = "biological_tissue_context_sample_consistency.tsv"
        tissue_context_unexpected_name = "biological_tissue_context_unexpected_signals.tsv"
        tissue_context_interpretation_name = (
            "biological_tissue_context_interpretation.tsv"
        )
        (output_dir / tissue_context_summary_name).write_text(
            render_tissue_cell_type_context_summary_tsv(
                report.tissue_cell_type_context_report
            ),
            encoding="utf-8",
        )
        (output_dir / tissue_context_sample_name).write_text(
            render_tissue_cell_type_sample_consistency_tsv(
                report.tissue_cell_type_context_report
            ),
            encoding="utf-8",
        )
        (output_dir / tissue_context_unexpected_name).write_text(
            render_tissue_cell_type_unexpected_signal_tsv(
                report.tissue_cell_type_context_report
            ),
            encoding="utf-8",
        )
        (output_dir / tissue_context_interpretation_name).write_text(
            render_tissue_cell_type_interpretation_tsv(
                report.tissue_cell_type_context_report
            ),
            encoding="utf-8",
        )
    else:
        tissue_context_summary_name = None
        tissue_context_sample_name = None
        tissue_context_unexpected_name = None
        tissue_context_interpretation_name = None
    if report.drug_target_report is not None:
        drug_target_summary_name = "biological_drug_target_summary.tsv"
        drug_target_name = "biological_drug_target_interpretation.tsv"
        (output_dir / drug_target_summary_name).write_text(
            render_drug_target_interpretation_summary_tsv(report.drug_target_report),
            encoding="utf-8",
        )
        (output_dir / drug_target_name).write_text(
            render_drug_target_interpretation_tsv(report.drug_target_report),
            encoding="utf-8",
        )
    else:
        drug_target_summary_name = None
        drug_target_name = None
    if report.disease_phenotype_report is not None:
        disease_phenotype_summary_name = (
            "biological_disease_phenotype_summary.tsv"
        )
        disease_phenotype_term_name = "biological_disease_phenotype_terms.tsv"
        disease_phenotype_unknown_name = (
            "biological_disease_phenotype_unknown_annotations.tsv"
        )
        (output_dir / disease_phenotype_summary_name).write_text(
            render_disease_phenotype_interpretation_summary_tsv(
                report.disease_phenotype_report
            ),
            encoding="utf-8",
        )
        (output_dir / disease_phenotype_term_name).write_text(
            render_disease_phenotype_interpretation_tsv(
                report.disease_phenotype_report
            ),
            encoding="utf-8",
        )
        (output_dir / disease_phenotype_unknown_name).write_text(
            render_unknown_disease_phenotype_annotation_tsv(
                report.disease_phenotype_report
            ),
            encoding="utf-8",
        )
    else:
        disease_phenotype_summary_name = None
        disease_phenotype_term_name = None
        disease_phenotype_unknown_name = None
    if report.compartment_biology_report is not None:
        compartment_summary_name = "biological_compartment_biology_summary.tsv"
        compartment_enrichment_name = "biological_compartment_enrichment.tsv"
        compartment_activity_matrix_name = "biological_compartment_activity_matrix.tsv"
        compartment_activity_sample_name = "biological_compartment_activity_samples.tsv"
        compartment_activity_condition_name = (
            "biological_compartment_activity_conditions.tsv"
        )
        compartment_activity_comparison_name = (
            "biological_compartment_activity_condition_comparisons.tsv"
        )
        compartment_activity_unresolved_name = (
            "biological_compartment_activity_unresolved.tsv"
        )
        compartment_unknown_name = "biological_compartment_unknown_localization.tsv"
        (output_dir / compartment_summary_name).write_text(
            render_compartment_biology_summary_tsv(report.compartment_biology_report),
            encoding="utf-8",
        )
        (output_dir / compartment_enrichment_name).write_text(
            render_compartment_enrichment_tsv(report.compartment_biology_report),
            encoding="utf-8",
        )
        (output_dir / compartment_activity_matrix_name).write_text(
            render_compartment_activity_matrix_tsv(report.compartment_biology_report),
            encoding="utf-8",
        )
        (output_dir / compartment_activity_sample_name).write_text(
            render_compartment_activity_sample_score_tsv(
                report.compartment_biology_report
            ),
            encoding="utf-8",
        )
        (output_dir / compartment_activity_condition_name).write_text(
            render_compartment_activity_condition_score_tsv(
                report.compartment_biology_report
            ),
            encoding="utf-8",
        )
        (output_dir / compartment_activity_comparison_name).write_text(
            render_compartment_activity_condition_comparison_tsv(
                report.compartment_biology_report
            ),
            encoding="utf-8",
        )
        (output_dir / compartment_activity_unresolved_name).write_text(
            render_compartment_activity_unresolved_member_tsv(
                report.compartment_biology_report
            ),
            encoding="utf-8",
        )
        (output_dir / compartment_unknown_name).write_text(
            render_unknown_compartment_localization_tsv(
                report.compartment_biology_report
            ),
            encoding="utf-8",
        )
    else:
        compartment_summary_name = None
        compartment_enrichment_name = None
        compartment_activity_matrix_name = None
        compartment_activity_sample_name = None
        compartment_activity_condition_name = None
        compartment_activity_comparison_name = None
        compartment_activity_unresolved_name = None
        compartment_unknown_name = None
    if report.pathway_activity_report is not None:
        pathway_activity_summary_name = "biological_pathway_activity_summary.tsv"
        pathway_activity_matrix_name = "biological_pathway_activity_matrix.tsv"
        pathway_activity_sample_name = "biological_pathway_activity_samples.tsv"
        pathway_activity_condition_name = "biological_pathway_activity_conditions.tsv"
        pathway_activity_comparison_name = (
            "biological_pathway_activity_condition_comparisons.tsv"
        )
        pathway_activity_member_name = "biological_pathway_activity_members.tsv"
        pathway_activity_unresolved_name = (
            "biological_pathway_activity_unresolved.tsv"
        )
        (output_dir / pathway_activity_summary_name).write_text(
            render_pathway_activity_summary_tsv(report.pathway_activity_report),
            encoding="utf-8",
        )
        (output_dir / pathway_activity_matrix_name).write_text(
            render_pathway_activity_matrix_tsv(report.pathway_activity_report),
            encoding="utf-8",
        )
        (output_dir / pathway_activity_sample_name).write_text(
            render_pathway_activity_sample_score_tsv(report.pathway_activity_report),
            encoding="utf-8",
        )
        (output_dir / pathway_activity_condition_name).write_text(
            render_pathway_activity_condition_score_tsv(report.pathway_activity_report),
            encoding="utf-8",
        )
        (output_dir / pathway_activity_comparison_name).write_text(
            render_pathway_activity_condition_comparison_tsv(
                report.pathway_activity_report
            ),
            encoding="utf-8",
        )
        (output_dir / pathway_activity_member_name).write_text(
            render_pathway_member_contribution_tsv(report.pathway_activity_report),
            encoding="utf-8",
        )
        (output_dir / pathway_activity_unresolved_name).write_text(
            render_pathway_activity_unresolved_member_tsv(
                report.pathway_activity_report
            ),
            encoding="utf-8",
        )
    if report.complex_activity_report is not None:
        complex_activity_summary_name = "biological_complex_activity_summary.tsv"
        complex_activity_matrix_name = "biological_complex_activity_matrix.tsv"
        complex_activity_sample_name = "biological_complex_activity_samples.tsv"
        complex_activity_condition_name = "biological_complex_activity_conditions.tsv"
        complex_activity_comparison_name = (
            "biological_complex_activity_condition_comparisons.tsv"
        )
        complex_activity_member_name = "biological_complex_activity_members.tsv"
        complex_activity_unresolved_name = (
            "biological_complex_activity_unresolved.tsv"
        )
        (output_dir / complex_activity_summary_name).write_text(
            render_complex_activity_summary_tsv(report.complex_activity_report),
            encoding="utf-8",
        )
        (output_dir / complex_activity_matrix_name).write_text(
            render_complex_activity_matrix_tsv(report.complex_activity_report),
            encoding="utf-8",
        )
        (output_dir / complex_activity_sample_name).write_text(
            render_complex_activity_sample_score_tsv(report.complex_activity_report),
            encoding="utf-8",
        )
        (output_dir / complex_activity_condition_name).write_text(
            render_complex_activity_condition_score_tsv(report.complex_activity_report),
            encoding="utf-8",
        )
        (output_dir / complex_activity_comparison_name).write_text(
            render_complex_activity_condition_comparison_tsv(
                report.complex_activity_report
            ),
            encoding="utf-8",
        )
        (output_dir / complex_activity_member_name).write_text(
            render_complex_member_contribution_tsv(report.complex_activity_report),
            encoding="utf-8",
        )
        (output_dir / complex_activity_unresolved_name).write_text(
            render_complex_activity_unresolved_member_tsv(
                report.complex_activity_report
            ),
            encoding="utf-8",
        )
    else:
        complex_activity_summary_name = None
        complex_activity_matrix_name = None
        complex_activity_sample_name = None
        complex_activity_condition_name = None
        complex_activity_comparison_name = None
        complex_activity_member_name = None
        complex_activity_unresolved_name = None
    (output_dir / volcano_tsv_name).write_text(
        render_volcano_review_tsv(report.volcano_review),
        encoding="utf-8",
    )
    export_volcano_review_json(report.volcano_review, output_dir / volcano_json_name)
    export_volcano_review_svg(report.volcano_review, output_dir / volcano_svg_name)
    export_volcano_review_html(report.volcano_review, output_dir / volcano_html_name)
    export_heatmap_summary_tsv(report.heatmap_report, output_dir / heatmap_summary_name)
    export_heatmap_matrix_tsv(report.heatmap_report, output_dir / heatmap_matrix_name)
    export_heatmap_row_metadata_tsv(report.heatmap_report, output_dir / heatmap_row_name)
    export_heatmap_column_metadata_tsv(
        report.heatmap_report,
        output_dir / heatmap_column_name,
    )
    export_sample_exploration_summary_tsv(
        report.sample_exploration_report,
        output_dir / sample_summary_name,
    )
    export_sample_pca_scores_tsv(
        report.sample_exploration_report,
        output_dir / sample_scores_name,
    )
    export_sample_pca_variance_tsv(
        report.sample_exploration_report,
        output_dir / sample_variance_name,
    )
    export_sample_distance_tsv(
        report.sample_exploration_report,
        output_dir / sample_distance_name,
    )
    export_sample_cluster_tsv(
        report.sample_exploration_report,
        output_dir / sample_cluster_name,
    )

    go_summary_name = None
    go_term_name = None
    go_unannotated_name = None
    if report.go_enrichment_report is not None:
        go_summary_name = "biological_go_summary.tsv"
        go_term_name = "biological_go_terms.tsv"
        go_unannotated_name = "biological_go_unannotated.tsv"
        (output_dir / go_summary_name).write_text(
            render_go_enrichment_summary_tsv(report.go_enrichment_report),
            encoding="utf-8",
        )
        (output_dir / go_term_name).write_text(
            render_go_enrichment_term_tsv(report.go_enrichment_report),
            encoding="utf-8",
        )
        (output_dir / go_unannotated_name).write_text(
            render_go_enrichment_unannotated_tsv(report.go_enrichment_report),
            encoding="utf-8",
        )

    pathway_summary_name = None
    pathway_entry_name = None
    pathway_unresolved_name = None
    if report.pathway_enrichment_report is not None:
        pathway_summary_name = "biological_pathway_summary.tsv"
        pathway_entry_name = "biological_pathway_entries.tsv"
        pathway_unresolved_name = "biological_pathway_unresolved.tsv"
        (output_dir / pathway_summary_name).write_text(
            render_pathway_enrichment_summary_tsv(report.pathway_enrichment_report),
            encoding="utf-8",
        )
        (output_dir / pathway_entry_name).write_text(
            render_pathway_enrichment_entry_tsv(report.pathway_enrichment_report),
            encoding="utf-8",
        )
        (output_dir / pathway_unresolved_name).write_text(
            render_pathway_unresolved_member_tsv(report.pathway_enrichment_report),
            encoding="utf-8",
        )

    complex_summary_name = None
    complex_entry_name = None
    complex_unresolved_name = None
    if report.complex_enrichment_report is not None:
        complex_summary_name = "biological_complex_summary.tsv"
        complex_entry_name = "biological_complex_entries.tsv"
        complex_unresolved_name = "biological_complex_unresolved.tsv"
        (output_dir / complex_summary_name).write_text(
            render_complex_enrichment_summary_tsv(report.complex_enrichment_report),
            encoding="utf-8",
        )
        (output_dir / complex_entry_name).write_text(
            render_complex_enrichment_entry_tsv(report.complex_enrichment_report),
            encoding="utf-8",
        )
        (output_dir / complex_unresolved_name).write_text(
            render_complex_unresolved_member_tsv(report.complex_enrichment_report),
            encoding="utf-8",
        )

    artifacts = BiologicalResultReportArtifactPaths(
        summary_tsv=summary_name,
        differential_tsv=differential_name,
        protein_card_summary_tsv=protein_card_summary_name,
        protein_card_tsv=protein_card_name,
        protein_mechanism_card_summary_tsv=protein_mechanism_card_summary_name,
        protein_mechanism_card_tsv=protein_mechanism_card_name,
        evidence_graph_nodes_tsv=evidence_graph_nodes_name,
        evidence_graph_edges_tsv=evidence_graph_edges_name,
        experiment_confidence_summary_tsv=experiment_confidence_summary_name,
        experiment_confidence_components_tsv=experiment_confidence_components_name,
        section_confidence_tsv=section_confidence_name,
        evidence_aware_ranking_tsv=evidence_aware_ranking_name,
        claim_validation_summary_tsv=claim_validation_summary_name,
        supported_claim_tsv=supported_claim_name,
        rejected_claim_tsv=rejected_claim_name,
        biological_hypothesis_summary_tsv=biological_hypothesis_summary_name,
        biological_hypothesis_tsv=biological_hypothesis_name,
        rejected_hypothesis_candidate_tsv=rejected_hypothesis_candidate_name,
        foreground_background_summary_tsv=foreground_background_summary_name,
        foreground_background_entry_tsv=foreground_background_entry_name,
        foreground_background_issue_tsv=foreground_background_issue_name,
        regulator_inference_summary_tsv=regulator_inference_summary_name,
        regulator_inference_tsv=regulator_inference_name,
        regulator_inference_unresolved_tsv=regulator_unresolved_name,
        regulator_evidence_rejected_tsv=regulator_rejected_name,
        annotation_summary_tsv=annotation_summary_name,
        annotation_tsv=annotation_name,
        annotation_unmapped_tsv=annotation_unmapped_name,
        context_summary_tsv=context_summary_name,
        context_mapping_tsv=context_mapping_name,
        context_term_tsv=context_term_name,
        context_unmapped_tsv=context_unmapped_name,
        context_rejected_tsv=context_rejected_name,
        cohort_stratification_summary_tsv=cohort_summary_name,
        cohort_stratum_tsv=cohort_stratum_name,
        cohort_subgroup_effect_tsv=cohort_effect_name,
        cohort_interaction_candidate_tsv=cohort_interaction_name,
        tissue_context_summary_tsv=tissue_context_summary_name,
        tissue_context_sample_consistency_tsv=tissue_context_sample_name,
        tissue_context_unexpected_signal_tsv=tissue_context_unexpected_name,
        tissue_context_interpretation_tsv=tissue_context_interpretation_name,
        drug_target_summary_tsv=drug_target_summary_name,
        drug_target_tsv=drug_target_name,
        disease_phenotype_summary_tsv=disease_phenotype_summary_name,
        disease_phenotype_term_tsv=disease_phenotype_term_name,
        disease_phenotype_unknown_annotation_tsv=disease_phenotype_unknown_name,
        compartment_biology_summary_tsv=compartment_summary_name,
        compartment_enrichment_tsv=compartment_enrichment_name,
        compartment_activity_matrix_tsv=compartment_activity_matrix_name,
        compartment_activity_sample_score_tsv=compartment_activity_sample_name,
        compartment_activity_condition_score_tsv=compartment_activity_condition_name,
        compartment_activity_condition_comparison_tsv=(
            compartment_activity_comparison_name
        ),
        compartment_activity_unresolved_member_tsv=(
            compartment_activity_unresolved_name
        ),
        compartment_unknown_localization_tsv=compartment_unknown_name,
        pathway_activity_summary_tsv=pathway_activity_summary_name,
        pathway_activity_matrix_tsv=pathway_activity_matrix_name,
        pathway_activity_sample_score_tsv=pathway_activity_sample_name,
        pathway_activity_condition_score_tsv=pathway_activity_condition_name,
        pathway_activity_condition_comparison_tsv=pathway_activity_comparison_name,
        pathway_activity_member_contribution_tsv=pathway_activity_member_name,
        pathway_activity_unresolved_member_tsv=pathway_activity_unresolved_name,
        complex_activity_summary_tsv=complex_activity_summary_name,
        complex_activity_matrix_tsv=complex_activity_matrix_name,
        complex_activity_sample_score_tsv=complex_activity_sample_name,
        complex_activity_condition_score_tsv=complex_activity_condition_name,
        complex_activity_condition_comparison_tsv=complex_activity_comparison_name,
        complex_activity_member_contribution_tsv=complex_activity_member_name,
        complex_activity_unresolved_member_tsv=complex_activity_unresolved_name,
        volcano_tsv=volcano_tsv_name,
        volcano_json=volcano_json_name,
        volcano_svg=volcano_svg_name,
        volcano_html=volcano_html_name,
        heatmap_summary_tsv=heatmap_summary_name,
        heatmap_matrix_tsv=heatmap_matrix_name,
        heatmap_row_metadata_tsv=heatmap_row_name,
        heatmap_column_metadata_tsv=heatmap_column_name,
        sample_exploration_summary_tsv=sample_summary_name,
        sample_pca_scores_tsv=sample_scores_name,
        sample_pca_variance_tsv=sample_variance_name,
        sample_distance_tsv=sample_distance_name,
        sample_cluster_tsv=sample_cluster_name,
        report_html=report_html_name,
        go_summary_tsv=go_summary_name,
        go_term_tsv=go_term_name,
        go_unannotated_tsv=go_unannotated_name,
        pathway_summary_tsv=pathway_summary_name,
        pathway_entry_tsv=pathway_entry_name,
        pathway_unresolved_tsv=pathway_unresolved_name,
        complex_summary_tsv=complex_summary_name,
        complex_entry_tsv=complex_entry_name,
        complex_unresolved_tsv=complex_unresolved_name,
    )
    (output_dir / report_html_name).write_text(
        _render_biological_result_report_html(report, artifacts),
        encoding="utf-8",
    )
    synchronize_workflow_artifact_layout(
        output_dir,
        producer_function="export_biological_result_report_bundle",
    )
    return BiologicalResultReportExportManifest(
        summary=report.summary,
        artifacts=artifacts,
        claim_validation_included=report.claim_validation_report is not None,
        hypothesis_summary_included=report.biological_hypothesis_report is not None,
        context_summary_included=report.context_mapping_report is not None,
        cohort_stratification_summary_included=(
            report.cohort_stratification_report is not None
        ),
        tissue_context_summary_included=report.tissue_cell_type_context_report is not None,
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
def export_biological_result_report_bundle(
    report: BiologicalResultReportBundle,
    output_dir: Path,
) -> BiologicalResultReportExportManifest:
    """Compatibility wrapper for the legacy biological report bundle export name."""

    return write_biological_result_report_bundle(report, output_dir)


__all__ = [
    "export_biological_result_report_bundle",
    "write_biological_result_report_bundle",
    "render_biological_report_section_confidence_tsv",
    "render_biological_result_report_summary_tsv",
]
