# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Interpretation-layer review assembly for biological quant-table workflows."""

from __future__ import annotations

from typing import NamedTuple

from bijux_proteomics.interpretation import (
    PathwayActivityReport,
    PathwayEnrichmentReport,
    RegulatorInferenceReport,
)
from bijux_proteomics.quantification.contracts import DifferentialAbundanceReport
from bijux_proteomics.review.belief.evidence_aware_ranking import (
    EvidenceAwareRankingReport,
)
from bijux_proteomics.review.claims.biological_claim_validation import (
    BiologicalClaimValidationReport,
)
from bijux_proteomics.review.claims.biological_hypotheses import (
    BiologicalHypothesisReport,
)
from bijux_proteomics.workflow.cards.protein_evidence_cards import (
    ProteinEvidenceCardReport,
)
from bijux_proteomics.workflow.cards.protein_mechanism_cards import (
    ProteinMechanismCardReport,
)
from bijux_proteomics.workflow.reports.biological_report_claims import (
    _build_biological_claim_validation_report,
    _build_biological_evidence_aware_ranking_report,
    _build_biological_hypothesis_report,
)
from bijux_proteomics.workflow.reports.biological_report_experiment_review_contracts import (
    BiologicalExperimentReviewReports,
)
from bijux_proteomics.workflow.reports.biological_report_selection_policy import (
    BiologicalResultSelectionPolicy,
)


class BiologicalQuantTableInterpretationReports(NamedTuple):
    """Interpretation reports layered over experiment review outputs."""

    evidence_aware_ranking_report: EvidenceAwareRankingReport | None
    claim_validation_report: BiologicalClaimValidationReport
    biological_hypothesis_report: BiologicalHypothesisReport


def _build_biological_quant_table_interpretation_reports(
    *,
    differential_report: DifferentialAbundanceReport,
    active_selection_policy: BiologicalResultSelectionPolicy,
    protein_cards: ProteinEvidenceCardReport,
    protein_mechanism_cards: ProteinMechanismCardReport,
    pathway_activity_report: PathwayActivityReport | None,
    pathway_enrichment_report: PathwayEnrichmentReport | None,
    regulator_inference_report: RegulatorInferenceReport | None,
    experiment_review_reports: BiologicalExperimentReviewReports,
) -> BiologicalQuantTableInterpretationReports:
    experiment_confidence_report = (
        experiment_review_reports.experiment_confidence_report
    )
    evidence_aware_ranking_report = _build_biological_evidence_aware_ranking_report(
        differential_report,
        protein_cards=protein_cards,
        protein_mechanism_cards=protein_mechanism_cards,
        experiment_confidence_report=experiment_confidence_report,
        pathway_enrichment_report=pathway_enrichment_report,
    )
    claim_validation_report = _build_biological_claim_validation_report(
        differential_report,
        protein_mechanism_cards=protein_mechanism_cards,
        pathway_activity_report=pathway_activity_report,
        regulator_inference_report=regulator_inference_report,
        selection_policy=active_selection_policy,
    )
    biological_hypothesis_report = _build_biological_hypothesis_report(
        claim_validation_report,
        protein_mechanism_cards=protein_mechanism_cards,
        pathway_activity_report=pathway_activity_report,
        regulator_inference_report=regulator_inference_report,
    )
    return BiologicalQuantTableInterpretationReports(
        evidence_aware_ranking_report=evidence_aware_ranking_report,
        claim_validation_report=claim_validation_report,
        biological_hypothesis_report=biological_hypothesis_report,
    )


__all__ = [
    "BiologicalQuantTableInterpretationReports",
    "_build_biological_quant_table_interpretation_reports",
]
