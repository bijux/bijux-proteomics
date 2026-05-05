# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Explanation and refusal owners for targeted lab handoffs."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import AssayId, JsonModel
from bijux_proteomics_foundation.refusals import OperationRefusal, RefusalKind
from bijux_proteomics_foundation.results import OperationResult
from bijux_proteomics_lab.lifecycle import CandidateHandoffValidation
from bijux_proteomics_lab.planning import ExecutableAssayPlan, ReviewPacket

from .transitions import TargetedTransitionReview


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
    operational_consequences: tuple[str, ...] = Field(default_factory=tuple)
    result: OperationResult


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
                evidence_refs=tuple(
                    sorted(review_packet.advancement_evidence.evidence_ids)
                ),
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
    operational_consequences = tuple(
        sorted(
            {
                "candidate remains out of the executable follow-up queue",
                "lab scheduling must stop before irreversible spend",
                *(
                    ["review packet must be reopened before a new handoff is proposed"]
                    if review_packet.blocking_findings
                    else []
                ),
                *(
                    ["batch stays unavailable for execution scheduling"]
                    if executable_plan.blocked_by or not executable_plan.ready_for_execution
                    else []
                ),
            }
        )
    )
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
        operational_consequences=operational_consequences,
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
    "build_handoff_explanation",
    "refuse_irresponsible_assay_handoff",
]
