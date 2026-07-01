# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Input contracts for biological result report bundle assembly."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bijux_proteomics.interpretation import (
        BiologicalContextImportReport,
        BiologicalContextMappingReport,
        BiologicalForegroundBackgroundModel,
        CompartmentBiologyReport,
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
    from bijux_proteomics.quantification.contracts import (
        DifferentialAbundanceReport,
        LabelFreeQuantTable,
    )
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
    from bijux_proteomics.workflow.reports.biological_report_selection_policy import (
        BiologicalResultSelectionPolicy,
    )
    from bijux_proteomics.workflow.reports.biological_result_graph import (
        BiologicalResultGraphReport,
    )
    from bijux_proteomics.workflow.studies.cohort_stratification import (
        CohortStratificationReport,
    )


@dataclass(frozen=True)
class BiologicalReportBundleAssemblyInputs:
    """All owned inputs required to assemble one biological result bundle."""

    normalized_table: LabelFreeQuantTable
    differential_report: DifferentialAbundanceReport
    graph_report: BiologicalResultGraphReport
    annotation_report: ProteinAnnotationMappingReport
    protein_cards: ProteinEvidenceCardReport
    protein_mechanism_cards: ProteinMechanismCardReport
    experiment_confidence_report: ExperimentConfidenceReport
    evidence_aware_ranking_report: EvidenceAwareRankingReport | None
    claim_validation_report: BiologicalClaimValidationReport | None
    biological_hypothesis_report: BiologicalHypothesisReport | None
    foreground_background_model: BiologicalForegroundBackgroundModel
    regulator_evidence_import_report: RegulatorEvidenceImportReport | None
    regulator_inference_report: RegulatorInferenceReport | None
    context_import_report: BiologicalContextImportReport | None
    context_mapping_report: BiologicalContextMappingReport | None
    cohort_stratification_report: CohortStratificationReport | None
    tissue_cell_type_context_report: TissueCellTypeContextReport | None
    drug_target_report: DrugTargetInterpretationReport | None
    disease_phenotype_report: DiseasePhenotypeInterpretationReport | None
    compartment_biology_report: CompartmentBiologyReport | None
    pathway_activity_report: PathwayActivityReport | None
    complex_activity_report: ComplexActivityReport | None
    go_enrichment_report: GoEnrichmentReport | None
    pathway_enrichment_report: PathwayEnrichmentReport | None
    complex_enrichment_report: ComplexEnrichmentReport | None
    volcano_review: VolcanoReviewReport
    heatmap_report: HeatmapPreparationReport
    sample_exploration_report: SampleExplorationReport
    selection_policy: BiologicalResultSelectionPolicy


__all__ = ["BiologicalReportBundleAssemblyInputs"]
