# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics import create_program_spec
from bijux_proteomics_knowledge import (
    DecisionReadiness,
    EvidenceCoverage,
)
from bijux_proteomics_intelligence import (
    CandidateRanking,
    CandidateRiskProfile,
    EvaluatorPolicyBundle,
    HoldPolicyConfig,
    HypothesisStatus,
    ProgressionPolicyConfig,
    ProgressionPolicy,
    RankedCandidate,
    ScaleUpPolicy,
    ScenarioAction,
    evaluate_portfolio_balance,
    summarize_scenario_consensus,
    build_intelligence_review_packet,
    summarize_hold_pressure,
    summarize_scenario_confidence_spread,
    derive_decision_escalation_flags,
    build_final_decision_recommendation,
    RedesignPolicyConfig,
    SynthesisPolicy,
    evaluate_for_progression,
    evaluate_for_redesign,
    evaluate_for_scale_up,
    evaluate_for_synthesis,
    evaluate_all_scenarios,
)


def _ready_state() -> DecisionReadiness:
    return DecisionReadiness(
        target_id="target-1",
        ready=True,
        blockers=[],
        recommendations=[],
        coverage=EvidenceCoverage(
            bundle_id="bundle-1",
            target_id="target-1",
            by_kind={"literature": 1, "structure": 1, "assay": 2, "pathway": 0, "safety": 0},
            missing_kinds=[],
            decisive_records=2,
            mean_confidence=0.85,
        ),
    )


def test_evaluate_for_progression_advances_when_ready_and_ranked() -> None:
    program = create_program_spec(
        program_id="prog-1",
        name="progression",
        objective="advance a viable candidate",
        target_id="target-1",
        target_name="Target 1",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="stabilize productive packing",
    )
    ranking = CandidateRanking(
        program_id="prog-1",
        ranked_candidates=[
            RankedCandidate(candidate_id="candidate-1", score=1.2, rank=1)
        ],
    )

    evaluation = evaluate_for_progression(program, ranking, _ready_state())

    assert evaluation.action is ScenarioAction.ADVANCE
    assert evaluation.hypothesis_status is HypothesisStatus.SUPPORTED
    assert evaluation.confidence > 0.8


def test_evaluate_for_progression_holds_when_top_candidate_has_many_blockers() -> None:
    program = create_program_spec(
        program_id="prog-blockers",
        name="progression blockers",
        objective="hold progression when top blocker pressure is high",
        target_id="target-1",
        target_name="Target 1",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="require blocker reduction before advance",
    )
    ranking = CandidateRanking(
        program_id="prog-blockers",
        ranked_candidates=[
            RankedCandidate(
                candidate_id="candidate-1",
                score=1.2,
                rank=1,
                explainability={"blockers": ["agg risk", "off-target risk", "yield risk"]},
            )
        ],
    )

    evaluation = evaluate_for_progression(program, ranking, _ready_state())

    assert evaluation.action is ScenarioAction.HOLD
    assert evaluation.unresolved_questions == ["agg risk", "off-target risk", "yield risk"]


def test_evaluate_for_progression_holds_when_top_candidate_confidence_is_low() -> None:
    program = create_program_spec(
        program_id="prog-low-conf",
        name="progression confidence gate",
        objective="hold progression when top confidence is weak",
        target_id="target-low-conf",
        target_name="Target Low Conf",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="enforce confidence floor",
    )
    ranking = CandidateRanking(
        program_id="prog-low-conf",
        ranked_candidates=[
            RankedCandidate(
                candidate_id="candidate-1",
                score=1.2,
                rank=1,
                explainability={"confidence": 0.45, "blockers": []},
            )
        ],
    )

    evaluation = evaluate_for_progression(program, ranking, _ready_state())

    assert evaluation.action is ScenarioAction.HOLD
    assert "top_candidate_confidence=0.45" in evaluation.unresolved_questions


def test_evaluate_for_synthesis_redesigns_on_high_risk_top_candidate() -> None:
    ranking = CandidateRanking(
        program_id="prog-1",
        ranked_candidates=[
            RankedCandidate(candidate_id="candidate-1", score=1.2, rank=1)
        ],
    )
    risks = [
        CandidateRiskProfile(
            candidate_id="candidate-1",
            residual_risk=0.6,
        )
    ]

    evaluation = evaluate_for_synthesis(
        ranking,
        _ready_state(),
        risks,
        policy=SynthesisPolicy(
            policy_id="strict-synthesis",
            maximum_residual_risk=0.5,
        ),
    )

    assert evaluation.action is ScenarioAction.REDESIGN
    assert evaluation.key_discriminating_experiment is not None
    assert evaluation.unresolved_questions


def test_evaluate_for_synthesis_holds_on_blocker_pressure() -> None:
    ranking = CandidateRanking(
        program_id="prog-1",
        ranked_candidates=[
            RankedCandidate(
                candidate_id="candidate-1",
                score=1.2,
                rank=1,
                explainability={"blockers": ["risk-a", "risk-b", "risk-c"]},
            )
        ],
    )
    risks = [
        CandidateRiskProfile(
            candidate_id="candidate-1",
            residual_risk=0.2,
        )
    ]

    evaluation = evaluate_for_synthesis(ranking, _ready_state(), risks)

    assert evaluation.action is ScenarioAction.HOLD
    assert evaluation.unresolved_questions == ["risk-a", "risk-b", "risk-c"]


def test_evaluate_for_synthesis_holds_when_top_candidate_confidence_is_low() -> None:
    ranking = CandidateRanking(
        program_id="prog-1",
        ranked_candidates=[
            RankedCandidate(
                candidate_id="candidate-1",
                score=1.2,
                rank=1,
                explainability={"confidence": 0.5, "blockers": []},
            )
        ],
    )
    risks = [CandidateRiskProfile(candidate_id="candidate-1", residual_risk=0.2)]

    evaluation = evaluate_for_synthesis(ranking, _ready_state(), risks)

    assert evaluation.action is ScenarioAction.HOLD
    assert "top_candidate_confidence=0.50" in evaluation.unresolved_questions


def test_evaluate_for_synthesis_redesigns_on_safety_channel_risk() -> None:
    ranking = CandidateRanking(
        program_id="prog-safety",
        ranked_candidates=[RankedCandidate(candidate_id="candidate-1", score=1.2, rank=1)],
    )
    risks = [
        CandidateRiskProfile(
            candidate_id="candidate-1",
            residual_risk=0.3,
            safety_risk=0.55,
        )
    ]

    evaluation = evaluate_for_synthesis(ranking, _ready_state(), risks)

    assert evaluation.action is ScenarioAction.REDESIGN
    assert "safety_risk=0.55 exceeds policy limit" in evaluation.unresolved_questions


def test_evaluate_for_scale_up_holds_on_safety_channel_risk() -> None:
    ranking = CandidateRanking(
        program_id="prog-scale-safety",
        ranked_candidates=[RankedCandidate(candidate_id="candidate-1", score=1.2, rank=1)],
    )
    risks = [
        CandidateRiskProfile(
            candidate_id="candidate-1",
            residual_risk=0.1,
            safety_risk=0.3,
        )
    ]

    evaluation = evaluate_for_scale_up(ranking, _ready_state(), risks)

    assert evaluation.action is ScenarioAction.HOLD
    assert "safety_risk=0.30 remains above policy" in evaluation.unresolved_questions


def test_evaluate_for_scale_up_requires_low_risk_and_decisive_evidence() -> None:
    ranking = CandidateRanking(
        program_id="prog-1",
        ranked_candidates=[
            RankedCandidate(candidate_id="candidate-1", score=1.2, rank=1)
        ],
    )
    risks = [
        CandidateRiskProfile(
            candidate_id="candidate-1",
            residual_risk=0.1,
        )
    ]

    evaluation = evaluate_for_scale_up(
        ranking,
        _ready_state(),
        risks,
        policy=ScaleUpPolicy(
            policy_id="scale-up-default",
            minimum_decisive_records=2,
            maximum_residual_risk=0.2,
        ),
    )

    assert evaluation.action is ScenarioAction.SCALE_UP


def test_evaluate_for_redesign_requests_redesign_when_candidates_are_rejected() -> None:
    ranking = CandidateRanking(
        program_id="prog-1",
        ranked_candidates=[],
        rejected_candidates=["candidate-1"],
    )

    evaluation = evaluate_for_redesign(ranking, _ready_state())

    assert evaluation.action is ScenarioAction.REDESIGN


def test_evaluate_for_progression_can_allow_evidence_only_progression() -> None:
    program = create_program_spec(
        program_id="prog-2",
        name="evidence progression",
        objective="allow evidence progression without ranking",
        target_id="target-2",
        target_name="Target 2",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="progress when evidence is ready even before ranking",
    )
    ranking = CandidateRanking(program_id="prog-2", ranked_candidates=[])

    evaluation = evaluate_for_progression(
        program,
        ranking,
        _ready_state(),
        policy=ProgressionPolicy(
            policy_id="evidence-first",
            require_ranked_candidate=False,
        ),
    )

    assert evaluation.action is ScenarioAction.ADVANCE


def test_evaluator_policy_bundle_exposes_all_policy_ids() -> None:
    bundle = EvaluatorPolicyBundle()

    assert bundle.progression.policy_id == "progression-default"
    assert bundle.synthesis.policy_id == "synthesis-default"
    assert bundle.scale_up.policy_id == "scale-up-default"
    assert bundle.redesign.policy_id == "redesign-default"


def test_policy_configs_have_expected_default_thresholds() -> None:
    assert ProgressionPolicyConfig(policy_id="p").minimum_evidence_support == 0.6
    assert HoldPolicyConfig(policy_id="h").minimum_confidence_for_release == 0.65
    assert RedesignPolicyConfig(policy_id="r").residual_risk_trigger == 0.5


def test_evaluate_all_scenarios_returns_grouped_actions() -> None:
    program = create_program_spec(
        program_id="prog-3",
        name="bundle eval",
        objective="run all evaluator scenarios together",
        target_id="target-3",
        target_name="Target 3",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="group scenario evaluation",
    )
    ranking = CandidateRanking(
        program_id="prog-3",
        ranked_candidates=[RankedCandidate(candidate_id="candidate-1", score=1.2, rank=1)],
    )
    risks = [CandidateRiskProfile(candidate_id="candidate-1", residual_risk=0.1)]

    grouped = evaluate_all_scenarios(
        program,
        ranking,
        _ready_state(),
        risks,
        policies=EvaluatorPolicyBundle(),
    )

    assert grouped.progression.action is ScenarioAction.ADVANCE
    assert grouped.scale_up.action is ScenarioAction.SCALE_UP


def test_evaluate_portfolio_balance_flags_low_diversity_high_risk_shortlist() -> None:
    ranking = CandidateRanking(
        program_id="prog-portfolio",
        ranked_candidates=[
            RankedCandidate(
                candidate_id="candidate-1",
                score=1.2,
                rank=1,
                explainability={"blockers": ["aggregation"]},
            ),
            RankedCandidate(
                candidate_id="candidate-2",
                score=1.1,
                rank=2,
                explainability={"blockers": ["aggregation"]},
            ),
        ],
    )
    risks = [
        CandidateRiskProfile(candidate_id="candidate-1", residual_risk=0.6),
        CandidateRiskProfile(candidate_id="candidate-2", residual_risk=0.55),
    ]

    report = evaluate_portfolio_balance(ranking, risks, top_n=2)

    assert report.balanced_portfolio is False
    assert report.liability_diversity == 1
    assert report.mean_residual_risk > 0.5


def test_summarize_scenario_consensus_reports_conflicting_actions() -> None:
    program = create_program_spec(
        program_id="prog-consensus",
        name="consensus",
        objective="summarize scenario action consensus",
        target_id="target-consensus",
        target_name="Target Consensus",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="evaluate scenario action coherence",
    )
    ranking = CandidateRanking(
        program_id="prog-consensus",
        ranked_candidates=[RankedCandidate(candidate_id="candidate-1", score=1.2, rank=1)],
    )
    risks = [CandidateRiskProfile(candidate_id="candidate-1", residual_risk=0.1, safety_risk=0.4)]
    grouped = evaluate_all_scenarios(program, ranking, _ready_state(), risks, policies=EvaluatorPolicyBundle())

    consensus = summarize_scenario_consensus(grouped)

    assert consensus.action_counts
    assert consensus.conflicting_actions is True


def test_build_intelligence_review_packet_combines_consensus_and_portfolio() -> None:
    program = create_program_spec(
        program_id="prog-packet",
        name="review packet",
        objective="compose intelligence review packet",
        target_id="target-packet",
        target_name="Target Packet",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="integrate intelligence outputs for review",
    )
    ranking = CandidateRanking(
        program_id="prog-packet",
        ranked_candidates=[RankedCandidate(candidate_id="candidate-1", score=1.2, rank=1)],
    )
    risks = [CandidateRiskProfile(candidate_id="candidate-1", residual_risk=0.6, safety_risk=0.6)]
    grouped = evaluate_all_scenarios(program, ranking, _ready_state(), risks, policies=EvaluatorPolicyBundle())

    packet = build_intelligence_review_packet(grouped, ranking, risks)

    assert packet.consensus.action_counts
    assert packet.portfolio.candidate_count == 1
    assert packet.review_ready is False


def test_summarize_hold_pressure_counts_hold_actions() -> None:
    grouped = evaluate_all_scenarios(
        create_program_spec(
            program_id="prog-hold-pressure",
            name="hold pressure",
            objective="summarize hold pressure",
            target_id="target-hold-pressure",
            target_name="Target Hold Pressure",
            sequence="ACDEFGHIKLMNPQRSTVWY",
            organism="human",
            mechanism="hold pressure tracking",
        ),
        CandidateRanking(
            program_id="prog-hold-pressure",
            ranked_candidates=[RankedCandidate(candidate_id="candidate-1", score=1.0, rank=1)],
        ),
        _ready_state(),
        [CandidateRiskProfile(candidate_id="candidate-1", residual_risk=0.1, safety_risk=0.6)],
        policies=EvaluatorPolicyBundle(),
    )

    summary = summarize_hold_pressure(grouped)

    assert summary.total_scenarios == 4
    assert summary.hold_count >= 1


def test_summarize_scenario_confidence_spread_reports_range() -> None:
    grouped = evaluate_all_scenarios(
        create_program_spec(
            program_id="prog-confidence-spread",
            name="confidence spread",
            objective="summarize confidence spread across scenarios",
            target_id="target-confidence-spread",
            target_name="Target Confidence Spread",
            sequence="ACDEFGHIKLMNPQRSTVWY",
            organism="human",
            mechanism="confidence spread tracking",
        ),
        CandidateRanking(
            program_id="prog-confidence-spread",
            ranked_candidates=[RankedCandidate(candidate_id="candidate-1", score=1.0, rank=1)],
        ),
        _ready_state(),
        [CandidateRiskProfile(candidate_id="candidate-1", residual_risk=0.6, safety_risk=0.6)],
        policies=EvaluatorPolicyBundle(),
    )

    spread = summarize_scenario_confidence_spread(grouped)

    assert spread.maximum_confidence >= spread.minimum_confidence
    assert spread.spread >= 0.0


def test_derive_decision_escalation_flags_triggers_human_review() -> None:
    grouped = evaluate_all_scenarios(
        create_program_spec(
            program_id="prog-escalation",
            name="escalation",
            objective="derive escalation flags from scenario outputs",
            target_id="target-escalation",
            target_name="Target Escalation",
            sequence="ACDEFGHIKLMNPQRSTVWY",
            organism="human",
            mechanism="trigger escalation when scenarios conflict",
        ),
        CandidateRanking(
            program_id="prog-escalation",
            ranked_candidates=[RankedCandidate(candidate_id="candidate-1", score=1.0, rank=1)],
        ),
        _ready_state(),
        [CandidateRiskProfile(candidate_id="candidate-1", residual_risk=0.6, safety_risk=0.6)],
        policies=EvaluatorPolicyBundle(),
    )

    flags = derive_decision_escalation_flags(grouped)

    assert flags.escalate_to_human_review is True


def test_build_final_decision_recommendation_uses_consensus_and_escalation() -> None:
    grouped = evaluate_all_scenarios(
        create_program_spec(
            program_id="prog-final-recommendation",
            name="final recommendation",
            objective="build final recommendation from scenario intelligence",
            target_id="target-final-recommendation",
            target_name="Target Final Recommendation",
            sequence="ACDEFGHIKLMNPQRSTVWY",
            organism="human",
            mechanism="combine consensus and escalation",
        ),
        CandidateRanking(
            program_id="prog-final-recommendation",
            ranked_candidates=[RankedCandidate(candidate_id="candidate-1", score=1.0, rank=1)],
        ),
        _ready_state(),
        [CandidateRiskProfile(candidate_id="candidate-1", residual_risk=0.6, safety_risk=0.6)],
        policies=EvaluatorPolicyBundle(),
    )

    recommendation = build_final_decision_recommendation(grouped)

    assert recommendation.reasons
    assert recommendation.requires_human_review is True
