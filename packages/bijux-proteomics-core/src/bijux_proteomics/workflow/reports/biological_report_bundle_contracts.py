# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Workflow bundle contracts for biological report assembly and rendering."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.confidence import ConfidenceTier
from bijux_proteomics.interpretation import (
    BiologicalContextImportReport,
    BiologicalContextMappingReport,
    BiologicalForegroundBackgroundModel,
    ComplexActivityReport,
    ComplexEnrichmentReport,
    DiseasePhenotypeInterpretationReport,
    DrugTargetInterpretationReport,
    GoEnrichmentReport,
    PathwayActivityReport,
    PathwayEnrichmentReport,
    ProteinAnnotationMappingReport,
    RegulatorEvidenceImportReport,
    RegulatorInferenceReport,
    TissueCellTypeContextReport,
)
from bijux_proteomics.interpretation.compartment_biology import (
    CompartmentBiologyReport,
)
from bijux_proteomics.quantification.contracts import DifferentialAbundanceReport
from bijux_proteomics.quantification.provenance import (
    HeatmapPreparationReport,
    SampleExplorationReport,
)
from bijux_proteomics.review.belief.evidence_aware_ranking import (
    EvidenceAwareRankingReport,
)
from bijux_proteomics.review.claims.biological_claim_validation import (
    BiologicalClaimValidationReport,
)
from bijux_proteomics.review.claims.biological_hypotheses import (
    BiologicalHypothesisReport,
)
from bijux_proteomics.review.explanations.volcano_plots import VolcanoReviewReport
from bijux_proteomics.study import ExperimentConfidenceReport
from bijux_proteomics.workflow.cards.protein_evidence_cards import (
    ProteinEvidenceCardReport,
)
from bijux_proteomics.workflow.cards.protein_mechanism_cards import (
    ProteinMechanismCardReport,
)
from bijux_proteomics.workflow.reports.biological_report_section_metadata import (
    BiologicalReportSectionConfidenceEntry,
)
from bijux_proteomics.workflow.reports.biological_report_selection_policy import (
    BiologicalResultSelectionPolicy,
)
from bijux_proteomics.workflow.reports.biological_result_graph import (
    BiologicalResultGraphReport,
)
from bijux_proteomics.workflow.studies.cohort_stratification import (
    CohortStratificationReport,
)
from bijux_proteomics_foundation import JsonModel


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


BiologicalResultReportBundle.model_rebuild()
