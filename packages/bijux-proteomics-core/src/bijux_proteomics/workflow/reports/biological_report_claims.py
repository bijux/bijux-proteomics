# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Biological claim and hypothesis report entrypoints."""

from __future__ import annotations

from bijux_proteomics.interpretation import (
    PathwayActivityReport,
    PathwayEnrichmentReport,
    RegulatorInferenceReport,
)
from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceReport,
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
from bijux_proteomics.study import (
    ExperimentConfidenceReport,
)
from bijux_proteomics.workflow.cards.protein_evidence_cards import (
    ProteinEvidenceCardReport,
)
from bijux_proteomics.workflow.cards.protein_mechanism_cards import (
    ProteinMechanismCardReport,
)
from bijux_proteomics.workflow.reports.biological_report_claim_validation_reports import (
    _build_biological_claim_validation_report as _build_claim_validation_report,
)
from bijux_proteomics.workflow.reports.biological_report_hypothesis_reports import (
    _build_biological_hypothesis_report as _build_hypothesis_report,
)
from bijux_proteomics.workflow.reports.biological_report_ranking_reports import (
    _build_biological_evidence_aware_ranking_report as _build_ranking_report,
)
from bijux_proteomics.workflow.reports.biological_report_selection_policy import (
    BiologicalResultSelectionPolicy,
)


def _build_biological_evidence_aware_ranking_report(
    differential_report: DifferentialAbundanceReport,
    *,
    protein_cards: ProteinEvidenceCardReport,
    protein_mechanism_cards: ProteinMechanismCardReport,
    experiment_confidence_report: ExperimentConfidenceReport,
    pathway_enrichment_report: PathwayEnrichmentReport | None,
) -> EvidenceAwareRankingReport:
    return _build_ranking_report(
        differential_report,
        protein_cards=protein_cards,
        protein_mechanism_cards=protein_mechanism_cards,
        experiment_confidence_report=experiment_confidence_report,
        pathway_enrichment_report=pathway_enrichment_report,
    )


def _build_biological_claim_validation_report(
    differential_report: DifferentialAbundanceReport,
    *,
    protein_mechanism_cards: ProteinMechanismCardReport,
    pathway_activity_report: PathwayActivityReport | None,
    regulator_inference_report: RegulatorInferenceReport | None,
    selection_policy: BiologicalResultSelectionPolicy,
) -> BiologicalClaimValidationReport:
    return _build_claim_validation_report(
        differential_report,
        protein_mechanism_cards=protein_mechanism_cards,
        pathway_activity_report=pathway_activity_report,
        regulator_inference_report=regulator_inference_report,
        selection_policy=selection_policy,
    )


def _build_biological_hypothesis_report(
    claim_validation_report: BiologicalClaimValidationReport,
    *,
    protein_mechanism_cards: ProteinMechanismCardReport,
    pathway_activity_report: PathwayActivityReport | None,
    regulator_inference_report: RegulatorInferenceReport | None,
) -> BiologicalHypothesisReport:
    return _build_hypothesis_report(
        claim_validation_report,
        protein_mechanism_cards=protein_mechanism_cards,
        pathway_activity_report=pathway_activity_report,
        regulator_inference_report=regulator_inference_report,
    )


__all__ = [
    "_build_biological_claim_validation_report",
    "_build_biological_evidence_aware_ranking_report",
    "_build_biological_hypothesis_report",
]
