# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Reviewable handoff surfaces for targeted follow-up work."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import AssayId, JsonModel
from bijux_proteomics_foundation.refusals import OperationRefusal, RefusalKind
from bijux_proteomics_foundation.results import OperationResult
from bijux_proteomics_lab.lifecycle import CandidateHandoffValidation
from bijux_proteomics_lab.planning import ExecutableAssayPlan, ReviewPacket
from bijux_proteomics_lab.risk import (
    AssayRiskAssessment,
    assess_assay_risk,
)


class TransitionReviewDisposition(StrEnum):
    """Disposition for one targeted transition candidate."""

    APPROVED = "approved"
    EXPLORATORY = "exploratory"
    REFUSED = "refused"


class TargetedTransitionCandidate(JsonModel):
    """Candidate transition for targeted follow-up review."""

    model_config = ConfigDict(extra="forbid")

    transition_id: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    precursor_mz: float = Field(..., gt=0.0)
    product_mz: float = Field(..., gt=0.0)
    peptide_uniqueness_score: float = Field(..., ge=0.0, le=1.0)
    localization_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    quant_reproducibility_score: float = Field(..., ge=0.0, le=1.0)
    assay_feasibility_score: float = Field(..., ge=0.0, le=1.0)
    predicted_failure_risk: float = Field(..., ge=0.0, le=1.0)
    required_controls: tuple[str, ...] = Field(default_factory=tuple)


class TargetedTransitionReviewEntry(JsonModel):
    """Review outcome for one targeted transition candidate."""

    model_config = ConfigDict(extra="forbid")

    transition_id: str = Field(..., min_length=1)
    disposition: TransitionReviewDisposition
    risk_assessment: AssayRiskAssessment
    missing_controls: tuple[str, ...] = Field(default_factory=tuple)
    reasons: tuple[str, ...] = Field(default_factory=tuple)


class TargetedTransitionReview(JsonModel):
    """Review summary for a targeted transition list."""

    model_config = ConfigDict(extra="forbid")

    assay_id: AssayId = Field(..., description="Assay identifier.")
    approved_transition_ids: tuple[str, ...] = Field(default_factory=tuple)
    exploratory_transition_ids: tuple[str, ...] = Field(default_factory=tuple)
    refused_transition_ids: tuple[str, ...] = Field(default_factory=tuple)
    readiness_score: float = Field(..., ge=0.0, le=1.0)
    entries: tuple[TargetedTransitionReviewEntry, ...] = Field(default_factory=tuple)
    notes: tuple[str, ...] = Field(default_factory=tuple)


class HandoffSupportLevel(StrEnum):
    """Support level for one handoff statement."""

    SUPPORTED = "supported"
    EXPLORATORY = "exploratory"
    BLOCKED = "blocked"


class HandoffSupportStatement(JsonModel):
    """One structured statement in a handoff explanation."""

    model_config = ConfigDict(extra="forbid")

    level: HandoffSupportLevel
    summary: str = Field(..., min_length=1)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)


class HandoffExplanation(JsonModel):
    """Structured explanation of what a handoff can honestly claim."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    supported: tuple[HandoffSupportStatement, ...] = Field(default_factory=tuple)
    exploratory: tuple[HandoffSupportStatement, ...] = Field(default_factory=tuple)
    blocked: tuple[HandoffSupportStatement, ...] = Field(default_factory=tuple)
    summary: str = Field(..., min_length=1)


class LabExecutionRefusal(JsonModel):
    """Explicit refusal surface for irresponsible assay handoffs."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    blocked_assay_ids: tuple[AssayId, ...] = Field(default_factory=tuple)
    explanation: HandoffExplanation
    result: OperationResult


def review_targeted_transition_candidates(
    *,
    assay_id: AssayId,
    candidates: tuple[TargetedTransitionCandidate, ...],
    available_controls: tuple[str, ...] = (),
) -> TargetedTransitionReview:
    """Review targeted transitions using assay feasibility and explicit scientific risk."""
    available_control_set = set(available_controls)
    entries: list[TargetedTransitionReviewEntry] = []

    for candidate in candidates:
        risk_assessment = assess_assay_risk(
            assay_id=assay_id,
            peptide_uniqueness_score=candidate.peptide_uniqueness_score,
            localization_probability=candidate.localization_probability,
            quant_reproducibility_score=candidate.quant_reproducibility_score,
            assay_feasibility_score=candidate.assay_feasibility_score,
            predicted_failure_risk=candidate.predicted_failure_risk,
        )
        missing_controls = tuple(
            sorted(
                control
                for control in candidate.required_controls
                if control not in available_control_set
            )
        )
        reasons: list[str] = []
        if missing_controls:
            reasons.append(
                "missing required controls: " + ", ".join(missing_controls)
            )
        if not risk_assessment.supported_for_follow_up:
            reasons.append(
                f"assay risk score {risk_assessment.overall_risk_score:.2f} is too high for confident transition approval"
            )
        elif risk_assessment.overall_risk_score >= 0.3:
            reasons.append(
                f"assay risk score {risk_assessment.overall_risk_score:.2f} keeps the transition exploratory"
            )
        if candidate.assay_feasibility_score < 0.65:
            reasons.append("assay feasibility is too weak for direct targeted handoff")

        if (
            not missing_controls
            and risk_assessment.supported_for_follow_up
            and candidate.assay_feasibility_score >= 0.75
        ):
            disposition = TransitionReviewDisposition.APPROVED
            reasons.append("transition is feasible enough for targeted follow-up")
        elif (
            candidate.assay_feasibility_score >= 0.55
            and risk_assessment.overall_risk_score < 0.6
        ):
            disposition = TransitionReviewDisposition.EXPLORATORY
            reasons.append("transition may be used only as exploratory follow-up")
        else:
            disposition = TransitionReviewDisposition.REFUSED
            reasons.append("transition is not responsible to schedule as written")

        entries.append(
            TargetedTransitionReviewEntry(
                transition_id=candidate.transition_id,
                disposition=disposition,
                risk_assessment=risk_assessment,
                missing_controls=missing_controls,
                reasons=tuple(reasons),
            )
        )

    approved_transition_ids = tuple(
        entry.transition_id
        for entry in entries
        if entry.disposition is TransitionReviewDisposition.APPROVED
    )
    exploratory_transition_ids = tuple(
        entry.transition_id
        for entry in entries
        if entry.disposition is TransitionReviewDisposition.EXPLORATORY
    )
    refused_transition_ids = tuple(
        entry.transition_id
        for entry in entries
        if entry.disposition is TransitionReviewDisposition.REFUSED
    )
    readiness_score = (
        round(
            max(
                0.0,
                min(
                    (
                        (len(approved_transition_ids) / max(len(entries), 1)) * 0.75
                        + (len(exploratory_transition_ids) / max(len(entries), 1)) * 0.25
                    ),
                    1.0,
                ),
            ),
            4,
        )
        if entries
        else 0.0
    )
    notes = (
        ("targeted transition review is ready for handoff",)
        if approved_transition_ids
        else ("no transition is currently ready for responsible targeted handoff",)
    )
    return TargetedTransitionReview(
        assay_id=assay_id,
        approved_transition_ids=approved_transition_ids,
        exploratory_transition_ids=exploratory_transition_ids,
        refused_transition_ids=refused_transition_ids,
        readiness_score=readiness_score,
        entries=tuple(entries),
        notes=notes,
    )


def build_handoff_explanation(
    *,
    candidate_id: str,
    handoff_validation: CandidateHandoffValidation,
    transition_review: TargetedTransitionReview,
    review_packet: ReviewPacket,
    executable_plan: ExecutableAssayPlan,
) -> HandoffExplanation:
    """Summarize what a lab handoff can support, explore, or must block."""
    supported: list[HandoffSupportStatement] = []
    exploratory: list[HandoffSupportStatement] = []
    blocked: list[HandoffSupportStatement] = []

    if handoff_validation.accepted:
        supported.append(
            HandoffSupportStatement(
                level=HandoffSupportLevel.SUPPORTED,
                summary="candidate handoff passed operational validation",
                evidence_refs=tuple(sorted(handoff_validation.accepted_assay_ids)),
            )
        )
    if transition_review.approved_transition_ids:
        supported.append(
            HandoffSupportStatement(
                level=HandoffSupportLevel.SUPPORTED,
                summary="targeted transitions are ready for responsible follow-up",
                evidence_refs=transition_review.approved_transition_ids,
            )
        )
    if review_packet.advancement_evidence.evidence_ids:
        supported.append(
            HandoffSupportStatement(
                level=HandoffSupportLevel.SUPPORTED,
                summary="review packet contains linked evidence for the requested follow-up",
                evidence_refs=tuple(sorted(review_packet.advancement_evidence.evidence_ids)),
            )
        )

    for transition_id in transition_review.exploratory_transition_ids:
        exploratory.append(
            HandoffSupportStatement(
                level=HandoffSupportLevel.EXPLORATORY,
                summary=f"transition {transition_id} remains exploratory rather than execution-grade",
                evidence_refs=(transition_id,),
            )
        )
    for note in handoff_validation.skepticism_notes:
        exploratory.append(
            HandoffSupportStatement(
                level=HandoffSupportLevel.EXPLORATORY,
                summary=note,
            )
        )

    for blocker in handoff_validation.blockers:
        blocked.append(
            HandoffSupportStatement(
                level=HandoffSupportLevel.BLOCKED,
                summary=blocker,
                evidence_refs=tuple(sorted(handoff_validation.accepted_assay_ids)),
            )
        )
    for transition_id in transition_review.refused_transition_ids:
        blocked.append(
            HandoffSupportStatement(
                level=HandoffSupportLevel.BLOCKED,
                summary=f"transition {transition_id} is not responsible to schedule",
                evidence_refs=(transition_id,),
            )
        )
    for blocker in executable_plan.blocked_by:
        blocked.append(
            HandoffSupportStatement(
                level=HandoffSupportLevel.BLOCKED,
                summary=blocker,
                evidence_refs=(executable_plan.batch_id,),
            )
        )
    for blocker in review_packet.blocking_findings:
        blocked.append(
            HandoffSupportStatement(
                level=HandoffSupportLevel.BLOCKED,
                summary=blocker,
            )
        )

    if blocked:
        summary = "handoff remains blocked until weak science or operational blockers are resolved"
    elif exploratory:
        summary = "handoff is partly supported but still contains exploratory follow-up elements"
    else:
        summary = "handoff is supported for responsible lab follow-up"

    return HandoffExplanation(
        candidate_id=candidate_id,
        supported=tuple(supported),
        exploratory=tuple(exploratory),
        blocked=tuple(blocked),
        summary=summary,
    )


def refuse_irresponsible_assay_handoff(
    *,
    candidate_id: str,
    handoff_validation: CandidateHandoffValidation,
    transition_review: TargetedTransitionReview,
    review_packet: ReviewPacket,
    executable_plan: ExecutableAssayPlan,
) -> LabExecutionRefusal | None:
    """Build an explicit refusal when a suggested assay handoff is not responsible."""
    explanation = build_handoff_explanation(
        candidate_id=candidate_id,
        handoff_validation=handoff_validation,
        transition_review=transition_review,
        review_packet=review_packet,
        executable_plan=executable_plan,
    )
    blocked_assay_ids = tuple(
        sorted(
            {
                *handoff_validation.accepted_assay_ids,
                *[instruction.assay_id for instruction in executable_plan.instructions],
            }
        )
    )
    should_refuse = (
        not handoff_validation.accepted
        or bool(transition_review.refused_transition_ids)
        or bool(executable_plan.blocked_by)
        or not executable_plan.ready_for_execution
    )
    if not should_refuse:
        return None
    refusal = OperationRefusal(
        operation="lab_execution_handoff",
        kind=(
            RefusalKind.UNSAFE
            if handoff_validation.blockers or executable_plan.blocked_by
            else RefusalKind.AMBIGUOUS
        ),
        code="irresponsible_assay_handoff",
        reason="lab handoff is not responsible to run as written",
        reason_details=tuple(statement.summary for statement in explanation.blocked),
        recommended_actions=tuple(handoff_validation.required_next_actions),
    )
    return LabExecutionRefusal(
        candidate_id=candidate_id,
        blocked_assay_ids=blocked_assay_ids,
        explanation=explanation,
        result=OperationResult.refused(
            operation="lab_execution_handoff",
            summary="lab handoff refused until scientific and operational blockers are cleared",
            refusal=refusal,
        ),
    )


__all__ = [
    "HandoffExplanation",
    "HandoffSupportLevel",
    "HandoffSupportStatement",
    "LabExecutionRefusal",
    "TargetedTransitionCandidate",
    "TargetedTransitionReview",
    "TargetedTransitionReviewEntry",
    "TransitionReviewDisposition",
    "build_handoff_explanation",
    "refuse_irresponsible_assay_handoff",
    "review_targeted_transition_candidates",
]
