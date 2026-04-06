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
    ProgressionPolicy,
    RankedCandidate,
    ScaleUpPolicy,
    ScenarioAction,
    SynthesisPolicy,
    evaluate_for_progression,
    evaluate_for_redesign,
    evaluate_for_scale_up,
    evaluate_for_synthesis,
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
