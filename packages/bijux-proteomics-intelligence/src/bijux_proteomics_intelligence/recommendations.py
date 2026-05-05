# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Recommendation, escalation, and uncertainty owners for intelligence outputs."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_foundation.results import OperationResult
from bijux_proteomics_intelligence.evaluators import (
    HypothesisStatus,
    ScenarioAction,
    ScenarioEvaluation,
    ScenarioSetEvaluation,
    summarize_hold_pressure,
    summarize_scenario_confidence_spread,
    summarize_scenario_consensus,
)
from bijux_proteomics_intelligence.evidence_posture import (
    assess_recommendation_readiness,
)
from bijux_proteomics_knowledge.evidence import EvidenceBundle
from bijux_proteomics_knowledge.references.benchmarks import KnowledgeWorkflowFamily


class DecisionEscalationFlags(JsonModel):
    """Escalation flags indicating when human arbitration should be mandatory."""

    model_config = ConfigDict(extra="forbid")

    conflicting_actions: bool = Field(..., description="Scenario actions conflict.")
    high_hold_pressure: bool = Field(..., description="Hold pressure is high.")
    wide_confidence_spread: bool = Field(
        ..., description="Confidence spread exceeds threshold."
    )
    escalate_to_human_review: bool = Field(
        ..., description="Overall escalation recommendation."
    )


class FinalDecisionRecommendation(JsonModel):
    """Final intelligence recommendation combining consensus and escalation."""

    model_config = ConfigDict(extra="forbid")

    action: ScenarioAction = Field(..., description="Recommended final action.")
    requires_human_review: bool = Field(
        ..., description="Whether human arbitration is required."
    )
    gate_result: OperationResult | None = Field(
        default=None,
        description="Optional machine-readable refusal or degraded-success gate result.",
    )
    reasons: list[str] = Field(
        default_factory=list, description="Reasons supporting the final recommendation."
    )


class UnresolvedQuestionLedger(JsonModel):
    """Deduplicated unresolved question ledger across scenario outputs."""

    model_config = ConfigDict(extra="forbid")

    question_counts: dict[str, int] = Field(
        default_factory=dict,
        description="Count of unresolved question occurrences across scenarios.",
    )
    prioritized_questions: list[str] = Field(
        default_factory=list,
        description="Questions sorted by frequency and then lexicographic order.",
    )


class ScenarioUncertaintyEntry(JsonModel):
    """Scenario-specific uncertainty that should remain visible to reviewers."""

    model_config = ConfigDict(extra="forbid")

    scenario: str = Field(..., min_length=1)
    action: ScenarioAction
    confidence: float = Field(..., ge=0.0, le=1.0)
    hypothesis_status: HypothesisStatus
    unresolved_questions: list[str] = Field(default_factory=list)


class UncertaintyPreservingInterpretationSummary(JsonModel):
    """Summary that preserves scenario disagreement and unresolved questions."""

    model_config = ConfigDict(extra="forbid")

    consensus_action: ScenarioAction = Field(...)
    conflicting_actions: bool = Field(...)
    confidence_spread: float = Field(..., ge=0.0, le=1.0)
    unresolved_question_count: int = Field(default=0, ge=0)
    scenario_entries: list[ScenarioUncertaintyEntry] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class IntelligenceOutputMode(StrEnum):
    """Governance mode for intelligence outputs."""

    ADVISORY = "advisory"
    ENFORCED = "enforced"


class IntelligenceDecisionSupportEnvelope(JsonModel):
    """Explicit boundary between advisory intelligence and enforced policy."""

    model_config = ConfigDict(extra="forbid")

    recommendation: FinalDecisionRecommendation = Field(...)
    mode: IntelligenceOutputMode = Field(default=IntelligenceOutputMode.ADVISORY)
    enforced_policy_id: str | None = Field(default=None)
    promoted_by: str | None = Field(default=None)
    promotion_rationale: str | None = Field(default=None)


def derive_decision_escalation_flags(
    evaluations: ScenarioSetEvaluation,
    *,
    hold_threshold: float = 0.5,
    confidence_spread_threshold: float = 0.25,
) -> DecisionEscalationFlags:
    """Derive escalation flags from scenario consensus, hold pressure, and confidence spread."""

    consensus = summarize_scenario_consensus(evaluations)
    hold_pressure = summarize_hold_pressure(evaluations, threshold=hold_threshold)
    spread = summarize_scenario_confidence_spread(evaluations)
    wide_spread = spread.spread >= confidence_spread_threshold
    escalate = (
        consensus.conflicting_actions or hold_pressure.high_hold_pressure or wide_spread
    )
    return DecisionEscalationFlags(
        conflicting_actions=consensus.conflicting_actions,
        high_hold_pressure=hold_pressure.high_hold_pressure,
        wide_confidence_spread=wide_spread,
        escalate_to_human_review=escalate,
    )


def build_final_decision_recommendation(
    evaluations: ScenarioSetEvaluation,
    *,
    evidence_bundle: EvidenceBundle | None = None,
    workflow_family: KnowledgeWorkflowFamily | None = None,
) -> FinalDecisionRecommendation:
    """Build final recommendation from scenario consensus and escalation signals."""

    consensus = summarize_scenario_consensus(evaluations)
    escalation = derive_decision_escalation_flags(evaluations)
    reasons = list(consensus.notes)
    if escalation.high_hold_pressure:
        reasons.append("hold pressure is high across scenario evaluations")
    if escalation.wide_confidence_spread:
        reasons.append("scenario confidence spread is wide")
    if escalation.conflicting_actions:
        reasons.append("scenario actions conflict")
    gate_result: OperationResult | None = None
    action = consensus.recommended_action
    requires_human_review = escalation.escalate_to_human_review
    if evidence_bundle is not None:
        gate_result = assess_recommendation_readiness(evidence_bundle)
        if gate_result.disposition.value == "refused":
            action = ScenarioAction.HOLD
            requires_human_review = True
            reasons.append(gate_result.summary)
            if gate_result.refusal is not None:
                reasons.extend(gate_result.refusal.reason_details)
        elif gate_result.disposition.value == "degraded_success":
            requires_human_review = True
            reasons.append(gate_result.summary)
            reasons.extend(gate_result.degradation_reasons)
    if workflow_family is not None:
        reasons.append(f"workflow_family={workflow_family.value}")
    return FinalDecisionRecommendation(
        action=action,
        requires_human_review=requires_human_review,
        gate_result=gate_result,
        reasons=reasons,
    )


def build_intelligence_decision_support_envelope(
    recommendation: FinalDecisionRecommendation,
) -> IntelligenceDecisionSupportEnvelope:
    """Wrap intelligence output as advisory decision support by default."""

    return IntelligenceDecisionSupportEnvelope(recommendation=recommendation)


def promote_intelligence_output_to_policy(
    envelope: IntelligenceDecisionSupportEnvelope,
    *,
    policy_id: str,
    promoted_by: str,
    rationale: str,
) -> IntelligenceDecisionSupportEnvelope:
    """Explicitly promote advisory intelligence output into enforced policy."""

    if envelope.mode is IntelligenceOutputMode.ENFORCED:
        raise ValueError("intelligence output is already enforced")
    return envelope.model_copy(
        update={
            "mode": IntelligenceOutputMode.ENFORCED,
            "enforced_policy_id": policy_id,
            "promoted_by": promoted_by,
            "promotion_rationale": rationale,
        }
    )


def summarize_unresolved_question_ledger(
    evaluations: ScenarioSetEvaluation,
) -> UnresolvedQuestionLedger:
    """Build deduplicated unresolved question ledger across scenarios."""

    questions = (
        evaluations.progression.unresolved_questions
        + evaluations.synthesis.unresolved_questions
        + evaluations.scale_up.unresolved_questions
        + evaluations.redesign.unresolved_questions
    )
    counts: dict[str, int] = {}
    for question in questions:
        cleaned = question.strip()
        if not cleaned:
            continue
        counts[cleaned] = counts.get(cleaned, 0) + 1
    prioritized = sorted(counts, key=lambda item: (-counts[item], item))
    return UnresolvedQuestionLedger(
        question_counts=counts,
        prioritized_questions=prioritized,
    )


def summarize_uncertainty_preserving_interpretation(
    evaluations: ScenarioSetEvaluation,
) -> UncertaintyPreservingInterpretationSummary:
    """Summarize scenario outputs without flattening disagreement away."""

    scenarios: list[ScenarioEvaluation] = [
        evaluations.progression,
        evaluations.synthesis,
        evaluations.scale_up,
        evaluations.redesign,
    ]
    consensus = summarize_scenario_consensus(evaluations)
    spread = summarize_scenario_confidence_spread(evaluations)
    entries = [
        ScenarioUncertaintyEntry(
            scenario=scenario.scenario,
            action=scenario.action,
            confidence=scenario.confidence,
            hypothesis_status=scenario.hypothesis_status,
            unresolved_questions=scenario.unresolved_questions,
        )
        for scenario in scenarios
    ]
    unresolved_questions = {
        question for scenario in scenarios for question in scenario.unresolved_questions
    }
    notes: list[str] = []
    if consensus.conflicting_actions:
        notes.append("scenario actions disagree and should remain visible to reviewers")
    if spread.spread >= 0.2:
        notes.append(
            "scenario confidence spread is wide enough to keep uncertainty explicit"
        )
    if unresolved_questions:
        notes.append(
            f"{len(unresolved_questions)} unresolved questions still influence the decision"
        )
    if not notes:
        notes.append(
            "scenario uncertainty is narrow enough for a stable advisory interpretation"
        )
    return UncertaintyPreservingInterpretationSummary(
        consensus_action=consensus.recommended_action,
        conflicting_actions=consensus.conflicting_actions,
        confidence_spread=spread.spread,
        unresolved_question_count=len(unresolved_questions),
        scenario_entries=entries,
        notes=notes,
    )
