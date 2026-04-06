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
    CandidateScientificProfile,
    CandidateVariantContext,
    MutationAnnotation,
    MutationBurdenSignals,
    PortfolioRiskSummary,
    TransitionAuditIssue,
    ParsedMutation,
    CandidateAssayAgendaItem,
    PortfolioMutationBurdenSummary,
    ParetoFrontResult,
    SequenceRiskSignals,
    LiabilityFlag,
    build_risk_profile,
    build_candidate_scientific_profile,
    mutation_burden_signals,
    summarize_portfolio_risk,
    validate_transition_history,
    parse_mutation_token,
    build_mutation_annotations,
    build_candidate_assay_agenda,
    summarize_portfolio_mutation_burden,
    portfolio_status,
    sequence_risk_signals,
    select_pareto_candidates,
    summarize_variant_context,
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


def test_summarize_variant_context_groups_regions_and_conservation_risk() -> None:
    context = summarize_variant_context(
        "candidate-variant",
        [
            MutationAnnotation(
                mutation="A101V",
                region="activation-loop",
                expected_effect="stabilize active conformation",
                conservation_score=0.91,
            ),
            MutationAnnotation(
                mutation="G205S",
                region="allosteric-site",
                expected_effect="reduce off-target family engagement",
                conservation_score=0.42,
            ),
        ],
    )

    assert isinstance(context, CandidateVariantContext)
    assert context.affected_regions == ["activation-loop", "allosteric-site"]
    assert context.elevated_conservation_risk is True
    assert context.mechanistic_hypotheses == [
        "reduce off-target family engagement",
        "stabilize active conformation",
    ]


def test_build_candidate_scientific_profile_links_risk_and_assay_rationale() -> None:
    profile = build_candidate_scientific_profile(
        CandidateAssessment(
            candidate_id="candidate-science-1",
            sequence="VVVVVVVVVVVVVVVVVVVV",
            liabilities=[
                LiabilityFlag(
                    code="safety-off-target",
                    summary="potential off-target family risk",
                    severity=4,
                    source="model",
                )
            ],
            manufacturability_score=0.35,
            evidence_support=0.7,
        ),
        [
            MutationAnnotation(
                mutation="A101V",
                region="active-site",
                expected_effect="stabilize active state",
                conservation_score=0.92,
            )
        ],
    )

    assert isinstance(profile, CandidateScientificProfile)
    assert profile.variant_context.elevated_conservation_risk is True
    assert profile.risk_profile.manufacturability_risk > 0.3
    assert len(profile.assay_rationale) >= 2


def test_mutation_burden_signals_capture_conserved_and_region_spread() -> None:
    signals = mutation_burden_signals(
        "candidate-burden",
        [
            MutationAnnotation(
                mutation="A101V",
                region="active-site",
                expected_effect="stabilize active conformation",
                conservation_score=0.9,
            ),
            MutationAnnotation(
                mutation="L215P",
                region="interface",
                expected_effect="improve specificity",
                conservation_score=0.45,
            ),
            MutationAnnotation(
                mutation="G216S",
                region="interface",
                expected_effect="improve specificity",
                conservation_score=0.81,
            ),
        ],
    )

    assert isinstance(signals, MutationBurdenSignals)
    assert signals.mutation_count == 3
    assert signals.conserved_mutation_count == 2
    assert signals.affected_region_count == 2
    assert signals.burden_risk_index > 0.0


def test_summarize_portfolio_risk_reports_high_risk_candidates_and_channel() -> None:
    summary = summarize_portfolio_risk(
        [
            CandidateRiskProfile(candidate_id="c1", residual_risk=0.62, safety_risk=0.7),
            CandidateRiskProfile(candidate_id="c2", residual_risk=0.3, safety_risk=0.2),
        ],
        high_risk_threshold=0.5,
    )

    assert isinstance(summary, PortfolioRiskSummary)
    assert summary.mean_residual_risk > 0.4
    assert summary.high_risk_candidate_ids == ["c1"]


def test_validate_transition_history_flags_broken_status_chain() -> None:
    first = transition_candidate(
        "candidate-audit",
        CandidateStatus.PROPOSED,
        CandidateStatus.SCREENED,
        reason="screen complete",
    )
    broken = CandidateTransition(
        candidate_id="candidate-audit",
        from_status=CandidateStatus.PROPOSED,
        to_status=CandidateStatus.PRIORITIZED,
        reason="invalid history jump",
        evidence_ids=["ev-1"],
        changed_at=first.changed_at,
    )

    issues = validate_transition_history([first, broken])

    assert issues
    assert isinstance(issues[0], TransitionAuditIssue)
    assert any(issue.code == "status-link-broken" for issue in issues)


def test_parse_mutation_token_extracts_wild_type_position_and_variant() -> None:
    parsed = parse_mutation_token("A123V")

    assert isinstance(parsed, ParsedMutation)
    assert parsed.wild_type == "A"
    assert parsed.position == 123
    assert parsed.variant == "V"


def test_parse_mutation_token_rejects_invalid_patterns() -> None:
    with pytest.raises(ValueError):
        parse_mutation_token("A12")


def test_build_mutation_annotations_supports_position_maps() -> None:
    annotations = build_mutation_annotations(
        ["A10V", "G20S"],
        expected_effect="improve selectivity",
        region_by_position={10: "active-site", 20: "interface"},
        conservation_by_position={10: 0.91, 20: 0.42},
    )

    assert [annotation.region for annotation in annotations] == ["active-site", "interface"]
    assert annotations[0].conservation_score == 0.91


def test_build_candidate_assay_agenda_prioritizes_higher_risk_profiles() -> None:
    profile_high = build_candidate_scientific_profile(
        CandidateAssessment(
            candidate_id="candidate-high",
            sequence="VVVVVVVVVVVVVVVVVVVV",
            manufacturability_score=0.3,
            evidence_support=0.6,
        ),
        [MutationAnnotation(mutation="A101V", region="active-site", expected_effect="stabilize", conservation_score=0.9)],
    )
    profile_low = build_candidate_scientific_profile(
        CandidateAssessment(
            candidate_id="candidate-low",
            sequence="ACDEFGHIKLMNPQRSTVWY",
            manufacturability_score=0.9,
            evidence_support=0.9,
        ),
        [MutationAnnotation(mutation="G20S", region="loop", expected_effect="tune", conservation_score=0.2)],
    )

    agenda = build_candidate_assay_agenda([profile_low, profile_high])

    assert isinstance(agenda[0], CandidateAssayAgendaItem)
    assert agenda[0].candidate_id == "candidate-high"
    assert agenda[0].priority == 1


def test_summarize_portfolio_mutation_burden_aggregates_contexts() -> None:
    summary = summarize_portfolio_mutation_burden(
        [
            summarize_variant_context(
                "c1",
                [MutationAnnotation(mutation="A10V", region="core", expected_effect="stabilize", conservation_score=0.9)],
            ),
            summarize_variant_context(
                "c2",
                [MutationAnnotation(mutation="G20S", region="loop", expected_effect="tune", conservation_score=0.2)],
            ),
        ]
    )

    assert isinstance(summary, PortfolioMutationBurdenSummary)
    assert summary.candidate_count == 2
    assert summary.total_mutations == 2
    assert summary.total_conserved_mutations == 1
