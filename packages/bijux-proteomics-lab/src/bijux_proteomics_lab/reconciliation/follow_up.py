# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Planned-versus-observed reconciliation for operational follow-up loops."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import BatchId, JsonModel, ProgramId
from bijux_proteomics_lab.handoffs.explanations import (
    HandoffExplanation,
    LabExecutionRefusal,
    build_handoff_explanation,
    refuse_irresponsible_assay_handoff,
)
from bijux_proteomics_lab.handoffs.transitions import TargetedTransitionReview
from bijux_proteomics_lab.lifecycle import CandidateHandoffValidation
from bijux_proteomics_lab.outcomes import (
    AssayOutcome,
    AssayResultState,
    BatchClaimBeliefUpdate,
    BatchEvidencePromotionReport,
    BatchRerunPlan,
    ExperimentOutcome,
    build_batch_rerun_plan,
    consolidate_claim_belief_updates,
    promote_batch_outcome_to_evidence,
)
from bijux_proteomics_lab.planning import (
    ExecutableAssayPlan,
    LabExecutionRequest,
    ReviewPacket,
    build_lab_execution_request,
)


class PlannedObservedAssayDelta(JsonModel):
    """Difference between planned execution intent and observed assay outcome."""

    model_config = ConfigDict(extra="forbid")

    assay_id: str = Field(..., min_length=1)
    requested: bool = Field(..., description="Whether the assay was requested.")
    observed: bool = Field(..., description="Whether the assay produced an outcome.")
    result_state: str | None = Field(default=None, min_length=1)
    supports_progression: bool = False
    execution_gap: str = Field(..., min_length=1)
    notes: tuple[str, ...] = Field(default_factory=tuple)


class IntelligenceFeedbackSignal(JsonModel):
    """Lab-owned feedback payload that intelligence can consume without ownership confusion."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    program_id: ProgramId = Field(..., description="Program identifier.")
    supported_assay_ids: tuple[str, ...] = Field(default_factory=tuple)
    weakened_assay_ids: tuple[str, ...] = Field(default_factory=tuple)
    blocked_assay_ids: tuple[str, ...] = Field(default_factory=tuple)
    promoted_evidence_ids: tuple[str, ...] = Field(default_factory=tuple)
    recommended_action: str = Field(..., min_length=1)
    notes: tuple[str, ...] = Field(default_factory=tuple)


class IntelligenceFeedbackBaseline(JsonModel):
    """Baseline prioritization state preserved from historical decisions."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    baseline_score: float = Field(..., ge=0.0, le=1.0)
    historical_snapshot_id: str = Field(..., min_length=1)


class LabObservedOutcomeSignal(JsonModel):
    """Observed lab outcome signal used to adjust future prioritization."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    outcome_strength: float = Field(..., ge=-1.0, le=1.0)
    evidence_quality: float = Field(..., ge=0.0, le=1.0)


class IntelligenceFeedbackAdjustment(JsonModel):
    """Adjusted score for future prioritization while retaining historical snapshots."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    historical_snapshot_id: str = Field(..., min_length=1)
    baseline_score: float = Field(..., ge=0.0, le=1.0)
    adjusted_score: float = Field(..., ge=0.0, le=1.0)
    preserves_history: bool


class IntelligenceFeedbackReport(JsonModel):
    """Feedback report from lab outcomes into future prioritization."""

    model_config = ConfigDict(extra="forbid")

    adjustments: tuple[IntelligenceFeedbackAdjustment, ...] = Field(
        default_factory=tuple
    )


class OutcomeReconciliationReport(JsonModel):
    """Reconciliation of execution intent, observed outcomes, and feedback posture."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    program_id: ProgramId = Field(..., description="Program identifier.")
    batch_id: BatchId = Field(..., description="Batch identifier.")
    assay_deltas: tuple[PlannedObservedAssayDelta, ...] = Field(default_factory=tuple)
    promotion_report: BatchEvidencePromotionReport
    claim_belief_update: BatchClaimBeliefUpdate
    rerun_plan: BatchRerunPlan
    ready_for_feedback: bool = Field(
        ...,
        description="Whether the reconciliation is specific enough for downstream feedback.",
    )
    intelligence_feedback: IntelligenceFeedbackSignal
    notes: tuple[str, ...] = Field(default_factory=tuple)


class OperationalFollowUpPath(JsonModel):
    """Full operational path from candidate handoff to observed outcome reconciliation."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    program_id: ProgramId = Field(..., description="Program identifier.")
    execution_request: LabExecutionRequest
    handoff_validation: CandidateHandoffValidation
    transition_review: TargetedTransitionReview
    explanation: HandoffExplanation
    refusal: LabExecutionRefusal | None = None
    reconciliation: OutcomeReconciliationReport
    notes: tuple[str, ...] = Field(default_factory=tuple)


def reconcile_planned_and_observed_outcome(
    *,
    candidate_id: str,
    execution_request: LabExecutionRequest,
    outcome: ExperimentOutcome,
    target_id: str,
    claim_links: dict[str, list[str]] | None = None,
) -> OutcomeReconciliationReport:
    """Reconcile requested assay work against observed outcomes and feedback posture."""
    claim_links = claim_links or {}
    outcome_by_assay = {assay.assay_id: assay for assay in outcome.assay_outcomes}
    requested_assay_ids = set(execution_request.requested_assay_ids)
    observed_assay_ids = set(outcome_by_assay)
    ordered_assay_ids = sorted(requested_assay_ids | observed_assay_ids)

    deltas: list[PlannedObservedAssayDelta] = []
    supported_assay_ids: list[str] = []
    weakened_assay_ids: list[str] = []
    blocked_assay_ids: list[str] = []
    for assay_id in ordered_assay_ids:
        observed_outcome: AssayOutcome | None = outcome_by_assay.get(assay_id)
        requested = assay_id in requested_assay_ids
        observed = observed_outcome is not None
        if requested and not observed:
            execution_gap = "requested assay did not produce an observed outcome"
            blocked_assay_ids.append(assay_id)
            notes = ("follow-up remains blocked until the missing assay is observed",)
        elif observed_outcome is None:
            execution_gap = "unexpected assay is absent from the execution request"
            blocked_assay_ids.append(assay_id)
            notes = ("review unexpected lineage before using the assay operationally",)
        elif observed_outcome.result_state is AssayResultState.PASSED:
            execution_gap = "planned assay produced a progression-supporting outcome"
            supported_assay_ids.append(assay_id)
            notes = ("assay outcome can reinforce downstream follow-up reasoning",)
        elif observed_outcome.result_state is AssayResultState.FAILED_BIOLOGICAL:
            execution_gap = "planned assay weakened the progression hypothesis"
            weakened_assay_ids.append(assay_id)
            notes = ("biological miss should feed back into candidate review",)
        else:
            execution_gap = (
                "planned assay stayed blocked by technical or interpretive failure"
            )
            blocked_assay_ids.append(assay_id)
            notes = (
                "rerun or escalation is required before strong feedback is emitted",
            )
        deltas.append(
            PlannedObservedAssayDelta(
                assay_id=assay_id,
                requested=requested,
                observed=observed,
                result_state=observed_outcome.result_state.value
                if observed_outcome is not None
                else None,
                supports_progression=(
                    observed_outcome is not None
                    and observed_outcome.result_state is AssayResultState.PASSED
                ),
                execution_gap=execution_gap,
                notes=notes,
            )
        )

    promoted_payloads, promotion_report = promote_batch_outcome_to_evidence(
        outcome,
        target_id=target_id,
    )
    claim_belief_update = consolidate_claim_belief_updates(
        outcome,
        claim_links=claim_links,
    )
    rerun_plan = build_batch_rerun_plan(outcome)
    promoted_evidence_ids = tuple(payload.evidence_id for payload in promoted_payloads)
    ready_for_feedback = bool(deltas) and not any(
        delta.execution_gap == "unexpected assay is absent from the execution request"
        for delta in deltas
    )

    if blocked_assay_ids:
        recommended_action = (
            "hold downstream confidence until blocked assay issues are resolved"
        )
    elif weakened_assay_ids:
        recommended_action = (
            "send weakening feedback into candidate review before further spend"
        )
    else:
        recommended_action = "send supporting feedback into downstream follow-up review"

    intelligence_feedback = IntelligenceFeedbackSignal(
        candidate_id=candidate_id,
        program_id=execution_request.program_id,
        supported_assay_ids=tuple(sorted(supported_assay_ids)),
        weakened_assay_ids=tuple(sorted(weakened_assay_ids)),
        blocked_assay_ids=tuple(sorted(blocked_assay_ids)),
        promoted_evidence_ids=promoted_evidence_ids,
        recommended_action=recommended_action,
        notes=tuple(sorted(set(execution_request.unresolved_risks))),
    )
    notes = (
        ("reconciliation is ready for downstream analytical feedback",)
        if ready_for_feedback
        else ("reconciliation still needs lineage cleanup before downstream use",)
    )

    return OutcomeReconciliationReport(
        candidate_id=candidate_id,
        program_id=execution_request.program_id,
        batch_id=outcome.batch_id,
        assay_deltas=tuple(deltas),
        promotion_report=promotion_report,
        claim_belief_update=claim_belief_update,
        rerun_plan=rerun_plan,
        ready_for_feedback=ready_for_feedback,
        intelligence_feedback=intelligence_feedback,
        notes=notes,
    )


def apply_lab_feedback_to_intelligence_prioritization(
    *,
    baselines: tuple[IntelligenceFeedbackBaseline, ...],
    outcomes: tuple[LabObservedOutcomeSignal, ...],
) -> IntelligenceFeedbackReport:
    """Apply lab outcomes to future prioritization without rewriting historical snapshots."""

    outcomes_by_candidate = {outcome.candidate_id: outcome for outcome in outcomes}
    adjustments: list[IntelligenceFeedbackAdjustment] = []
    for baseline in baselines:
        outcome = outcomes_by_candidate.get(baseline.candidate_id)
        if outcome is None:
            adjusted = baseline.baseline_score
        else:
            delta = 0.2 * outcome.outcome_strength * outcome.evidence_quality
            adjusted = max(0.0, min(1.0, baseline.baseline_score + delta))

        adjustments.append(
            IntelligenceFeedbackAdjustment(
                candidate_id=baseline.candidate_id,
                historical_snapshot_id=baseline.historical_snapshot_id,
                baseline_score=baseline.baseline_score,
                adjusted_score=adjusted,
                preserves_history=True,
            )
        )

    adjustments.sort(key=lambda item: item.candidate_id)
    return IntelligenceFeedbackReport(adjustments=tuple(adjustments))


def build_operational_follow_up_path(
    *,
    candidate_id: str,
    handoff_validation: CandidateHandoffValidation,
    transition_review: TargetedTransitionReview,
    review_packet: ReviewPacket,
    executable_plan: ExecutableAssayPlan,
    outcome: ExperimentOutcome,
    target_id: str,
    claim_links: dict[str, list[str]] | None = None,
) -> OperationalFollowUpPath:
    """Build one full path from candidate handoff through observed outcome feedback."""
    execution_request = build_lab_execution_request(review_packet, executable_plan)
    explanation = build_handoff_explanation(
        candidate_id=candidate_id,
        handoff_validation=handoff_validation,
        transition_review=transition_review,
        review_packet=review_packet,
        executable_plan=executable_plan,
    )
    refusal = refuse_irresponsible_assay_handoff(
        candidate_id=candidate_id,
        handoff_validation=handoff_validation,
        transition_review=transition_review,
        review_packet=review_packet,
        executable_plan=executable_plan,
    )
    reconciliation = reconcile_planned_and_observed_outcome(
        candidate_id=candidate_id,
        execution_request=execution_request,
        outcome=outcome,
        target_id=target_id,
        claim_links=claim_links,
    )
    notes = (
        (
            "handoff remains refused but the observed batch still produced reviewable reconciliation",
        )
        if refusal is not None
        else (
            "handoff and observed outcome form a complete operational follow-up path",
        )
    )
    return OperationalFollowUpPath(
        candidate_id=candidate_id,
        program_id=execution_request.program_id,
        execution_request=execution_request,
        handoff_validation=handoff_validation,
        transition_review=transition_review,
        explanation=explanation,
        refusal=refusal,
        reconciliation=reconciliation,
        notes=notes,
    )


__all__ = [
    "IntelligenceFeedbackAdjustment",
    "IntelligenceFeedbackBaseline",
    "IntelligenceFeedbackReport",
    "IntelligenceFeedbackSignal",
    "LabObservedOutcomeSignal",
    "OperationalFollowUpPath",
    "OutcomeReconciliationReport",
    "PlannedObservedAssayDelta",
    "apply_lab_feedback_to_intelligence_prioritization",
    "build_operational_follow_up_path",
    "reconcile_planned_and_observed_outcome",
]
