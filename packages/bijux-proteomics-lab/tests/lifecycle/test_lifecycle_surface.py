# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics_lab.lifecycle import (
    AssayLifecycleStage,
    AssayLifecycleState,
    CandidateLabAdvancementDisposition,
    CandidateFollowUpSignal,
    PromotionDecisionState,
    ReviewQueueState,
    advance_assay_lifecycle,
    decide_candidate_lab_advancement,
    transition_promotion_decision,
    transition_review_queue,
    validate_candidate_follow_up_handoff,
    validate_promotion_transition_history,
    validate_review_transition_history,
)


def test_transition_review_queue_enforces_valid_progression() -> None:
    queued = transition_review_queue(
        "review-binding-gate",
        ReviewQueueState.QUEUED,
        ReviewQueueState.IN_REVIEW,
        reason="gate entered scientific review",
        actor="reviewer-1",
    )
    approved = transition_review_queue(
        "review-binding-gate",
        ReviewQueueState.IN_REVIEW,
        ReviewQueueState.APPROVED,
        reason="evidence packet passed review",
        actor="reviewer-1",
    )

    assert queued.review_id == "review-binding-gate"
    assert approved.to_state is ReviewQueueState.APPROVED


def test_transition_review_queue_rejects_invalid_terminal_jumps() -> None:
    with pytest.raises(ValueError, match="invalid review transition"):
        transition_review_queue(
            "review-binding-gate",
            ReviewQueueState.QUEUED,
            ReviewQueueState.APPROVED,
            reason="skip review",
            actor="reviewer-1",
        )


def test_validate_review_transition_history_flags_broken_chains() -> None:
    first = transition_review_queue(
        "review-binding-gate",
        ReviewQueueState.QUEUED,
        ReviewQueueState.IN_REVIEW,
        reason="started review",
        actor="reviewer-1",
    )
    broken = transition_review_queue(
        "review-binding-gate",
        ReviewQueueState.DEFERRED,
        ReviewQueueState.IN_REVIEW,
        reason="restarted after defer",
        actor="reviewer-2",
    )

    issues = validate_review_transition_history([first, broken])

    assert issues
    assert issues[0].code == "broken-review-chain"


def test_transition_promotion_decision_enforces_valid_progression() -> None:
    ready = transition_promotion_decision(
        "promotion-batch-1",
        PromotionDecisionState.PENDING,
        PromotionDecisionState.READY,
        reason="all assay quality gates passed",
        actor="reviewer-1",
    )
    promoted = transition_promotion_decision(
        "promotion-batch-1",
        PromotionDecisionState.READY,
        PromotionDecisionState.PROMOTED,
        reason="evidence bundle emitted",
        actor="reviewer-1",
    )

    assert ready.promotion_id == "promotion-batch-1"
    assert promoted.to_state is PromotionDecisionState.PROMOTED


def test_transition_promotion_decision_rejects_invalid_jumps() -> None:
    with pytest.raises(ValueError, match="invalid promotion transition"):
        transition_promotion_decision(
            "promotion-batch-1",
            PromotionDecisionState.PENDING,
            PromotionDecisionState.PROMOTED,
            reason="skip readiness gate",
            actor="reviewer-1",
        )


def test_validate_promotion_transition_history_flags_broken_chains() -> None:
    first = transition_promotion_decision(
        "promotion-batch-1",
        PromotionDecisionState.PENDING,
        PromotionDecisionState.READY,
        reason="ready for emission",
        actor="reviewer-1",
    )
    broken = transition_promotion_decision(
        "promotion-batch-1",
        PromotionDecisionState.BLOCKED,
        PromotionDecisionState.PENDING,
        reason="reopened after blocker review",
        actor="reviewer-2",
    )

    issues = validate_promotion_transition_history([first, broken])

    assert issues
    assert issues[0].code == "broken-promotion-chain"


def test_decide_candidate_lab_advancement_returns_promote_and_refuse_outcomes() -> None:
    promoted = decide_candidate_lab_advancement(
        program_id="prog-lab",
        candidate_id="cand-1",
        evidence_ids=["ev-1", "ev-2"],
        blocking_findings=[],
        recommended_actions=["schedule confirmation assay"],
        ready_for_synthesis=True,
    )
    refused = decide_candidate_lab_advancement(
        program_id="prog-lab",
        candidate_id="cand-2",
        evidence_ids=["ev-3"],
        blocking_findings=["missing orthogonal confirmation"],
        recommended_actions=["collect orthogonal confirmation"],
        ready_for_synthesis=False,
    )

    assert promoted.disposition is CandidateLabAdvancementDisposition.PROMOTE
    assert promoted.decision_code == "candidate_ready_for_lab_execution"
    assert refused.disposition is CandidateLabAdvancementDisposition.REFUSE
    assert refused.decision_code == "candidate_refused_for_lab_execution"
    assert refused.reasons == ["missing orthogonal confirmation"]
    assert "candidate stays out of lab execution" in refused.audit_trail


def test_advance_assay_lifecycle_requires_reproducible_validation_before_targeted_work() -> (
    None
):
    decision = advance_assay_lifecycle(
        AssayLifecycleState(
            assay_id="assay-validate",
            current_stage=AssayLifecycleStage.VALIDATION,
            completed_stages=(
                AssayLifecycleStage.DISCOVERY,
                AssayLifecycleStage.VERIFICATION,
            ),
            required_transition_evidence=("orthogonal assay", "matched controls"),
        ),
        evidence_ready=True,
        reproducibility_ready=False,
        targeted_panel_ready=False,
        blocking_findings=["replicate drift remains unresolved"],
        recommended_actions=["repeat validation with matched controls"],
    )

    assert decision.ready_to_advance is False
    assert decision.to_stage is None
    assert decision.decision_code == "hold_for_blockers"
    assert "replicate drift remains unresolved" in decision.reasons
    assert any(
        "targeted follow-up panel" in item for item in decision.required_next_actions
    )
    assert "hold because blocking findings remain" in decision.audit_trail


def test_validate_candidate_follow_up_handoff_refuses_unjustified_signal() -> None:
    validation = validate_candidate_follow_up_handoff(
        program_id="prog-lab-handoff",
        signal=CandidateFollowUpSignal(
            candidate_id="cand-uncertain",
            recommendation="hold candidate until contradictions are resolved",
            decision_ready=False,
            contradiction_pressure=0.62,
            freshness_pressure=0.18,
            unresolved_questions=("does the orthogonal assay reproduce",),
            evidence_ids=("ev-1",),
            required_assay_ids=("assay-a", "assay-b"),
            recommended_next_steps=("resolve the orthogonal assay contradiction",),
            policy_lineage_id="policy-balanced",
        ),
        available_assay_ids=["assay-a"],
        ready_for_execution=False,
        operational_blockers=["instrument maintenance window is still open"],
    )

    assert validation.accepted is False
    assert "contradiction pressure is too high for lab handoff" in validation.blockers
    assert "upstream recommendation is still on hold" in validation.blockers
    assert any(
        "operational blockers" in step for step in validation.required_next_actions
    )


def test_validate_candidate_follow_up_handoff_accepts_grounded_signal() -> None:
    validation = validate_candidate_follow_up_handoff(
        program_id="prog-lab-handoff",
        signal=CandidateFollowUpSignal(
            candidate_id="cand-ready",
            recommendation="prioritize candidate-ready for follow-up review",
            decision_ready=True,
            contradiction_pressure=0.11,
            freshness_pressure=0.08,
            unresolved_questions=(),
            evidence_ids=("ev-1", "ev-2"),
            required_assay_ids=("assay-a", "assay-b"),
            recommended_next_steps=("schedule orthogonal follow-up assays",),
            policy_lineage_id="policy-balanced",
        ),
        available_assay_ids=["assay-a", "assay-b", "assay-c"],
        ready_for_execution=True,
    )

    assert validation.accepted is True
    assert validation.accepted_assay_ids == ["assay-a", "assay-b"]
    assert "schedule accepted follow-up assays" in validation.required_next_actions
