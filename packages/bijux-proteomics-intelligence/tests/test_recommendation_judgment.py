# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from bijux_proteomics.domain.criteria import MeasurementDirection, SuccessCriterion
from bijux_proteomics.domain.program_spec import create_program_spec
from bijux_proteomics_intelligence.briefs import (
    CandidateAssessment,
    build_ranking_sensitivity_report,
    prioritize_candidates,
)
from bijux_proteomics_intelligence.candidates import CandidateRiskProfile
from bijux_proteomics_intelligence.evaluators import (
    ScenarioAction,
    ScenarioEvaluation,
    ScenarioSetEvaluation,
)
from bijux_proteomics_intelligence.evidence_posture import (
    assess_recommendation_readiness,
    ContradictionPosture,
    FreshnessPosture,
    summarize_evidence_contradictions,
    summarize_evidence_freshness,
)
from bijux_proteomics_intelligence.recommendations import (
    build_final_decision_recommendation,
)
from bijux_proteomics_intelligence.review_packets import (
    ComparativeCandidateReviewPacket,
    build_comparative_candidate_review_packet,
)
from bijux_proteomics_knowledge.references.rules import (
    build_ranking_rule_grounding_ledger,
)
from bijux_proteomics_knowledge.evidence import (
    EvidenceBundle,
    EvidenceKind,
    EvidenceRecord,
    EvidenceSourceType,
    EvidenceStrength,
)
from bijux_proteomics_knowledge.references.benchmarks import KnowledgeWorkflowFamily


def _program() -> object:
    program = create_program_spec(
        program_id="prog-judgment",
        name="judgment surface",
        objective="prioritize candidates with grounded analytical judgment",
        target_id="target-judgment",
        target_name="Target Judgment",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="preserve disease-relevant signaling rescue",
    )
    program.success_criteria.append(
        SuccessCriterion(
            criterion_id="binding",
            metric="binding_score",
            direction=MeasurementDirection.MAXIMIZE,
            threshold=0.75,
        )
    )
    return program


def _grounded_bundle() -> EvidenceBundle:
    now = datetime.now(UTC)
    return EvidenceBundle(
        bundle_id="bundle-grounded",
        target_id="target-judgment",
        records=[
            EvidenceRecord(
                evidence_id="evidence-assay",
                kind=EvidenceKind.ASSAY,
                title="Orthogonal assay support",
                source="lab-assay-1",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="supports progression with reproducible assay signal",
                confidence=0.91,
                strength=EvidenceStrength.DECISIVE,
                decision_tags=["progression"],
                observed_at=now - timedelta(days=12),
            ),
            EvidenceRecord(
                evidence_id="evidence-literature",
                kind=EvidenceKind.LITERATURE,
                title="Recent literature support",
                source="PMID:123",
                source_type=EvidenceSourceType.LITERATURE,
                claim="supports disease-relevant target engagement",
                confidence=0.83,
                strength=EvidenceStrength.SUPPORTING,
                decision_tags=["progression"],
                observed_at=now - timedelta(days=40),
            ),
        ],
    )


def _contradictory_bundle() -> EvidenceBundle:
    now = datetime.now(UTC)
    return EvidenceBundle(
        bundle_id="bundle-contradictory",
        target_id="target-judgment",
        records=[
            EvidenceRecord(
                evidence_id="evidence-supports",
                kind=EvidenceKind.ASSAY,
                title="Supportive assay",
                source="lab-assay-a",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="supports progression with stable assay response",
                confidence=0.88,
                strength=EvidenceStrength.DECISIVE,
                decision_tags=["progression"],
                observed_at=now - timedelta(days=420),
            ),
            EvidenceRecord(
                evidence_id="evidence-fails",
                kind=EvidenceKind.ASSAY,
                title="Contradictory assay",
                source="lab-assay-b",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="fails progression because the assay response worsens",
                confidence=0.82,
                strength=EvidenceStrength.DECISIVE,
                decision_tags=["progression"],
                observed_at=now - timedelta(days=395),
            ),
        ],
    )


def _unresolved_contradiction_bundle() -> EvidenceBundle:
    now = datetime.now(UTC)
    return EvidenceBundle(
        bundle_id="bundle-unresolved",
        target_id="target-judgment",
        records=[
            EvidenceRecord(
                evidence_id="evidence-supports",
                kind=EvidenceKind.ASSAY,
                title="Supportive assay",
                source="lab-assay-a",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="supports progression with stable assay response",
                confidence=0.9,
                strength=EvidenceStrength.DECISIVE,
                decision_tags=["progression"],
                observed_at=now - timedelta(days=20),
            ),
            EvidenceRecord(
                evidence_id="evidence-fails",
                kind=EvidenceKind.ASSAY,
                title="Conflicting assay",
                source="lab-assay-b",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="fails progression because the assay response worsens",
                confidence=0.86,
                strength=EvidenceStrength.SUPPORTING,
                decision_tags=["progression"],
                observed_at=now - timedelta(days=18),
            ),
            EvidenceRecord(
                evidence_id="evidence-literature",
                kind=EvidenceKind.LITERATURE,
                title="Context literature",
                source="PMID:456",
                source_type=EvidenceSourceType.LITERATURE,
                claim="documents disease relevance for the progression target context",
                confidence=0.79,
                strength=EvidenceStrength.SUPPORTING,
                decision_tags=["progression"],
                observed_at=now - timedelta(days=25),
            ),
        ],
    )


def _thin_grounding_bundle() -> EvidenceBundle:
    now = datetime.now(UTC)
    return EvidenceBundle(
        bundle_id="bundle-thin-grounding",
        target_id="target-judgment",
        records=[
            EvidenceRecord(
                evidence_id="evidence-literature-thin",
                kind=EvidenceKind.LITERATURE,
                title="Thin literature support",
                source="PMID:thin",
                source_type=EvidenceSourceType.LITERATURE,
                claim="supports progression with weak single-source justification",
                confidence=0.68,
                strength=EvidenceStrength.SUPPORTING,
                decision_tags=["progression"],
                observed_at=now - timedelta(days=14),
            ),
        ],
    )


def _stale_grounded_bundle() -> EvidenceBundle:
    now = datetime.now(UTC)
    return EvidenceBundle(
        bundle_id="bundle-stale-grounded",
        target_id="target-judgment",
        records=[
            EvidenceRecord(
                evidence_id="evidence-assay-stale",
                kind=EvidenceKind.ASSAY,
                title="Stale assay support",
                source="lab-assay-stale",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="supports progression with historical assay support",
                confidence=0.91,
                strength=EvidenceStrength.DECISIVE,
                decision_tags=["progression"],
                observed_at=now - timedelta(days=240),
            ),
            EvidenceRecord(
                evidence_id="evidence-literature-current",
                kind=EvidenceKind.LITERATURE,
                title="Current literature context",
                source="PMID:stale-grounded",
                source_type=EvidenceSourceType.LITERATURE,
                claim="supports disease relevance for the progression target",
                confidence=0.82,
                strength=EvidenceStrength.SUPPORTING,
                decision_tags=["progression"],
                observed_at=now - timedelta(days=22),
            ),
        ],
    )


def test_prioritize_candidates_exposes_grounded_multi_objective_judgment() -> None:
    ranking = prioritize_candidates(
        _program(),
        [
            CandidateAssessment(
                candidate_id="candidate-a",
                sequence="ACDEFGHIKLMNPQRSTVWY",
                metric_scores={"binding_score": 0.86},
                manufacturability_score=0.84,
                uncertainty=0.08,
                evidence_support=0.87,
                reproducibility_score=0.9,
                effect_size_score=0.78,
                assay_feasibility_score=0.88,
                novelty_score=0.61,
                lab_cost_risk=0.12,
                operational_risk=0.09,
            ),
            CandidateAssessment(
                candidate_id="candidate-b",
                sequence="ACDEFGHIKLMNPQRSTVWYA",
                metric_scores={"binding_score": 0.83},
                manufacturability_score=0.7,
                uncertainty=0.12,
                evidence_support=0.74,
                reproducibility_score=0.66,
                effect_size_score=0.69,
                assay_feasibility_score=0.63,
                novelty_score=0.58,
                lab_cost_risk=0.24,
                operational_risk=0.26,
            ),
        ],
        evidence_bundle=_grounded_bundle(),
        workflow_family=KnowledgeWorkflowFamily.DIA,
    )

    top_candidate = ranking.ranked_candidates[0]
    sensitivity = build_ranking_sensitivity_report(top_candidate)

    assert top_candidate.candidate_id == "candidate-a"
    assert top_candidate.explainability["knowledge_grounding_rule_ids"]
    assert (
        top_candidate.explainability["multi_objective_profile"]["scientific_value"]
        > 0.8
    )
    assert (
        top_candidate.explainability["multi_objective_profile"][
            "operational_reliability"
        ]
        > 0.8
    )
    assert sensitivity.dominant_inputs
    assert any(
        entry.input_name in {"scientific_value", "assay_feasibility"}
        for entry in sensitivity.dominant_inputs
    )


def test_evidence_posture_summaries_surface_conflicts_and_staleness() -> None:
    contradictions = summarize_evidence_contradictions(_contradictory_bundle())
    freshness = summarize_evidence_freshness(_contradictory_bundle())

    assert contradictions.conflict_count >= 1
    assert contradictions.posture is ContradictionPosture.BLOCKING
    assert contradictions.conflicting_evidence_ids == (
        "evidence-fails",
        "evidence-supports",
    )
    assert contradictions.exact_conflict_reasons
    assert contradictions.unresolved_questions
    assert freshness.stale_records
    assert freshness.posture is FreshnessPosture.STALE
    assert freshness.stale_record_reasons
    assert freshness.decisive_stale_records == (
        "evidence-fails",
        "evidence-supports",
    )
    assert freshness.freshness_score < 0.8


def test_assess_recommendation_readiness_refuses_contradictory_evidence() -> None:
    result = assess_recommendation_readiness(_contradictory_bundle())

    assert result.disposition.value == "refused"
    assert result.refusal is not None
    assert result.refusal.code == "contradictory_evidence"
    assert "evidence contradictions remain unresolved" in result.refusal.reason


def test_assess_recommendation_readiness_degrades_unresolved_contradiction_pressure() -> (
    None
):
    result = assess_recommendation_readiness(_unresolved_contradiction_bundle())

    assert result.disposition.value == "degraded_success"
    assert result.support_state.value == "ambiguous"
    assert any(
        "contradiction pressure=" in reason for reason in result.degradation_reasons
    )


def test_assess_recommendation_readiness_refuses_thin_grounding_support() -> None:
    result = assess_recommendation_readiness(_thin_grounding_bundle())

    assert result.disposition.value == "refused"
    assert result.refusal is not None
    assert result.refusal.code == "thin_grounding_support"
    assert any(
        "lacks orthogonal support" in detail for detail in result.refusal.reason_details
    )


def test_assess_recommendation_readiness_degrades_stale_grounded_support_with_exact_reasons() -> (
    None
):
    result = assess_recommendation_readiness(_stale_grounded_bundle())

    assert result.disposition.value == "degraded_success"
    assert any(
        reason.startswith("evidence-assay-stale:")
        for reason in result.degradation_reasons
    )
    assert any("stale and should be refreshed" in reason for reason in result.degradation_reasons)


def test_final_decision_recommendation_holds_when_evidence_gate_refuses() -> None:
    grouped = ScenarioSetEvaluation(
        progression=ScenarioEvaluation(
            scenario="progression",
            action=ScenarioAction.ADVANCE,
            confidence=0.84,
        ),
        synthesis=ScenarioEvaluation(
            scenario="synthesis",
            action=ScenarioAction.ADVANCE,
            confidence=0.8,
        ),
        scale_up=ScenarioEvaluation(
            scenario="scale_up",
            action=ScenarioAction.SCALE_UP,
            confidence=0.78,
        ),
        redesign=ScenarioEvaluation(
            scenario="redesign",
            action=ScenarioAction.ADVANCE,
            confidence=0.76,
        ),
    )

    recommendation = build_final_decision_recommendation(
        grouped,
        evidence_bundle=_contradictory_bundle(),
        workflow_family=KnowledgeWorkflowFamily.DIA,
    )

    assert recommendation.action is ScenarioAction.HOLD
    assert recommendation.requires_human_review is True
    assert recommendation.gate_result is not None
    assert recommendation.gate_result.disposition.value == "refused"


def test_comparative_candidate_review_packet_surfaces_multi_objective_deltas() -> None:
    ranking = prioritize_candidates(
        _program(),
        [
            CandidateAssessment(
                candidate_id="candidate-a",
                sequence="ACDEFGHIKLMNPQRSTVWY",
                metric_scores={"binding_score": 0.86},
                manufacturability_score=0.84,
                uncertainty=0.08,
                evidence_support=0.87,
                reproducibility_score=0.9,
                effect_size_score=0.78,
                assay_feasibility_score=0.88,
                novelty_score=0.61,
                lab_cost_risk=0.12,
                operational_risk=0.09,
            ),
            CandidateAssessment(
                candidate_id="candidate-b",
                sequence="ACDEFGHIKLMNPQRSTVWYA",
                metric_scores={"binding_score": 0.83},
                manufacturability_score=0.7,
                uncertainty=0.12,
                evidence_support=0.74,
                reproducibility_score=0.66,
                effect_size_score=0.69,
                assay_feasibility_score=0.63,
                novelty_score=0.58,
                lab_cost_risk=0.24,
                operational_risk=0.26,
            ),
        ],
        evidence_bundle=_grounded_bundle(),
        workflow_family=KnowledgeWorkflowFamily.DIA,
    )
    packet = build_comparative_candidate_review_packet(
        ranking,
        [
            CandidateAssessment(
                candidate_id="candidate-a",
                sequence="ACDEFGHIKLMNPQRSTVWY",
                evidence_support=0.87,
            ),
            CandidateAssessment(
                candidate_id="candidate-b",
                sequence="ACDEFGHIKLMNPQRSTVWYA",
                evidence_support=0.74,
            ),
        ],
        [
            CandidateRiskProfile(candidate_id="candidate-a", residual_risk=0.14),
            CandidateRiskProfile(candidate_id="candidate-b", residual_risk=0.33),
        ],
        preferred_candidate_id="candidate-a",
        compared_candidate_id="candidate-b",
    )

    assert isinstance(packet, ComparativeCandidateReviewPacket)
    assert packet.scientific_value_delta > 0
    assert packet.assay_feasibility_delta > 0
    assert packet.operational_reliability_delta > 0
    assert any("scientific value delta" in line for line in packet.rationale)


def test_grounding_ledger_keeps_reference_provenance_visible() -> None:
    ledger = build_ranking_rule_grounding_ledger(KnowledgeWorkflowFamily.DIA)

    assert ledger.rules
    assert ledger.rules[0].citation_ids
    assert ledger.rules[0].benchmark_ids
    assert ledger.rules[0].known_problem_ids
