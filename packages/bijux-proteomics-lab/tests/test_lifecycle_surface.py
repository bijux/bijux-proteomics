# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics_lab import (
    CandidateLabAdvancementDisposition,
    PromotionDecisionState,
    ReviewQueueState,
    decide_candidate_lab_advancement,
    transition_promotion_decision,
    transition_review_queue,
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


def test_decide_candidate_lab_advancement_returns_promote_and_refuse_outcomes() -> (
    None
):
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
    assert refused.disposition is CandidateLabAdvancementDisposition.REFUSE
    assert refused.reasons == ["missing orthogonal confirmation"]
