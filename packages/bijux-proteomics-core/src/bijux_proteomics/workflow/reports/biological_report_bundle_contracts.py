# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Workflow bundle contracts for biological report assembly and rendering."""

from __future__ import annotations

from typing import Any

from pydantic import ConfigDict, Field

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
from bijux_proteomics.workflow.reports.biological_report_summary_contracts import (
    BiologicalResultReportSummary,
)
from bijux_proteomics.workflow.reports.biological_result_graph import (
    BiologicalResultGraphReport,
)
from bijux_proteomics.workflow.studies.cohort_stratification import (
    CohortStratificationReport,
)
from bijux_proteomics_foundation import JsonModel


class BiologicalScientificReportBundle(JsonModel):
    """Scientific review state owned by biological report assembly."""

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


class BiologicalContextualReportBundle(JsonModel):
    """Contextual interpretation state owned by biological report assembly."""

    model_config = ConfigDict(extra="forbid")

    context_import_report: BiologicalContextImportReport | None = None
    context_mapping_report: BiologicalContextMappingReport | None = None
    cohort_stratification_report: CohortStratificationReport | None = None
    tissue_cell_type_context_report: TissueCellTypeContextReport | None = None
    drug_target_report: DrugTargetInterpretationReport | None = None
    disease_phenotype_report: DiseasePhenotypeInterpretationReport | None = None


class BiologicalActivityReportBundle(JsonModel):
    """Activity interpretation state owned by biological report assembly."""

    model_config = ConfigDict(extra="forbid")

    compartment_biology_report: CompartmentBiologyReport | None = None
    pathway_activity_report: PathwayActivityReport | None = None
    complex_activity_report: ComplexActivityReport | None = None


class BiologicalEnrichmentReportBundle(JsonModel):
    """Enrichment interpretation state owned by biological report assembly."""

    model_config = ConfigDict(extra="forbid")

    go_enrichment_report: GoEnrichmentReport | None = None
    pathway_enrichment_report: PathwayEnrichmentReport | None = None
    complex_enrichment_report: ComplexEnrichmentReport | None = None


class BiologicalVisualReportBundle(JsonModel):
    """Visual review state owned by biological report assembly."""

    model_config = ConfigDict(extra="forbid")

    volcano_review: VolcanoReviewReport
    heatmap_report: HeatmapPreparationReport
    sample_exploration_report: SampleExplorationReport


class BiologicalResultReportBundle(JsonModel):
    """Owned workflow bundle over differential proteins and review-ready plots."""

    model_config = ConfigDict(extra="forbid")

    scientific: BiologicalScientificReportBundle
    contextual: BiologicalContextualReportBundle
    activity: BiologicalActivityReportBundle
    enrichment: BiologicalEnrichmentReportBundle
    visual: BiologicalVisualReportBundle
    selection_policy: BiologicalResultSelectionPolicy
    section_confidence_entries: tuple[BiologicalReportSectionConfidenceEntry, ...] = (
        Field(default_factory=tuple)
    )
    summary: BiologicalResultReportSummary
    note: str = Field(..., min_length=1)

    @property
    def differential_report(self) -> DifferentialAbundanceReport:
        return self.scientific.differential_report

    @property
    def graph_report(self) -> BiologicalResultGraphReport:
        return self.scientific.graph_report

    @property
    def annotation_report(self) -> ProteinAnnotationMappingReport:
        return self.scientific.annotation_report

    @property
    def protein_cards(self) -> ProteinEvidenceCardReport:
        return self.scientific.protein_cards

    @property
    def protein_mechanism_cards(self) -> ProteinMechanismCardReport:
        return self.scientific.protein_mechanism_cards

    @property
    def experiment_confidence_report(self) -> ExperimentConfidenceReport:
        return self.scientific.experiment_confidence_report

    @property
    def evidence_aware_ranking_report(self) -> EvidenceAwareRankingReport | None:
        return self.scientific.evidence_aware_ranking_report

    @property
    def claim_validation_report(self) -> BiologicalClaimValidationReport | None:
        return self.scientific.claim_validation_report

    @property
    def biological_hypothesis_report(self) -> BiologicalHypothesisReport | None:
        return self.scientific.biological_hypothesis_report

    @property
    def foreground_background_model(self) -> BiologicalForegroundBackgroundModel:
        return self.scientific.foreground_background_model

    @property
    def regulator_evidence_import_report(
        self,
    ) -> RegulatorEvidenceImportReport | None:
        return self.scientific.regulator_evidence_import_report

    @property
    def regulator_inference_report(self) -> RegulatorInferenceReport | None:
        return self.scientific.regulator_inference_report

    @property
    def context_import_report(self) -> BiologicalContextImportReport | None:
        return self.contextual.context_import_report

    @property
    def context_mapping_report(self) -> BiologicalContextMappingReport | None:
        return self.contextual.context_mapping_report

    @property
    def cohort_stratification_report(self) -> CohortStratificationReport | None:
        return self.contextual.cohort_stratification_report

    @property
    def tissue_cell_type_context_report(self) -> TissueCellTypeContextReport | None:
        return self.contextual.tissue_cell_type_context_report

    @property
    def drug_target_report(self) -> DrugTargetInterpretationReport | None:
        return self.contextual.drug_target_report

    @property
    def disease_phenotype_report(self) -> DiseasePhenotypeInterpretationReport | None:
        return self.contextual.disease_phenotype_report

    @property
    def compartment_biology_report(self) -> CompartmentBiologyReport | None:
        return self.activity.compartment_biology_report

    @property
    def pathway_activity_report(self) -> PathwayActivityReport | None:
        return self.activity.pathway_activity_report

    @property
    def complex_activity_report(self) -> ComplexActivityReport | None:
        return self.activity.complex_activity_report

    @property
    def go_enrichment_report(self) -> GoEnrichmentReport | None:
        return self.enrichment.go_enrichment_report

    @property
    def pathway_enrichment_report(self) -> PathwayEnrichmentReport | None:
        return self.enrichment.pathway_enrichment_report

    @property
    def complex_enrichment_report(self) -> ComplexEnrichmentReport | None:
        return self.enrichment.complex_enrichment_report

    @property
    def volcano_review(self) -> VolcanoReviewReport:
        return self.visual.volcano_review

    @property
    def heatmap_report(self) -> HeatmapPreparationReport:
        return self.visual.heatmap_report

    @property
    def sample_exploration_report(self) -> SampleExplorationReport:
        return self.visual.sample_exploration_report

    def to_dict(self) -> dict[str, Any]:
        """Return the stable public bundle payload without exposing internal grouping."""

        payload = super().to_dict()
        scientific = payload.pop("scientific")
        contextual = payload.pop("contextual")
        activity = payload.pop("activity")
        enrichment = payload.pop("enrichment")
        visual = payload.pop("visual")
        return {
            **payload,
            **scientific,
            **contextual,
            **activity,
            **enrichment,
            **visual,
        }


BiologicalResultReportBundle.model_rebuild()


__all__ = [
    "BiologicalActivityReportBundle",
    "BiologicalContextualReportBundle",
    "BiologicalEnrichmentReportBundle",
    "BiologicalResultReportBundle",
    "BiologicalScientificReportBundle",
    "BiologicalVisualReportBundle",
]
