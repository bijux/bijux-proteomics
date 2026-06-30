# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
# ruff: noqa: F401

"""Biological report contracts and stable section metadata."""

from __future__ import annotations

import csv
from enum import StrEnum
from html import escape
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.confidence import ConfidenceTier
from bijux_proteomics.interpretation import (
    BiologicalContextImportReport,
    BiologicalContextKind,
    BiologicalContextMappingReport,
    BiologicalForegroundBackgroundModel,
    BiologicalSetEntry,
    BiologicalSetFilteringPolicy,
    BiologicalSetSourceKind,
    ComplexActivityReport,
    ComplexEnrichmentCorrectionPolicy,
    ComplexEnrichmentReport,
    DiseasePhenotypeInterpretationPolicy,
    DiseasePhenotypeInterpretationReport,
    DrugTargetInterpretationPolicy,
    DrugTargetInterpretationReport,
    GoEnrichmentCorrectionPolicy,
    GoEnrichmentReport,
    PathwayActivityReport,
    PathwayEnrichmentCorrectionPolicy,
    PathwayEnrichmentReport,
    ProteinAnnotationColumnMapping,
    ProteinAnnotationMappingReport,
    ProteinReferenceEntry,
    RegulatorEvidenceImportReport,
    RegulatorInferenceReport,
    TissueCellTypeContextReport,
    apply_complex_enrichment_multiple_testing,
    apply_go_enrichment_multiple_testing,
    apply_pathway_enrichment_multiple_testing,
    build_biological_context_mapping_report,
    build_biological_foreground_background_model,
    build_complex_activity_report,
    build_complex_enrichment_report,
    build_disease_phenotype_interpretation_report,
    build_drug_target_interpretation_report,
    build_go_enrichment_report,
    build_pathway_activity_report,
    build_pathway_enrichment_report,
    build_protein_annotation_mapping_report,
    build_regulator_inference_report,
    build_regulator_site_signal_entries_from_ptm_evidence_cards,
    build_tissue_cell_type_context_report,
    parse_biological_context_table,
    parse_complex_membership_table,
    parse_go_annotation_table,
    parse_pathway_membership_table,
    parse_protein_annotation_table,
    parse_regulator_evidence_table,
    parse_regulator_site_signal_table,
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
    render_disease_phenotype_interpretation_summary_tsv,
    render_disease_phenotype_interpretation_tsv,
    render_drug_target_interpretation_summary_tsv,
    render_drug_target_interpretation_tsv,
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
    render_regulator_inference_summary_tsv,
    render_regulator_inference_tsv,
    render_rejected_biological_context_tsv,
    render_rejected_regulator_evidence_tsv,
    render_tissue_cell_type_context_summary_tsv,
    render_tissue_cell_type_interpretation_tsv,
    render_tissue_cell_type_sample_consistency_tsv,
    render_tissue_cell_type_unexpected_signal_tsv,
    render_unknown_disease_phenotype_annotation_tsv,
    render_unmapped_biological_context_tsv,
    render_unmapped_protein_annotation_tsv,
    render_unresolved_regulator_target_tsv,
    require_valid_biological_foreground_background_model,
)
from bijux_proteomics.interpretation.compartment_biology import (
    CompartmentBiologyPolicy,
    CompartmentBiologyReport,
    build_compartment_biology_report,
    render_compartment_activity_condition_comparison_tsv,
    render_compartment_activity_condition_score_tsv,
    render_compartment_activity_matrix_tsv,
    render_compartment_activity_sample_score_tsv,
    render_compartment_activity_unresolved_member_tsv,
    render_compartment_biology_summary_tsv,
    render_compartment_enrichment_tsv,
    render_unknown_compartment_localization_tsv,
)
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.lab.protocol_context import (
    build_lab_protocol_interpretation_profile,
    parse_lab_protocol_context_table,
    require_single_lab_protocol_context,
)
from bijux_proteomics.ptm import PtmEvidenceCardReport
from bijux_proteomics.quantification import (
    HeatmapMissingValuePolicy,
    HeatmapPreparationPolicy,
    HeatmapPreparationReport,
    LabelFreeQuantTable,
    Ms1FeatureColumnMapping,
    NormalizationMethod,
    QuantEntityLevel,
    QuantMeasureKind,
    QuantRollupMethod,
    SampleExplorationReport,
    build_differential_abundance_report,
    build_heatmap_preparation_report,
    build_label_free_intensity_table,
    build_missingness_condition_summary_report,
    build_power_estimation_report,
    build_sample_exploration_report,
    export_heatmap_column_metadata_tsv,
    export_heatmap_matrix_tsv,
    export_heatmap_row_metadata_tsv,
    export_heatmap_summary_tsv,
    export_sample_cluster_tsv,
    export_sample_distance_tsv,
    export_sample_exploration_summary_tsv,
    export_sample_pca_scores_tsv,
    export_sample_pca_variance_tsv,
    normalize_label_free_table,
    parse_ms1_feature_table,
    render_differential_abundance_tsv,
)
from bijux_proteomics.quantification.contracts.differential import (
    DifferentialAbundanceReport,
)
from bijux_proteomics.quantification.differential_abundance import (
    apply_benjamini_hochberg,
)
from bijux_proteomics.review import (
    BiologicalClaimCandidate,
    BiologicalClaimDirection,
    BiologicalClaimKind,
    BiologicalClaimValidationPolicy,
    BiologicalClaimValidationReport,
    BiologicalHypothesisCandidate,
    BiologicalHypothesisKind,
    BiologicalHypothesisReport,
    EvidenceAwareRankingCandidate,
    EvidenceAwareRankingEntityKind,
    EvidenceAwareRankingReport,
    VolcanoReviewPolicy,
    VolcanoReviewReport,
    build_biological_claim_validation_report,
    build_biological_hypothesis_report,
    build_evidence_aware_ranking_report,
    build_quantification_volcano_review,
    export_proteomics_evidence_graph,
    export_volcano_review_html,
    export_volcano_review_json,
    export_volcano_review_svg,
    normalize_linear_range,
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
    score_adjusted_p_value,
    score_effect_size,
    score_support_count,
)
from bijux_proteomics.sequences import (
    FastaParseMode,
    parse_fasta_document,
    parse_protein_region_context_tsv,
    parse_proteogenomic_variant_peptide_table,
)
from bijux_proteomics.study import (
    ExperimentConfidenceReport,
    ExperimentDesign,
    LcmsRunQcReport,
    QcRunAssessmentReport,
    build_experiment_confidence_report,
    build_experiment_feasibility_report,
    build_protocol_consistency_report,
    coerce_experiment_design,
    render_experiment_confidence_component_tsv,
    render_experiment_confidence_summary_tsv,
)
from bijux_proteomics.workflow.cards.protein_evidence_cards import (
    ProteinEvidenceCardReport,
    ProteinEvidenceCardSelectionPolicy,
    build_protein_evidence_card_report,
    render_protein_evidence_card_summary_tsv,
    render_protein_evidence_card_tsv,
)
from bijux_proteomics.workflow.cards.protein_mechanism_cards import (
    ProteinMechanismCard,
    ProteinMechanismCardReport,
    build_protein_mechanism_card_report,
    render_protein_mechanism_card_summary_tsv,
    render_protein_mechanism_card_tsv,
)
from bijux_proteomics.workflow.cohort_stratification import (
    CohortStratificationReport,
    build_cohort_stratification_report,
    render_cohort_interaction_candidate_tsv,
    render_cohort_stratification_summary_tsv,
    render_cohort_stratum_tsv,
    render_cohort_subgroup_effect_tsv,
)
from bijux_proteomics.workflow.reports.biological_result_graph import (
    BiologicalResultGraphReport,
    build_biological_result_graph_report,
)
from bijux_proteomics_foundation import JsonModel


class BiologicalResultSelectionPolicy(JsonModel):
    """Selection policy for interpretation-focused biological result bundles."""

    model_config = ConfigDict(extra="forbid")

    max_adjusted_p_value: float = Field(default=0.1, ge=0.0, le=1.0)
    min_absolute_log2_fold_change: float = Field(default=1.0, ge=0.0)
    heatmap_max_entity_count: int = Field(default=50, ge=1)
    heatmap_min_observed_fraction: float = Field(default=0.5, ge=0.0, le=1.0)


def _resolve_biological_result_selection_policy(
    selection_policy: BiologicalResultSelectionPolicy | None,
    *,
    protocol_context_tsv_path: Path | None,
) -> BiologicalResultSelectionPolicy:
    if selection_policy is not None:
        return selection_policy
    if protocol_context_tsv_path is None:
        return BiologicalResultSelectionPolicy()
    protocol_context = require_single_lab_protocol_context(
        parse_lab_protocol_context_table(protocol_context_tsv_path)
    )
    profile = build_lab_protocol_interpretation_profile(protocol_context)
    return BiologicalResultSelectionPolicy(
        max_adjusted_p_value=profile.max_adjusted_p_value,
        min_absolute_log2_fold_change=profile.min_absolute_log2_fold_change,
        heatmap_max_entity_count=profile.heatmap_max_entity_count,
        heatmap_min_observed_fraction=BiologicalResultSelectionPolicy().heatmap_min_observed_fraction,
    )


class BiologicalResultReportSummary(JsonModel):
    """Compact summary over one biological result bundle."""

    model_config = ConfigDict(extra="forbid")

    protein_count: int = Field(..., ge=0)
    significant_protein_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    annotation_entry_count: int = Field(..., ge=0)
    annotation_unmapped_count: int = Field(..., ge=0)
    protein_card_count: int = Field(..., ge=0)
    warning_card_count: int = Field(..., ge=0)
    tissue_mismatch_warning_count: int = Field(..., ge=0)
    cohort_blocked_stratum_count: int = Field(..., ge=0)
    cohort_subgroup_effect_count: int = Field(..., ge=0)
    cohort_interaction_candidate_count: int = Field(..., ge=0)
    experiment_confidence_score: float = Field(..., ge=0.0, le=1.0)
    experiment_confidence_tier: ConfidenceTier
    low_confidence_component_count: int = Field(..., ge=0)
    high_confidence_section_count: int = Field(..., ge=0)
    moderate_confidence_section_count: int = Field(..., ge=0)
    weak_confidence_section_count: int = Field(..., ge=0)
    exploratory_section_count: int = Field(..., ge=0)
    invalid_section_count: int = Field(..., ge=0)
    context_entry_count: int = Field(..., ge=0)
    context_unmapped_count: int = Field(..., ge=0)
    context_term_count: int = Field(..., ge=0)
    go_enriched_term_count: int = Field(..., ge=0)
    pathway_enriched_entry_count: int = Field(..., ge=0)
    complex_enriched_entry_count: int = Field(..., ge=0)
    heatmap_entity_count: int = Field(..., ge=0)
    pca_outlier_sample_count: int = Field(..., ge=0)


class BiologicalResultReportBundle(JsonModel):
    """Owned workflow bundle over differential proteins and review-ready plots."""

    model_config = ConfigDict(extra="forbid")

    differential_report: DifferentialAbundanceReport
    graph_report: BiologicalResultGraphReport
    annotation_report: ProteinAnnotationMappingReport
    protein_cards: ProteinEvidenceCardReport
    protein_mechanism_cards: ProteinMechanismCardReport
    experiment_confidence_report: ExperimentConfidenceReport
    evidence_aware_ranking_report: EvidenceAwareRankingReport | None = None
    claim_validation_report: BiologicalClaimValidationReport | None = None
    biological_hypothesis_report: BiologicalHypothesisReport | None = None
    foreground_background_model: BiologicalForegroundBackgroundModel
    regulator_evidence_import_report: RegulatorEvidenceImportReport | None = None
    regulator_inference_report: RegulatorInferenceReport | None = None
    context_import_report: BiologicalContextImportReport | None = None
    context_mapping_report: BiologicalContextMappingReport | None = None
    cohort_stratification_report: CohortStratificationReport | None = None
    tissue_cell_type_context_report: TissueCellTypeContextReport | None = None
    drug_target_report: DrugTargetInterpretationReport | None = None
    disease_phenotype_report: DiseasePhenotypeInterpretationReport | None = None
    compartment_biology_report: CompartmentBiologyReport | None = None
    pathway_activity_report: PathwayActivityReport | None = None
    complex_activity_report: ComplexActivityReport | None = None
    go_enrichment_report: GoEnrichmentReport | None = None
    pathway_enrichment_report: PathwayEnrichmentReport | None = None
    complex_enrichment_report: ComplexEnrichmentReport | None = None
    volcano_review: VolcanoReviewReport
    heatmap_report: HeatmapPreparationReport
    sample_exploration_report: SampleExplorationReport
    selection_policy: BiologicalResultSelectionPolicy
    section_confidence_entries: tuple[BiologicalReportSectionConfidenceEntry, ...] = (
        Field(default_factory=tuple)
    )
    summary: BiologicalResultReportSummary
    note: str = Field(..., min_length=1)


class BiologicalReportSectionKey(StrEnum):
    """Stable identifiers for biological report sections with scientific confidence."""

    EXPERIMENT_CONFIDENCE = "experiment_confidence"
    EVIDENCE_AWARE_RANKING = "evidence_aware_ranking"
    VALIDATED_BIOLOGICAL_CLAIMS = "validated_biological_claims"
    BIOLOGICAL_HYPOTHESES = "biological_hypotheses"
    ENRICHMENT_FOREGROUND_BACKGROUND = "enrichment_foreground_background"
    REGULATOR_INFERENCE = "regulator_inference"
    DRUG_TARGET_INTERPRETATION = "drug_target_interpretation"
    DISEASE_PHENOTYPE_INTERPRETATION = "disease_phenotype_interpretation"
    COHORT_STRATIFICATION = "cohort_stratification"
    TISSUE_CELL_TYPE_CONTEXT = "tissue_cell_type_context"
    COMPARTMENT_BIOLOGY = "compartment_biology"
    PATHWAY_ACTIVITY = "pathway_activity"
    COMPLEX_ACTIVITY = "complex_activity"
    PROTEIN_MECHANISM_CARDS = "protein_mechanism_cards"


class BiologicalReportSectionConfidenceLabel(StrEnum):
    """Derived confidence labels for scientific report sections."""

    HIGH = "high"
    MODERATE = "moderate"
    WEAK = "weak"
    EXPLORATORY = "exploratory"
    INVALID = "invalid"


class BiologicalReportSectionConfidenceEntry(JsonModel):
    """One deterministic confidence assignment for a biological report section."""

    model_config = ConfigDict(extra="forbid")

    section_key: BiologicalReportSectionKey
    section_title: str = Field(..., min_length=1)
    confidence_label: BiologicalReportSectionConfidenceLabel
    rationale: str = Field(..., min_length=1)


BiologicalResultReportBundle.model_rebuild()


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


_BIOLOGICAL_REPORT_SECTION_TITLES: dict[BiologicalReportSectionKey, str] = {
    BiologicalReportSectionKey.EXPERIMENT_CONFIDENCE: "Experiment confidence",
    BiologicalReportSectionKey.EVIDENCE_AWARE_RANKING: "Evidence-aware ranking",
    BiologicalReportSectionKey.VALIDATED_BIOLOGICAL_CLAIMS: "Validated biological claims",
    BiologicalReportSectionKey.BIOLOGICAL_HYPOTHESES: "Biological hypotheses",
    BiologicalReportSectionKey.ENRICHMENT_FOREGROUND_BACKGROUND: (
        "Enrichment foreground/background model"
    ),
    BiologicalReportSectionKey.REGULATOR_INFERENCE: "Regulator inference",
    BiologicalReportSectionKey.DRUG_TARGET_INTERPRETATION: "Drug-target interpretation",
    BiologicalReportSectionKey.DISEASE_PHENOTYPE_INTERPRETATION: (
        "Disease and phenotype interpretation"
    ),
    BiologicalReportSectionKey.COHORT_STRATIFICATION: "Cohort stratification",
    BiologicalReportSectionKey.TISSUE_CELL_TYPE_CONTEXT: "Tissue and cell-type context",
    BiologicalReportSectionKey.COMPARTMENT_BIOLOGY: "Compartment biology",
    BiologicalReportSectionKey.PATHWAY_ACTIVITY: "Pathway activity",
    BiologicalReportSectionKey.COMPLEX_ACTIVITY: "Complex activity",
    BiologicalReportSectionKey.PROTEIN_MECHANISM_CARDS: "Protein mechanism cards",
}
