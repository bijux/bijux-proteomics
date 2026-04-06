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
    ProgressionPolicyConfig,
    ProgressionPolicy,
    RankedCandidate,
    ScaleUpPolicy,
    ScenarioAction,
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
