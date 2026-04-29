# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Lifecycle transitions for review and promotion workflows."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import GateId, JsonModel, ProgramId, ReviewId


class ReviewQueueState(StrEnum):
    """State of one queued review decision."""

    QUEUED = "queued"
    IN_REVIEW = "in_review"
    DEFERRED = "deferred"
    APPROVED = "approved"
    REJECTED = "rejected"


class ReviewQueueDecision(JsonModel):
    """Current review state for one program gate."""

    model_config = ConfigDict(extra="forbid")

    review_id: ReviewId = Field(..., description="Stable review decision identifier.")
    program_id: ProgramId = Field(..., description="Program identifier.")
    gate_id: GateId = Field(..., description="Review gate identifier.")
    state: ReviewQueueState = Field(..., description="Current review state.")
    summary: str = Field(..., min_length=1, description="Current review summary.")
    evidence_ids: list[str] = Field(
        default_factory=list,
        description="Evidence references used in the review decision.",
    )


class ReviewQueueTransition(JsonModel):
    """One audited state transition in the review queue."""

    model_config = ConfigDict(extra="forbid")

    review_id: ReviewId = Field(..., description="Review identifier.")
    from_state: ReviewQueueState = Field(..., description="Previous review state.")
    to_state: ReviewQueueState = Field(..., description="New review state.")
    reason: str = Field(..., min_length=1, description="Why the transition occurred.")
    actor: str = Field(..., min_length=1, description="Actor recording the change.")
    changed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the review transition was recorded.",
    )


class ReviewLifecycleAuditIssue(JsonModel):
    """Issue found while auditing review transition history."""

    model_config = ConfigDict(extra="forbid")

    review_id: ReviewId = Field(..., description="Review identifier.")
    code: str = Field(..., min_length=1, description="Stable audit issue code.")
    message: str = Field(..., min_length=1, description="Human-readable issue.")


_ALLOWED_REVIEW_TRANSITIONS: dict[ReviewQueueState, set[ReviewQueueState]] = {
    ReviewQueueState.QUEUED: {
        ReviewQueueState.IN_REVIEW,
        ReviewQueueState.DEFERRED,
        ReviewQueueState.REJECTED,
    },
    ReviewQueueState.IN_REVIEW: {
        ReviewQueueState.APPROVED,
        ReviewQueueState.REJECTED,
        ReviewQueueState.DEFERRED,
    },
    ReviewQueueState.DEFERRED: {
        ReviewQueueState.QUEUED,
        ReviewQueueState.IN_REVIEW,
        ReviewQueueState.REJECTED,
    },
    ReviewQueueState.APPROVED: set(),
    ReviewQueueState.REJECTED: set(),
}


def transition_review_queue(
    review_id: ReviewId,
    from_state: ReviewQueueState,
    to_state: ReviewQueueState,
    *,
    reason: str,
    actor: str,
) -> ReviewQueueTransition:
    """Build one validated review queue transition."""
    if to_state not in _ALLOWED_REVIEW_TRANSITIONS[from_state]:
        raise ValueError(f"invalid review transition: {from_state} -> {to_state}")
    return ReviewQueueTransition(
        review_id=review_id,
        from_state=from_state,
        to_state=to_state,
        reason=reason,
        actor=actor,
    )


def validate_review_transition_history(
    transitions: list[ReviewQueueTransition],
) -> list[ReviewLifecycleAuditIssue]:
    """Validate review transition history coherence."""
    if not transitions:
        return []
    ordered = sorted(transitions, key=lambda item: item.changed_at)
    issues: list[ReviewLifecycleAuditIssue] = []
    review_id = ordered[0].review_id
    if any(item.review_id != review_id for item in ordered):
        issues.append(
            ReviewLifecycleAuditIssue(
                review_id=review_id,
                code="mixed-review-id",
                message="review transition history should not mix review identifiers",
            )
        )
        return issues
    for left, right in zip(ordered, ordered[1:], strict=False):
        if left.to_state is not right.from_state:
            issues.append(
                ReviewLifecycleAuditIssue(
                    review_id=review_id,
                    code="broken-review-chain",
                    message="review transitions should chain through consecutive states",
                )
            )
        if right.changed_at < left.changed_at:
            issues.append(
                ReviewLifecycleAuditIssue(
                    review_id=review_id,
                    code="out-of-order-review-time",
                    message="review transition timestamps should be non-decreasing",
                )
            )
    return issues
