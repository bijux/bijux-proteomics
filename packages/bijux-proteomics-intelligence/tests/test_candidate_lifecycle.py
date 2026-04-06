# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence import (
    CandidateAssessment,
    CandidateDecision,
    CandidatePortfolio,
    CandidateProposal,
    CandidateStatus,
    CandidateTransition,
    CandidateLifecycleSummary,
    ParetoFrontResult,
    SequenceRiskSignals,
    LiabilityFlag,
    build_risk_profile,
    portfolio_status,
    sequence_risk_signals,
    select_pareto_candidates,
    summarize_candidate_lifecycle,
    transition_candidate,
)

import pytest


def test_build_risk_profile_rolls_liabilities_into_residual_risk() -> None:
    assessment = CandidateAssessment(
        candidate_id="candidate-1",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        liabilities=[
            LiabilityFlag(
                code="aggregation",
                summary="Aggregation hotspot",
                severity=4,
                source="model",
            )
        ],
        evidence_support=0.8,
    )

    profile = build_risk_profile(assessment)

    assert profile.candidate_id == "candidate-1"
    assert profile.manufacturability_risk > 0.0
    assert profile.evidence_uncertainty_risk > 0.0
    assert 0.0 <= profile.sequence_complexity_risk <= 1.0
    assert 0.0 <= profile.residual_risk <= 1.0


def test_portfolio_status_counts_candidate_decisions() -> None:
    portfolio = CandidatePortfolio(
        program_id="prog-1",
        proposals=[
            CandidateProposal(
                candidate_id="candidate-1",
                program_id="prog-1",
                sequence="ACDEFGHIKLMNPQRSTVWY",
                origin="generator",
                rationale="Recover binding.",
            )
        ],
        decisions=[
            CandidateDecision(
                candidate_id="candidate-1",
                status=CandidateStatus.PRIORITIZED,
                decision_summary="Strong evidence and acceptable risk.",
            ),
            CandidateDecision(
                candidate_id="candidate-2",
                status=CandidateStatus.REJECTED,
                decision_summary="Aggregation risk too high.",
            ),
        ],
    )

    counts = portfolio_status(portfolio)

    assert counts["prioritized"] == 1
    assert counts["rejected"] == 1


def test_transition_candidate_enforces_lifecycle_progression() -> None:
    transition = transition_candidate(
        "candidate-1",
        CandidateStatus.PROPOSED,
        CandidateStatus.SCREENED,
        reason="screening completed",
        evidence_ids=["ev-1"],
    )

    assert transition.candidate_id == "candidate-1"
    assert transition.from_status is CandidateStatus.PROPOSED
    assert transition.to_status is CandidateStatus.SCREENED
    assert transition.reason == "screening completed"


def test_transition_candidate_rejects_invalid_jump() -> None:
    with pytest.raises(ValueError):
        transition_candidate(
            "candidate-1",
            CandidateStatus.PROPOSED,
            CandidateStatus.ADVANCED,
            reason="skip directly to advancement",
            evidence_ids=["ev-1"],
        )


def test_transition_candidate_requires_evidence_for_prioritization() -> None:
    with pytest.raises(ValueError):
        transition_candidate(
            "candidate-1",
            CandidateStatus.SCREENED,
            CandidateStatus.PRIORITIZED,
            reason="missing evidence refs",
        )


def test_transition_candidate_supports_deferred_and_reopened_states() -> None:
    deferred = transition_candidate(
        "candidate-1",
        CandidateStatus.SCREENED,
        CandidateStatus.DEFERRED,
        reason="waiting for new evidence",
    )
    reopened = transition_candidate(
        "candidate-1",
        CandidateStatus.DEFERRED,
        CandidateStatus.REOPENED,
        reason="new decisive assay evidence available",
        evidence_ids=["ev-5"],
    )

    assert deferred.to_status is CandidateStatus.DEFERRED
    assert reopened.to_status is CandidateStatus.REOPENED


def test_sequence_risk_signals_capture_basic_sequence_properties() -> None:
    proposal = CandidateProposal(
        candidate_id="candidate-9",
        program_id="prog-1",
        sequence="ACDNNSTVVKK",
        origin="generator",
        rationale="sequence features test",
    )

    signals = sequence_risk_signals(proposal)

    assert isinstance(signals, SequenceRiskSignals)
    assert signals.length == 11
    assert signals.glyco_motif_count >= 1


def test_select_pareto_candidates_preserves_multi_objective_tradeoffs() -> None:
    result = select_pareto_candidates(
        [
            CandidateAssessment(
                candidate_id="candidate-a",
                sequence="ACDEFGHIKLMNPQRSTVWY",
                evidence_support=0.9,
                manufacturability_score=0.6,
                uncertainty=0.2,
            ),
            CandidateAssessment(
                candidate_id="candidate-b",
                sequence="ACDEFGHIKLMNPQRSTVWY",
                evidence_support=0.7,
                manufacturability_score=0.9,
                uncertainty=0.1,
            ),
            CandidateAssessment(
                candidate_id="candidate-c",
                sequence="ACDEFGHIKLMNPQRSTVWY",
                evidence_support=0.6,
                manufacturability_score=0.5,
                uncertainty=0.4,
            ),
        ]
    )

    assert isinstance(result, ParetoFrontResult)
    assert set(result.frontier_candidate_ids) == {"candidate-a", "candidate-b"}
    assert result.dominated_candidate_ids == ["candidate-c"]


def test_summarize_candidate_lifecycle_builds_ordered_status_history() -> None:
    first = transition_candidate(
        "candidate-lifecycle",
        CandidateStatus.PROPOSED,
        CandidateStatus.SCREENED,
        reason="screen complete",
    )
    second = transition_candidate(
        "candidate-lifecycle",
        CandidateStatus.SCREENED,
        CandidateStatus.PRIORITIZED,
        reason="prioritized",
        evidence_ids=["ev-1"],
    )

    summary = summarize_candidate_lifecycle([second, first])

    assert isinstance(summary, CandidateLifecycleSummary)
    assert summary.transition_count == 2
    assert summary.latest_status is CandidateStatus.PRIORITIZED
