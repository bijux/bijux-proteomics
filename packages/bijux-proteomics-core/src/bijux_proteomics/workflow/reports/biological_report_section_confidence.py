# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Biological report section confidence orchestration."""

from __future__ import annotations

from bijux_proteomics.interpretation import (
    BiologicalForegroundBackgroundModel,
    ComplexActivityReport,
    DiseasePhenotypeInterpretationReport,
    DrugTargetInterpretationReport,
    PathwayActivityReport,
    RegulatorInferenceReport,
    TissueCellTypeContextReport,
)
from bijux_proteomics.interpretation.compartment_biology import (
    CompartmentBiologyReport,
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
from bijux_proteomics.study import ExperimentConfidenceReport
from bijux_proteomics.workflow.cards.protein_mechanism_cards import (
    ProteinMechanismCardReport,
)
from bijux_proteomics.workflow.reports.biological_report_activity_confidence import (
    _build_activity_section_confidence_entries,
)
from bijux_proteomics.workflow.reports.biological_report_context_confidence import (
    _build_context_section_confidence_entries,
)
from bijux_proteomics.workflow.reports.biological_report_evidence_confidence import (
    _build_evidence_section_confidence_entries,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalReportSectionConfidenceEntry,
    BiologicalReportSectionConfidenceLabel,
)
from bijux_proteomics.workflow.studies.cohort_stratification import (
    CohortStratificationReport,
)


def _build_biological_report_section_confidence_entries(
    *,
    experiment_confidence_report: ExperimentConfidenceReport,
    evidence_aware_ranking_report: EvidenceAwareRankingReport | None,
    claim_validation_report: BiologicalClaimValidationReport | None,
    biological_hypothesis_report: BiologicalHypothesisReport | None,
    foreground_background_model: BiologicalForegroundBackgroundModel,
    regulator_inference_report: RegulatorInferenceReport | None,
    drug_target_report: DrugTargetInterpretationReport | None,
    disease_phenotype_report: DiseasePhenotypeInterpretationReport | None,
    cohort_stratification_report: CohortStratificationReport | None,
    tissue_cell_type_context_report: TissueCellTypeContextReport | None,
    compartment_biology_report: CompartmentBiologyReport | None,
    pathway_activity_report: PathwayActivityReport | None,
    complex_activity_report: ComplexActivityReport | None,
    protein_mechanism_cards: ProteinMechanismCardReport,
) -> tuple[BiologicalReportSectionConfidenceEntry, ...]:
    return (
        _build_evidence_section_confidence_entries(
            experiment_confidence_report=experiment_confidence_report,
            evidence_aware_ranking_report=evidence_aware_ranking_report,
            claim_validation_report=claim_validation_report,
            biological_hypothesis_report=biological_hypothesis_report,
            foreground_background_model=foreground_background_model,
            regulator_inference_report=regulator_inference_report,
            protein_mechanism_cards=protein_mechanism_cards,
        )
        + _build_context_section_confidence_entries(
            drug_target_report=drug_target_report,
            disease_phenotype_report=disease_phenotype_report,
            cohort_stratification_report=cohort_stratification_report,
            tissue_cell_type_context_report=tissue_cell_type_context_report,
            compartment_biology_report=compartment_biology_report,
        )
        + _build_activity_section_confidence_entries(
            pathway_activity_report=pathway_activity_report,
            complex_activity_report=complex_activity_report,
        )
    )


def _count_section_confidence_labels(
    entries: tuple[BiologicalReportSectionConfidenceEntry, ...],
) -> dict[BiologicalReportSectionConfidenceLabel, int]:
    counts = dict.fromkeys(BiologicalReportSectionConfidenceLabel, 0)
    for entry in entries:
        counts[entry.confidence_label] += 1
    return counts
