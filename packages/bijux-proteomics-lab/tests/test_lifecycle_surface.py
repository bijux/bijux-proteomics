# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics_lab import (
    ReviewQueueState,
    transition_review_queue,
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
