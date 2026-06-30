# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Section-confidence preparation for biological result report bundles."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, NamedTuple

from bijux_proteomics.workflow.reports.biological_report_section_metadata import (
    BiologicalReportSectionConfidenceEntry,
    BiologicalReportSectionConfidenceLabel,
)
from bijux_proteomics.workflow.reports.biological_report_section_confidence import (
    _build_biological_report_section_confidence_entries,
    _count_section_confidence_labels,
)

if TYPE_CHECKING:
    from bijux_proteomics.interpretation import (
        BiologicalForegroundBackgroundModel,
        ComplexActivityReport,
        CompartmentBiologyReport,
        DiseasePhenotypeInterpretationReport,
        DrugTargetInterpretationReport,
        PathwayActivityReport,
        RegulatorInferenceReport,
        TissueCellTypeContextReport,
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
    from bijux_proteomics.workflow.cards.protein_mechanism_cards import (
        ProteinMechanismCardReport,
    )
    from bijux_proteomics.workflow.studies.cohort_stratification import (
        CohortStratificationReport,
    )
    from bijux_proteomics.study import ExperimentConfidenceReport


class BiologicalReportBundleConfidenceState(NamedTuple):
    """Prepared section-confidence state for one biological result bundle."""

    entries: tuple[BiologicalReportSectionConfidenceEntry, ...]
    counts: Mapping[BiologicalReportSectionConfidenceLabel, int]


def _build_biological_report_bundle_confidence_state(
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
) -> BiologicalReportBundleConfidenceState:
    entries = _build_biological_report_section_confidence_entries(
        experiment_confidence_report=experiment_confidence_report,
        evidence_aware_ranking_report=evidence_aware_ranking_report,
        claim_validation_report=claim_validation_report,
        biological_hypothesis_report=biological_hypothesis_report,
        foreground_background_model=foreground_background_model,
        regulator_inference_report=regulator_inference_report,
        drug_target_report=drug_target_report,
        disease_phenotype_report=disease_phenotype_report,
        cohort_stratification_report=cohort_stratification_report,
        tissue_cell_type_context_report=tissue_cell_type_context_report,
        compartment_biology_report=compartment_biology_report,
        pathway_activity_report=pathway_activity_report,
        complex_activity_report=complex_activity_report,
        protein_mechanism_cards=protein_mechanism_cards,
    )
    return BiologicalReportBundleConfidenceState(
        entries=entries,
        counts=_count_section_confidence_labels(entries),
    )


__all__ = [
    "BiologicalReportBundleConfidenceState",
    "_build_biological_report_bundle_confidence_state",
]
