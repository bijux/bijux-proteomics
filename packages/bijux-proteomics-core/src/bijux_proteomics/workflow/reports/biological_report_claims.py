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
    build_evidence_aware_ranking_report,
)
from bijux_proteomics.review.claims.biological_claim_validation import (
    BiologicalClaimValidationPolicy,
    BiologicalClaimValidationReport,
    build_biological_claim_validation_report,
)
from bijux_proteomics.review.claims.biological_hypotheses import (
    BiologicalHypothesisReport,
    build_biological_hypothesis_report,
)
from bijux_proteomics.study import (
    ExperimentConfidenceReport,
)
from bijux_proteomics.workflow.cards.protein_evidence_cards import ProteinEvidenceCardReport
from bijux_proteomics.workflow.cards.protein_mechanism_cards import (
    ProteinMechanismCardReport,
)
from bijux_proteomics.workflow.reports.biological_report_claim_candidates import (
    _build_biological_pathway_claim_candidates,
    _build_biological_protein_claim_candidates,
    _build_biological_regulator_claim_candidates,
)
from bijux_proteomics.workflow.reports.biological_report_hypothesis_candidates import (
    _build_biological_pathway_hypothesis_candidates,
    _build_biological_protein_hypothesis_candidates,
    _build_biological_regulator_hypothesis_candidates,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultSelectionPolicy,
)
from bijux_proteomics.workflow.reports.biological_report_ranking import (
    _build_biological_pathway_ranking_candidates,
    _build_biological_protein_ranking_candidates,
)
from bijux_proteomics.workflow.reports.biological_result_graph import (
    BiologicalResultGraphReport,
    build_biological_result_graph_report,
)


def _build_biological_evidence_aware_ranking_report(
    differential_report: DifferentialAbundanceReport,
    *,
    protein_cards: ProteinEvidenceCardReport,
    protein_mechanism_cards: ProteinMechanismCardReport,
    experiment_confidence_report: ExperimentConfidenceReport,
    pathway_enrichment_report: PathwayEnrichmentReport | None,
) -> EvidenceAwareRankingReport:
    protein_candidates = _build_biological_protein_ranking_candidates(
        differential_report,
        protein_cards=protein_cards,
        protein_mechanism_cards=protein_mechanism_cards,
        experiment_confidence_report=experiment_confidence_report,
    )
    pathway_candidates = _build_biological_pathway_ranking_candidates(
        pathway_enrichment_report,
        protein_mechanism_cards=protein_mechanism_cards,
        experiment_confidence_report=experiment_confidence_report,
    )
    return build_evidence_aware_ranking_report(protein_candidates + pathway_candidates)


def _build_biological_claim_validation_report(
    differential_report: DifferentialAbundanceReport,
    *,
    protein_mechanism_cards: ProteinMechanismCardReport,
    pathway_activity_report: PathwayActivityReport | None,
    regulator_inference_report: RegulatorInferenceReport | None,
    selection_policy: BiologicalResultSelectionPolicy,
) -> BiologicalClaimValidationReport:
    candidates = (
        _build_biological_protein_claim_candidates(
            differential_report,
            protein_mechanism_cards=protein_mechanism_cards,
        )
        + _build_biological_pathway_claim_candidates(pathway_activity_report)
        + _build_biological_regulator_claim_candidates(regulator_inference_report)
    )
    return build_biological_claim_validation_report(
        candidates,
        policy=BiologicalClaimValidationPolicy(
            max_adjusted_p_value=selection_policy.max_adjusted_p_value,
            min_robustness_score=0.55,
            min_pathway_activity_delta=0.2,
            min_regulator_score=0.55,
        ),
    )


def _build_biological_hypothesis_report(
    claim_validation_report: BiologicalClaimValidationReport,
    *,
    protein_mechanism_cards: ProteinMechanismCardReport,
    pathway_activity_report: PathwayActivityReport | None,
    regulator_inference_report: RegulatorInferenceReport | None,
) -> BiologicalHypothesisReport:
    candidates = (
        _build_biological_protein_hypothesis_candidates(
            claim_validation_report,
            protein_mechanism_cards=protein_mechanism_cards,
        )
        + _build_biological_pathway_hypothesis_candidates(
            claim_validation_report,
            protein_mechanism_cards=protein_mechanism_cards,
            pathway_activity_report=pathway_activity_report,
        )
        + _build_biological_regulator_hypothesis_candidates(
            claim_validation_report,
            protein_mechanism_cards=protein_mechanism_cards,
            regulator_inference_report=regulator_inference_report,
        )
    )
    return build_biological_hypothesis_report(candidates)
