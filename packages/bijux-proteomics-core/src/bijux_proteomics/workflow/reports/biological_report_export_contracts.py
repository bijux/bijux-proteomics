# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Artifact and manifest contracts for exported biological report bundles."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.workflow.reports.biological_report_summary_contracts import (
    BiologicalResultReportSummary,
)
from bijux_proteomics_foundation import JsonModel


class BiologicalResultReportArtifactPaths(JsonModel):
    """Relative artifact paths written into one biological result report directory."""

    model_config = ConfigDict(extra="forbid")

    summary_tsv: str = Field(..., min_length=1)
    differential_tsv: str = Field(..., min_length=1)
    protein_card_summary_tsv: str = Field(..., min_length=1)
    protein_card_tsv: str = Field(..., min_length=1)
    pathway_card_tsv: str | None = None
    protein_mechanism_card_summary_tsv: str = Field(..., min_length=1)
    protein_mechanism_card_tsv: str = Field(..., min_length=1)
    evidence_graph_nodes_tsv: str = Field(..., min_length=1)
    evidence_graph_edges_tsv: str = Field(..., min_length=1)
    experiment_confidence_summary_tsv: str = Field(..., min_length=1)
    experiment_confidence_components_tsv: str = Field(..., min_length=1)
    section_confidence_tsv: str = Field(..., min_length=1)
    evidence_aware_ranking_tsv: str | None = None
    claim_validation_summary_tsv: str | None = None
    supported_claim_tsv: str | None = None
    rejected_claim_tsv: str | None = None
    biological_hypothesis_summary_tsv: str | None = None
    biological_hypothesis_tsv: str | None = None
    rejected_hypothesis_candidate_tsv: str | None = None
    foreground_background_summary_tsv: str = Field(..., min_length=1)
    foreground_background_entry_tsv: str = Field(..., min_length=1)
    foreground_background_issue_tsv: str = Field(..., min_length=1)
    regulator_inference_summary_tsv: str | None = None
    regulator_inference_tsv: str | None = None
    regulator_inference_unresolved_tsv: str | None = None
    regulator_evidence_rejected_tsv: str | None = None
    annotation_summary_tsv: str = Field(..., min_length=1)
    annotation_tsv: str = Field(..., min_length=1)
    annotation_unmapped_tsv: str = Field(..., min_length=1)
    context_summary_tsv: str | None = None
    context_mapping_tsv: str | None = None
    context_term_tsv: str | None = None
    context_unmapped_tsv: str | None = None
    context_rejected_tsv: str | None = None
    cohort_stratification_summary_tsv: str | None = None
    cohort_stratum_tsv: str | None = None
    cohort_subgroup_effect_tsv: str | None = None
    cohort_interaction_candidate_tsv: str | None = None
    tissue_context_summary_tsv: str | None = None
    tissue_context_sample_consistency_tsv: str | None = None
    tissue_context_unexpected_signal_tsv: str | None = None
    tissue_context_interpretation_tsv: str | None = None
    drug_target_summary_tsv: str | None = None
    drug_target_tsv: str | None = None
    disease_phenotype_summary_tsv: str | None = None
    disease_phenotype_term_tsv: str | None = None
    disease_phenotype_unknown_annotation_tsv: str | None = None
    compartment_biology_summary_tsv: str | None = None
    compartment_enrichment_tsv: str | None = None
    compartment_activity_matrix_tsv: str | None = None
    compartment_activity_sample_score_tsv: str | None = None
    compartment_activity_condition_score_tsv: str | None = None
    compartment_activity_condition_comparison_tsv: str | None = None
    compartment_activity_unresolved_member_tsv: str | None = None
    compartment_unknown_localization_tsv: str | None = None
    pathway_activity_summary_tsv: str | None = None
    pathway_activity_matrix_tsv: str | None = None
    pathway_activity_sample_score_tsv: str | None = None
    pathway_activity_condition_score_tsv: str | None = None
    pathway_activity_condition_comparison_tsv: str | None = None
    pathway_activity_member_contribution_tsv: str | None = None
    pathway_activity_unresolved_member_tsv: str | None = None
    complex_activity_summary_tsv: str | None = None
    complex_activity_matrix_tsv: str | None = None
    complex_activity_sample_score_tsv: str | None = None
    complex_activity_condition_score_tsv: str | None = None
    complex_activity_condition_comparison_tsv: str | None = None
    complex_activity_member_contribution_tsv: str | None = None
    complex_activity_unresolved_member_tsv: str | None = None
    volcano_tsv: str = Field(..., min_length=1)
    volcano_json: str = Field(..., min_length=1)
    volcano_svg: str = Field(..., min_length=1)
    volcano_html: str = Field(..., min_length=1)
    heatmap_summary_tsv: str = Field(..., min_length=1)
    heatmap_matrix_tsv: str = Field(..., min_length=1)
    heatmap_row_metadata_tsv: str = Field(..., min_length=1)
    heatmap_column_metadata_tsv: str = Field(..., min_length=1)
    sample_exploration_summary_tsv: str = Field(..., min_length=1)
    sample_pca_scores_tsv: str = Field(..., min_length=1)
    sample_pca_variance_tsv: str = Field(..., min_length=1)
    sample_distance_tsv: str = Field(..., min_length=1)
    sample_cluster_tsv: str = Field(..., min_length=1)
    sample_card_tsv: str | None = None
    report_html: str = Field(..., min_length=1)
    go_summary_tsv: str | None = None
    go_term_tsv: str | None = None
    go_unannotated_tsv: str | None = None
    pathway_summary_tsv: str | None = None
    pathway_entry_tsv: str | None = None
    pathway_unresolved_tsv: str | None = None
    complex_summary_tsv: str | None = None
    complex_entry_tsv: str | None = None
    complex_unresolved_tsv: str | None = None


class BiologicalResultReportExportManifest(JsonModel):
    """Stable manifest over one exported biological result report directory."""

    model_config = ConfigDict(extra="forbid")

    summary: BiologicalResultReportSummary
    artifacts: BiologicalResultReportArtifactPaths
    claim_validation_included: bool
    hypothesis_summary_included: bool
    context_summary_included: bool
    cohort_stratification_summary_included: bool
    tissue_context_summary_included: bool
    drug_target_summary_included: bool
    disease_phenotype_summary_included: bool
    go_summary_included: bool
    pathway_summary_included: bool
    complex_summary_included: bool
    note: str = Field(..., min_length=1)
