# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence import (
    CandidateAssessment,
    CandidateDecision,
    CandidatePortfolio,
    CandidateProposal,
    CandidateStatus,
    LiabilityFlag,
    build_risk_profile,
    portfolio_status,
)


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
    assert profile.residual_risk == 0.2


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
