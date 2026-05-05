# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Lifecycle transitions for review and promotion workflows."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import (
    AssayId,
    BatchId,
    ClaimId,
    GateId,
    JsonModel,
    ProgramId,
)
from bijux_proteomics_foundation.ids import PromotionId, ReviewId


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


class PromotionDecisionState(StrEnum):
    """State of one lab-to-knowledge promotion decision."""

    PENDING = "pending"
    READY = "ready"
    BLOCKED = "blocked"
    PROMOTED = "promoted"
    SUPERSEDED = "superseded"


class AssayLifecycleStage(StrEnum):
    """Operational assay lifecycle stage from discovery through targeted follow-up."""

    DISCOVERY = "discovery"
    VERIFICATION = "verification"
    VALIDATION = "validation"
    TARGETED_FOLLOW_UP = "targeted_follow_up"


class AssayLifecycleState(JsonModel):
    """Current lifecycle state for one assay across discovery and follow-up."""

    model_config = ConfigDict(extra="forbid")

    assay_id: AssayId = Field(..., description="Assay identifier.")
    current_stage: AssayLifecycleStage = Field(
        ..., description="Current lifecycle stage."
    )
    completed_stages: tuple[AssayLifecycleStage, ...] = Field(default_factory=tuple)
    blocking_findings: tuple[str, ...] = Field(default_factory=tuple)
    required_transition_evidence: tuple[str, ...] = Field(default_factory=tuple)


class AssayLifecycleDecision(JsonModel):
    """Advance, hold, or complete one assay lifecycle transition."""

    model_config = ConfigDict(extra="forbid")

    assay_id: AssayId = Field(..., description="Assay identifier.")
    from_stage: AssayLifecycleStage
    to_stage: AssayLifecycleStage | None = Field(
        default=None,
        description="Next lifecycle stage when advancement is allowed.",
    )
    ready_to_advance: bool = Field(
        ..., description="Whether the assay may advance to the next stage."
    )
    decision_code: str = Field(..., min_length=1)
    reasons: list[str] = Field(default_factory=list)
    required_next_actions: list[str] = Field(default_factory=list)
    audit_trail: tuple[str, ...] = Field(default_factory=tuple)


class CandidateFollowUpSignal(JsonModel):
    """Lab-facing summary of one intelligence recommendation that needs skepticism."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    recommendation: str = Field(..., min_length=1)
    decision_ready: bool = Field(
        ...,
        description="Whether the upstream recommendation claims decision readiness.",
    )
    contradiction_pressure: float = Field(..., ge=0.0, le=1.0)
    freshness_pressure: float = Field(..., ge=0.0, le=1.0)
    unresolved_questions: tuple[str, ...] = Field(default_factory=tuple)
    evidence_ids: tuple[str, ...] = Field(default_factory=tuple)
    required_assay_ids: tuple[AssayId, ...] = Field(default_factory=tuple)
    recommended_next_steps: tuple[str, ...] = Field(default_factory=tuple)
    policy_lineage_id: str | None = Field(default=None, min_length=1)


class CandidateHandoffValidation(JsonModel):
    """Validation result for turning an intelligence follow-up signal into lab work."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    candidate_id: str = Field(..., min_length=1)
    accepted: bool = Field(
        ..., description="Whether the handoff is justified for lab progression."
    )
    accepted_assay_ids: list[AssayId] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    skepticism_notes: list[str] = Field(default_factory=list)
    required_next_actions: list[str] = Field(default_factory=list)


class PromotionDecision(JsonModel):
    """Current promotion state for one assay outcome."""

    model_config = ConfigDict(extra="forbid")

    promotion_id: PromotionId = Field(
        ..., description="Stable promotion decision identifier."
    )
    batch_id: BatchId = Field(..., description="Batch identifier.")
    assay_id: AssayId = Field(..., description="Assay identifier.")
    state: PromotionDecisionState = Field(..., description="Current promotion state.")
    linked_claim_ids: list[ClaimId] = Field(
        default_factory=list,
        description="Claim identifiers updated by the promotion decision.",
    )
    related_evidence_ids: list[str] = Field(
        default_factory=list,
        description="Evidence identifiers emitted by the promotion decision.",
    )


class PromotionTransition(JsonModel):
    """One audited transition in promotion lifecycle state."""

    model_config = ConfigDict(extra="forbid")

    promotion_id: PromotionId = Field(..., description="Promotion identifier.")
    from_state: PromotionDecisionState = Field(
        ..., description="Previous promotion state."
    )
    to_state: PromotionDecisionState = Field(..., description="New promotion state.")
    reason: str = Field(..., min_length=1, description="Why the state changed.")
    actor: str = Field(..., min_length=1, description="Actor recording the change.")
    changed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the transition was recorded.",
    )


class PromotionLifecycleAuditIssue(JsonModel):
    """Issue found while auditing promotion transition history."""

    model_config = ConfigDict(extra="forbid")

    promotion_id: PromotionId = Field(..., description="Promotion identifier.")
    code: str = Field(..., min_length=1, description="Stable audit issue code.")
    message: str = Field(..., min_length=1, description="Human-readable issue.")


class CandidateLabAdvancementDisposition(StrEnum):
    """Promotion or refusal outcome for advancing a candidate into lab work."""

    PROMOTE = "promote"
    REFUSE = "refuse"


class CandidateLabAdvancementDecision(JsonModel):
    """Auditable advancement decision for candidate entry into lab execution."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    candidate_id: str = Field(..., min_length=1, description="Candidate identifier.")
    disposition: CandidateLabAdvancementDisposition = Field(
        ..., description="Whether the candidate advances into lab work."
    )
    decision_code: str = Field(..., min_length=1)
    evidence_ids: list[str] = Field(
        default_factory=list,
        description="Evidence identifiers attached to the decision.",
    )
    reasons: list[str] = Field(
        default_factory=list,
        description="Primary reasons for promotion or refusal.",
    )
    follow_up_actions: list[str] = Field(
        default_factory=list,
        description="Actions that must happen next.",
    )
    audit_trail: tuple[str, ...] = Field(default_factory=tuple)


_ALLOWED_PROMOTION_TRANSITIONS: dict[
    PromotionDecisionState, set[PromotionDecisionState]
] = {
    PromotionDecisionState.PENDING: {
        PromotionDecisionState.READY,
        PromotionDecisionState.BLOCKED,
    },
    PromotionDecisionState.READY: {
        PromotionDecisionState.PROMOTED,
        PromotionDecisionState.BLOCKED,
    },
    PromotionDecisionState.BLOCKED: {
        PromotionDecisionState.PENDING,
        PromotionDecisionState.SUPERSEDED,
    },
    PromotionDecisionState.PROMOTED: {PromotionDecisionState.SUPERSEDED},
    PromotionDecisionState.SUPERSEDED: set(),
}


def transition_promotion_decision(
    promotion_id: PromotionId,
    from_state: PromotionDecisionState,
    to_state: PromotionDecisionState,
    *,
    reason: str,
    actor: str,
) -> PromotionTransition:
    """Build one validated promotion lifecycle transition."""
    if to_state not in _ALLOWED_PROMOTION_TRANSITIONS[from_state]:
        raise ValueError(f"invalid promotion transition: {from_state} -> {to_state}")
    return PromotionTransition(
        promotion_id=promotion_id,
        from_state=from_state,
        to_state=to_state,
        reason=reason,
        actor=actor,
    )


def validate_promotion_transition_history(
    transitions: list[PromotionTransition],
) -> list[PromotionLifecycleAuditIssue]:
    """Validate promotion transition history coherence."""
    if not transitions:
        return []
    ordered = sorted(transitions, key=lambda item: item.changed_at)
    issues: list[PromotionLifecycleAuditIssue] = []
    promotion_id = ordered[0].promotion_id
    if any(item.promotion_id != promotion_id for item in ordered):
        issues.append(
            PromotionLifecycleAuditIssue(
                promotion_id=promotion_id,
                code="mixed-promotion-id",
                message="promotion transition history should not mix promotion identifiers",
            )
        )
        return issues
    for left, right in zip(ordered, ordered[1:], strict=False):
        if left.to_state is not right.from_state:
            issues.append(
                PromotionLifecycleAuditIssue(
                    promotion_id=promotion_id,
                    code="broken-promotion-chain",
                    message="promotion transitions should chain through consecutive states",
                )
            )
        if right.changed_at < left.changed_at:
            issues.append(
                PromotionLifecycleAuditIssue(
                    promotion_id=promotion_id,
                    code="out-of-order-promotion-time",
                    message="promotion transition timestamps should be non-decreasing",
                )
            )
    return issues


_LIFECYCLE_NEXT_STAGE: dict[AssayLifecycleStage, AssayLifecycleStage | None] = {
    AssayLifecycleStage.DISCOVERY: AssayLifecycleStage.VERIFICATION,
    AssayLifecycleStage.VERIFICATION: AssayLifecycleStage.VALIDATION,
    AssayLifecycleStage.VALIDATION: AssayLifecycleStage.TARGETED_FOLLOW_UP,
    AssayLifecycleStage.TARGETED_FOLLOW_UP: None,
}


def advance_assay_lifecycle(
    state: AssayLifecycleState,
    *,
    evidence_ready: bool,
    reproducibility_ready: bool,
    targeted_panel_ready: bool,
    blocking_findings: list[str] | None = None,
    recommended_actions: list[str] | None = None,
) -> AssayLifecycleDecision:
    """Advance one assay through discovery, verification, validation, and follow-up."""
    blocking_findings = list(blocking_findings or [])
    recommended_actions = list(recommended_actions or [])
    audit_trail = [
        f"stage={state.current_stage.value}",
        f"evidence_ready={str(evidence_ready).lower()}",
        f"reproducibility_ready={str(reproducibility_ready).lower()}",
        f"targeted_panel_ready={str(targeted_panel_ready).lower()}",
    ]
    next_stage = _LIFECYCLE_NEXT_STAGE[state.current_stage]
    if next_stage is None:
        return AssayLifecycleDecision(
            assay_id=state.assay_id,
            from_stage=state.current_stage,
            to_stage=None,
            ready_to_advance=False,
            decision_code="targeted_follow_up_terminal_stage",
            reasons=["assay already reached targeted follow-up"],
            required_next_actions=[
                "execute the targeted follow-up work and review outcomes"
            ],
            audit_trail=tuple(audit_trail + ["terminal targeted follow-up stage reached"]),
        )

    blockers = list(state.blocking_findings) + blocking_findings
    reasons: list[str] = []
    required_next_actions_out = list(recommended_actions)
    ready_to_advance = False

    if blockers:
        reasons.extend(blockers)
        audit_trail.append("blocking findings remain unresolved")
    if state.current_stage is AssayLifecycleStage.DISCOVERY:
        ready_to_advance = evidence_ready and not blockers
        if not evidence_ready:
            reasons.append("discovery evidence is not strong enough for verification")
            required_next_actions_out.append("collect stronger discovery evidence")
    elif state.current_stage is AssayLifecycleStage.VERIFICATION:
        ready_to_advance = evidence_ready and reproducibility_ready and not blockers
        if not evidence_ready:
            reasons.append("verification evidence remains incomplete")
        if not reproducibility_ready:
            reasons.append("verification lacks reproducible signal across repeats")
            required_next_actions_out.append(
                "repeat the verification assay with matched controls"
            )
    else:
        ready_to_advance = (
            evidence_ready
            and reproducibility_ready
            and targeted_panel_ready
            and not blockers
        )
        if not targeted_panel_ready:
            reasons.append("targeted follow-up panel is not yet justified")
            required_next_actions_out.append(
                "define the targeted follow-up panel and transition controls"
            )
        if not reproducibility_ready:
            reasons.append(
                "validation evidence is not reproducible enough for targeted follow-up"
            )
        if not evidence_ready:
            reasons.append("validation evidence remains incomplete")

    if ready_to_advance:
        decision_code = f"advance_to_{next_stage.value}"
        audit_trail.append(f"advance to {next_stage.value}")
    elif blockers:
        decision_code = "hold_for_blockers"
        audit_trail.append("hold because blocking findings remain")
    elif not evidence_ready:
        decision_code = "hold_for_evidence"
        audit_trail.append("hold because evidence readiness is incomplete")
    elif (
        state.current_stage is AssayLifecycleStage.VERIFICATION
        and not reproducibility_ready
    ):
        decision_code = "hold_for_reproducibility"
        audit_trail.append("hold because reproducibility is insufficient")
    elif (
        state.current_stage is AssayLifecycleStage.VALIDATION
        and not targeted_panel_ready
    ):
        decision_code = "hold_for_targeted_panel"
        audit_trail.append("hold because the targeted panel is not justified")
    else:
        decision_code = "hold_for_readiness"
        audit_trail.append("hold because readiness is incomplete")

    if ready_to_advance:
        reasons.append(
            f"advance from {state.current_stage.value} to {next_stage.value}"
        )
        required_next_actions_out.append(
            f"prepare {next_stage.value} assays and controls"
        )

    return AssayLifecycleDecision(
        assay_id=state.assay_id,
        from_stage=state.current_stage,
        to_stage=next_stage if ready_to_advance else None,
        ready_to_advance=ready_to_advance,
        decision_code=decision_code,
        reasons=reasons or ["lifecycle state is ready to advance"],
        required_next_actions=sorted(
            {action for action in required_next_actions_out if action.strip()}
        ),
        audit_trail=tuple(audit_trail),
    )


def validate_candidate_follow_up_handoff(
    *,
    program_id: ProgramId,
    signal: CandidateFollowUpSignal,
    available_assay_ids: list[AssayId],
    ready_for_execution: bool,
    operational_blockers: list[str] | None = None,
) -> CandidateHandoffValidation:
    """Refuse lab handoff when recommendation posture is not operationally justified."""
    operational_blockers = list(operational_blockers or [])
    available_assay_set = set(available_assay_ids)
    blockers: list[str] = []
    skepticism_notes: list[str] = []

    if not signal.decision_ready:
        blockers.append("upstream follow-up signal is not decision-ready")
    if not signal.policy_lineage_id:
        blockers.append("upstream follow-up signal does not expose policy lineage")
    if not signal.evidence_ids:
        blockers.append("upstream follow-up signal does not attach supporting evidence")
    if signal.contradiction_pressure >= 0.45:
        blockers.append("contradiction pressure is too high for lab handoff")
    elif signal.contradiction_pressure >= 0.25:
        skepticism_notes.append(
            "contradiction pressure needs explicit monitoring during handoff"
        )
    if signal.freshness_pressure >= 0.45:
        blockers.append("supporting evidence is too stale for expensive follow-up")
    elif signal.freshness_pressure >= 0.25:
        skepticism_notes.append("refresh supporting evidence before irreversible spend")
    if signal.unresolved_questions:
        blockers.append(
            "unresolved questions remain open on the intelligence recommendation"
        )
    if "hold" in signal.recommendation.lower():
        blockers.append("upstream recommendation is still on hold")
    if not ready_for_execution:
        blockers.append("lab execution is not currently ready")
    blockers.extend(operational_blockers)

    accepted_assay_ids = sorted(
        assay_id
        for assay_id in signal.required_assay_ids
        if assay_id in available_assay_set
    )
    missing_assay_ids = sorted(
        assay_id
        for assay_id in signal.required_assay_ids
        if assay_id not in available_assay_set
    )
    if missing_assay_ids:
        blockers.append(
            "required follow-up assays are not currently available: "
            + ", ".join(missing_assay_ids)
        )
    if not accepted_assay_ids and signal.required_assay_ids:
        skepticism_notes.append("no required assays are immediately executable")

    accepted = not blockers
    required_next_actions = sorted(
        {
            *signal.recommended_next_steps,
            *(
                ["clear operational blockers before scheduling handoff"]
                if blockers
                else ["schedule accepted follow-up assays"]
            ),
        }
    )

    return CandidateHandoffValidation(
        program_id=program_id,
        candidate_id=signal.candidate_id,
        accepted=accepted,
        accepted_assay_ids=accepted_assay_ids,
        blockers=blockers,
        skepticism_notes=skepticism_notes,
        required_next_actions=required_next_actions,
    )


def decide_candidate_lab_advancement(
    *,
    program_id: ProgramId,
    candidate_id: str,
    evidence_ids: list[str],
    blocking_findings: list[str],
    recommended_actions: list[str],
    ready_for_synthesis: bool,
) -> CandidateLabAdvancementDecision:
    """Decide whether a candidate should advance into lab execution."""
    if ready_for_synthesis and not blocking_findings:
        return CandidateLabAdvancementDecision(
            program_id=program_id,
            candidate_id=candidate_id,
            disposition=CandidateLabAdvancementDisposition.PROMOTE,
            decision_code="candidate_ready_for_lab_execution",
            evidence_ids=evidence_ids,
            reasons=["review packet is ready for lab execution"],
            follow_up_actions=recommended_actions,
            audit_trail=(
                "review packet is synthesis-ready",
                "no blocking findings remain",
                "candidate advances into lab execution",
            ),
        )
    return CandidateLabAdvancementDecision(
        program_id=program_id,
        candidate_id=candidate_id,
        disposition=CandidateLabAdvancementDisposition.REFUSE,
        decision_code="candidate_refused_for_lab_execution",
        evidence_ids=evidence_ids,
        reasons=blocking_findings or ["review packet is not ready for lab execution"],
        follow_up_actions=recommended_actions,
        audit_trail=(
            "review packet is not synthesis-ready",
            "blocking findings remain open",
            "candidate stays out of lab execution",
        ),
    )
