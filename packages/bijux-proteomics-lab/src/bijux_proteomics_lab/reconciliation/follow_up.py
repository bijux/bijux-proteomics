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
    ClosedLoopPlan,
    ExecutableAssayPlan,
    LabExecutionRequest,
    ProgressDecision,
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
    belief_update_summary: tuple[str, ...] = Field(default_factory=tuple)
    operational_follow_through: tuple[str, ...] = Field(default_factory=tuple)
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
    next_cycle_packet: ClosedLoopPlan
    belief_posture: str = Field(..., min_length=1)
    belief_update_summary: tuple[str, ...] = Field(default_factory=tuple)
    operational_follow_through: tuple[str, ...] = Field(default_factory=tuple)
    operator_actions: tuple["OperatorFollowThroughAction", ...] = Field(
        default_factory=tuple
    )
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


class OperatorFollowThroughAction(JsonModel):
    """Structured operator action tied to a scientifically meaningful outcome."""

    model_config = ConfigDict(extra="forbid")

    assay_id: str | None = Field(default=None, min_length=1)
    action: str = Field(..., min_length=1)
    scientific_reason: str = Field(..., min_length=1)
    required_before_progression: bool = Field(
        ..., description="Whether progression should stop until the action is complete."
    )


def _belief_posture(
    *,
    claim_belief_update: BatchClaimBeliefUpdate,
    blocked_assay_ids: list[str],
) -> tuple[str, tuple[str, ...]]:
    reinforcing_claim_ids = sorted(
        update.claim_id for update in claim_belief_update.updates if update.delta > 0
    )
    weakening_claim_ids = sorted(
        update.claim_id for update in claim_belief_update.updates if update.delta < 0
    )
    if blocked_assay_ids:
        posture = "blocked"
    elif reinforcing_claim_ids and weakening_claim_ids:
        posture = "mixed"
    elif weakening_claim_ids:
        posture = "weakening"
    elif reinforcing_claim_ids:
        posture = "reinforcing"
    else:
        posture = "neutral"

    summary: list[str] = []
    if reinforcing_claim_ids:
        summary.append("reinforcing claims: " + ", ".join(reinforcing_claim_ids))
    if weakening_claim_ids:
        summary.append("weakening claims: " + ", ".join(weakening_claim_ids))
    if not summary:
        summary.append("no claim-linked belief deltas were emitted")
    return posture, tuple(summary)


def _operator_follow_through_actions(
    *,
    deltas: tuple[PlannedObservedAssayDelta, ...],
    promotion_report: BatchEvidencePromotionReport,
    rerun_plan: BatchRerunPlan,
    blocked_assay_ids: list[str],
    weakened_assay_ids: list[str],
) -> tuple[OperatorFollowThroughAction, ...]:
    rows: list[OperatorFollowThroughAction] = []
    for assay_id in sorted(promotion_report.promoted_assay_ids):
        rows.append(
            OperatorFollowThroughAction(
                assay_id=assay_id,
                action="promote-evidence",
                scientific_reason=(
                    "observed assay passed strongly enough to support downstream evidence promotion"
                ),
                required_before_progression=False,
            )
        )
    for delta in deltas:
        if delta.assay_id in blocked_assay_ids:
            rows.append(
                OperatorFollowThroughAction(
                    assay_id=delta.assay_id,
                    action="resolve-blocked-assay",
                    scientific_reason=delta.execution_gap,
                    required_before_progression=True,
                )
            )
        elif delta.assay_id in weakened_assay_ids:
            rows.append(
                OperatorFollowThroughAction(
                    assay_id=delta.assay_id,
                    action="return-to-candidate-review",
                    scientific_reason=delta.execution_gap,
                    required_before_progression=True,
                )
            )
    for rerun_action in rerun_plan.actions:
        rows.append(
            OperatorFollowThroughAction(
                assay_id=rerun_action.assay_id,
                action=rerun_action.action,
                scientific_reason=rerun_action.rationale,
                required_before_progression=True,
            )
        )
    if not rows:
        rows.append(
            OperatorFollowThroughAction(
                assay_id=None,
                action="carry-supporting-outcomes-forward",
                scientific_reason=(
                    "all observed outcomes support progression without unresolved assay drift"
                ),
                required_before_progression=False,
            )
        )
    deduped: list[OperatorFollowThroughAction] = []
    seen: set[tuple[str | None, str, str, bool]] = set()
    for row in rows:
        key = (
            row.assay_id,
            row.action,
            row.scientific_reason,
            row.required_before_progression,
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return tuple(deduped)


def _operational_follow_through(
    actions: tuple[OperatorFollowThroughAction, ...],
) -> tuple[str, ...]:
    summaries = [
        (
            f"{action.action}: {action.assay_id}"
            if action.assay_id is not None
            else action.action
        )
        for action in actions
    ]
    return tuple(dict.fromkeys(summaries))


def _build_next_cycle_packet(
    *,
    execution_request: LabExecutionRequest,
    blocked_assay_ids: list[str],
    weakened_assay_ids: list[str],
    supported_assay_ids: list[str],
    operator_actions: tuple[OperatorFollowThroughAction, ...],
) -> ClosedLoopPlan:
    evidence_backlog = list(dict.fromkeys(execution_request.unresolved_risks))
    notes: list[str] = []
    if blocked_assay_ids:
        decision = ProgressDecision.HOLD
        assay_backlog = sorted(blocked_assay_ids)
        notes.append("requested follow-up remained operationally blocked after execution reconciliation")
    elif weakened_assay_ids:
        decision = ProgressDecision.REDESIGN
        assay_backlog = sorted(weakened_assay_ids)
        notes.append("observed biological outcomes weakened the progression hypothesis")
    elif evidence_backlog:
        decision = ProgressDecision.HOLD
        assay_backlog = []
        notes.append("supporting assays landed, but unresolved scientific risks still block progression")
    else:
        decision = ProgressDecision.ADVANCE
        assay_backlog = []
        notes.append("requested follow-up produced progression-supporting outcomes without unresolved drift")
    if supported_assay_ids:
        notes.append(
            "progression-supporting assays: " + ", ".join(sorted(supported_assay_ids))
        )
    notes.extend(
        action.scientific_reason
        for action in operator_actions
        if action.required_before_progression
    )
    return ClosedLoopPlan(
        program_id=execution_request.program_id,
        decision=decision,
        evidence_backlog=evidence_backlog,
        assay_backlog=assay_backlog,
        notes=list(dict.fromkeys(notes)),
        evidence_trust_score=0.0,
        promotion_ready_count=len(supported_assay_ids),
        technical_failure_count=len(blocked_assay_ids),
    )


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
    belief_posture, belief_update_summary = _belief_posture(
        claim_belief_update=claim_belief_update,
        blocked_assay_ids=blocked_assay_ids,
    )
    operator_actions = _operator_follow_through_actions(
        deltas=tuple(deltas),
        promotion_report=promotion_report,
        rerun_plan=rerun_plan,
        blocked_assay_ids=blocked_assay_ids,
        weakened_assay_ids=weakened_assay_ids,
    )
    operational_follow_through = _operational_follow_through(operator_actions)
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
    next_cycle_packet = _build_next_cycle_packet(
        execution_request=execution_request,
        blocked_assay_ids=blocked_assay_ids,
        weakened_assay_ids=weakened_assay_ids,
        supported_assay_ids=supported_assay_ids,
        operator_actions=operator_actions,
    )

    intelligence_feedback = IntelligenceFeedbackSignal(
        candidate_id=candidate_id,
        program_id=execution_request.program_id,
        supported_assay_ids=tuple(sorted(supported_assay_ids)),
        weakened_assay_ids=tuple(sorted(weakened_assay_ids)),
        blocked_assay_ids=tuple(sorted(blocked_assay_ids)),
        promoted_evidence_ids=promoted_evidence_ids,
        recommended_action=recommended_action,
        belief_update_summary=belief_update_summary,
        operational_follow_through=operational_follow_through,
        notes=tuple(sorted(set(execution_request.unresolved_risks))),
    )
    notes = (
        (
            f"reconciliation is ready for downstream analytical feedback with {belief_posture} belief posture",
        )
        if ready_for_feedback
        else (
            f"reconciliation still needs lineage cleanup before downstream use and remains {belief_posture}",
        )
    )

    return OutcomeReconciliationReport(
        candidate_id=candidate_id,
        program_id=execution_request.program_id,
        batch_id=outcome.batch_id,
        assay_deltas=tuple(deltas),
        promotion_report=promotion_report,
        claim_belief_update=claim_belief_update,
        rerun_plan=rerun_plan,
        next_cycle_packet=next_cycle_packet,
        belief_posture=belief_posture,
        belief_update_summary=belief_update_summary,
        operational_follow_through=operational_follow_through,
        operator_actions=operator_actions,
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
    "OperatorFollowThroughAction",
    "OperationalFollowUpPath",
    "OutcomeReconciliationReport",
    "PlannedObservedAssayDelta",
    "apply_lab_feedback_to_intelligence_prioritization",
    "build_operational_follow_up_path",
    "reconcile_planned_and_observed_outcome",
]
