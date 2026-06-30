# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Final bundle materialization for biological report assembly."""

from __future__ import annotations

from typing import TYPE_CHECKING

from bijux_proteomics.workflow.reports.biological_report_bundle_contracts import (
    BiologicalResultReportBundle,
)
from bijux_proteomics.workflow.reports.biological_report_summary_contracts import (
    BiologicalResultReportSummary,
)

if TYPE_CHECKING:
    from bijux_proteomics.interpretation import (
        BiologicalContextImportReport,
        BiologicalContextMappingReport,
        BiologicalForegroundBackgroundModel,
        ComplexActivityReport,
        ComplexEnrichmentReport,
        CompartmentBiologyReport,
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
    from bijux_proteomics.workflow.reports.biological_report_models import (
        BiologicalReportSectionConfidenceEntry,
        BiologicalResultSelectionPolicy,
    )
    from bijux_proteomics.workflow.reports.biological_result_graph import (
        BiologicalResultGraphReport,
    )
    from bijux_proteomics.workflow.studies.cohort_stratification import (
        CohortStratificationReport,
    )


_BIOLOGICAL_RESULT_REPORT_BUNDLE_NOTE = (
    "biological reporting assembles governed protein differential analysis, "
    "protein evidence cards, annotation mapping, optional user-supplied "
    "biological context mapping, enrichment, volcano review, heatmap "
    "preparation, and sample exploration into one owned workflow bundle with "
    "experiment-level confidence scoring, tissue and cell-type context review, "
    "claim validation, biological hypotheses, and explicit component reasons"
)


def _materialize_biological_result_report_bundle(
    *,
    differential_report: DifferentialAbundanceReport,
    graph_report: BiologicalResultGraphReport,
    annotation_report: ProteinAnnotationMappingReport,
    protein_cards: ProteinEvidenceCardReport,
    protein_mechanism_cards: ProteinMechanismCardReport,
    experiment_confidence_report: ExperimentConfidenceReport,
    evidence_aware_ranking_report: EvidenceAwareRankingReport | None,
    claim_validation_report: BiologicalClaimValidationReport | None,
    biological_hypothesis_report: BiologicalHypothesisReport | None,
    foreground_background_model: BiologicalForegroundBackgroundModel,
    regulator_evidence_import_report: RegulatorEvidenceImportReport | None,
    regulator_inference_report: RegulatorInferenceReport | None,
    context_import_report: BiologicalContextImportReport | None,
    context_mapping_report: BiologicalContextMappingReport | None,
    cohort_stratification_report: CohortStratificationReport | None,
    tissue_cell_type_context_report: TissueCellTypeContextReport | None,
    drug_target_report: DrugTargetInterpretationReport | None,
    disease_phenotype_report: DiseasePhenotypeInterpretationReport | None,
    compartment_biology_report: CompartmentBiologyReport | None,
    pathway_activity_report: PathwayActivityReport | None,
    complex_activity_report: ComplexActivityReport | None,
    go_enrichment_report: GoEnrichmentReport | None,
    pathway_enrichment_report: PathwayEnrichmentReport | None,
    complex_enrichment_report: ComplexEnrichmentReport | None,
    volcano_review: VolcanoReviewReport,
    heatmap_report: HeatmapPreparationReport,
    sample_exploration_report: SampleExplorationReport,
    selection_policy: BiologicalResultSelectionPolicy,
    section_confidence_entries: tuple[BiologicalReportSectionConfidenceEntry, ...],
    summary: BiologicalResultReportSummary,
) -> BiologicalResultReportBundle:
    return BiologicalResultReportBundle(
        differential_report=differential_report,
        graph_report=graph_report,
        annotation_report=annotation_report,
        protein_cards=protein_cards,
        protein_mechanism_cards=protein_mechanism_cards,
        experiment_confidence_report=experiment_confidence_report,
        evidence_aware_ranking_report=evidence_aware_ranking_report,
        claim_validation_report=claim_validation_report,
        biological_hypothesis_report=biological_hypothesis_report,
        foreground_background_model=foreground_background_model,
        regulator_evidence_import_report=regulator_evidence_import_report,
        regulator_inference_report=regulator_inference_report,
        context_import_report=context_import_report,
        context_mapping_report=context_mapping_report,
        cohort_stratification_report=cohort_stratification_report,
        tissue_cell_type_context_report=tissue_cell_type_context_report,
        drug_target_report=drug_target_report,
        disease_phenotype_report=disease_phenotype_report,
        compartment_biology_report=compartment_biology_report,
        pathway_activity_report=pathway_activity_report,
        complex_activity_report=complex_activity_report,
        go_enrichment_report=go_enrichment_report,
        pathway_enrichment_report=pathway_enrichment_report,
        complex_enrichment_report=complex_enrichment_report,
        volcano_review=volcano_review,
        heatmap_report=heatmap_report,
        sample_exploration_report=sample_exploration_report,
        selection_policy=selection_policy,
        section_confidence_entries=section_confidence_entries,
        summary=summary,
        note=_BIOLOGICAL_RESULT_REPORT_BUNDLE_NOTE,
    )


__all__ = [
    "_BIOLOGICAL_RESULT_REPORT_BUNDLE_NOTE",
    "_materialize_biological_result_report_bundle",
]
