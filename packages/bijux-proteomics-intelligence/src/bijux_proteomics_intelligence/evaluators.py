# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Scenario evaluators for progression decisions."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.programs import ProgramSpec
from bijux_proteomics_intelligence.briefs import CandidateAssessment, CandidateRanking
from bijux_proteomics_intelligence.candidates import CandidateRiskProfile
from bijux_proteomics_intelligence.serialization import JsonModel
from bijux_proteomics_knowledge import DecisionReadiness


class ScenarioAction(StrEnum):
    """High-level actions recommended by scenario evaluators."""

    ADVANCE = "advance"
    HOLD = "hold"
    REDESIGN = "redesign"
    SCALE_UP = "scale_up"


class HypothesisStatus(StrEnum):
    """Status of the active scientific hypothesis for decision guidance."""

    SUPPORTED = "supported"
    WEAKENED = "weakened"
    UNRESOLVED = "unresolved"


class ScenarioEvaluation(JsonModel):
    """Recommendation for a specific progression scenario."""

    model_config = ConfigDict(extra="forbid")

    scenario: str = Field(..., min_length=1, description="Scenario under evaluation.")
    action: ScenarioAction = Field(..., description="Recommended action.")
    reasons: list[str] = Field(
        default_factory=list,
        description="Short reasons for the recommendation.",
    )
    hypothesis_status: HypothesisStatus = Field(
        default=HypothesisStatus.UNRESOLVED,
        description="How the recommendation maps to current hypothesis confidence.",
    )
    key_discriminating_experiment: str | None = Field(
        default=None,
        description="Most informative next experiment for reducing uncertainty.",
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence in the recommendation quality.",
    )
    unresolved_questions: list[str] = Field(
        default_factory=list,
        description="Critical unresolved questions that still affect the scenario.",
    )


class ProgressionPolicy(JsonModel):
    """Policy that governs progression decisions."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(..., min_length=1, description="Stable policy identifier.")
    require_ranked_candidate: bool = Field(
        default=True,
        description="Whether progression requires at least one ranked candidate.",
    )
    maximum_blocker_findings_on_top_candidate: int = Field(
        default=2,
        ge=0,
        description="Maximum blocker findings allowed on the top candidate before holding progression.",
    )
    minimum_top_candidate_confidence: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum confidence required on top candidate explainability for progression.",
    )


class SynthesisPolicy(JsonModel):
    """Policy that governs synthesis decisions."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(..., min_length=1, description="Stable policy identifier.")
    maximum_residual_risk: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Maximum acceptable residual risk for synthesis.",
    )
    maximum_blocker_findings_on_top_candidate: int = Field(
        default=2,
        ge=0,
        description="Maximum blocker findings allowed on the top candidate before synthesis.",
    )
    minimum_top_candidate_confidence: float = Field(
        default=0.65,
        ge=0.0,
        le=1.0,
        description="Minimum top candidate confidence required before synthesis.",
    )
    maximum_safety_risk: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Maximum acceptable safety-specific risk for synthesis.",
    )


class ScaleUpPolicy(JsonModel):
    """Policy that governs scale-up decisions."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(..., min_length=1, description="Stable policy identifier.")
    minimum_decisive_records: int = Field(
        default=2,
        ge=1,
        description="Minimum decisive evidence count required for scale-up.",
    )
    maximum_residual_risk: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Maximum acceptable residual risk for scale-up.",
    )
    maximum_safety_risk: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="Maximum acceptable safety-specific risk for scale-up.",
    )


class RedesignPolicy(JsonModel):
    """Policy that governs redesign decisions."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(..., min_length=1, description="Stable policy identifier.")
    redesign_on_any_rejection: bool = Field(
        default=True,
        description="Whether any rejection should trigger redesign consideration.",
    )


class EvaluatorPolicyBundle(JsonModel):
    """Bundle of scenario policies applied together."""

    model_config = ConfigDict(extra="forbid")

    progression: ProgressionPolicy = Field(
        default_factory=lambda: ProgressionPolicy(policy_id="progression-default"),
        description="Progression scenario policy.",
    )
    synthesis: SynthesisPolicy = Field(
        default_factory=lambda: SynthesisPolicy(policy_id="synthesis-default"),
        description="Synthesis scenario policy.",
    )
    scale_up: ScaleUpPolicy = Field(
        default_factory=lambda: ScaleUpPolicy(policy_id="scale-up-default"),
        description="Scale-up scenario policy.",
    )
    redesign: RedesignPolicy = Field(
        default_factory=lambda: RedesignPolicy(policy_id="redesign-default"),
        description="Redesign scenario policy.",
    )


class ScenarioSetEvaluation(JsonModel):
    """Grouped scenario evaluations for one program state."""

    model_config = ConfigDict(extra="forbid")

    progression: ScenarioEvaluation = Field(..., description="Progression evaluation.")
    synthesis: ScenarioEvaluation = Field(..., description="Synthesis evaluation.")
    scale_up: ScenarioEvaluation = Field(..., description="Scale-up evaluation.")
    redesign: ScenarioEvaluation = Field(..., description="Redesign evaluation.")


class PortfolioDecisionReport(JsonModel):
    """Portfolio-level quality report for ranked candidates."""

    model_config = ConfigDict(extra="forbid")

    candidate_count: int = Field(
        ..., ge=0, description="Number of ranked candidates evaluated."
    )
    liability_diversity: int = Field(
        ..., ge=0, description="Distinct liability blocker labels in top candidates."
    )
    mean_residual_risk: float = Field(
        ..., ge=0.0, le=1.0, description="Average residual risk across top candidates."
    )
    balanced_portfolio: bool = Field(
        ..., description="Whether the shortlist appears balanced for progression."
    )
    notes: list[str] = Field(
        default_factory=list, description="Short explanation of portfolio quality."
    )


class ScenarioDecisionConsensus(JsonModel):
    """Consensus summary across scenario evaluations."""

    model_config = ConfigDict(extra="forbid")

    recommended_action: ScenarioAction = Field(
        ..., description="Consensus recommended action."
    )
    action_counts: dict[str, int] = Field(
        default_factory=dict,
        description="Count of scenario actions by action label.",
    )
    conflicting_actions: bool = Field(
        ...,
        description="Whether scenario evaluations disagree on action direction.",
    )
    notes: list[str] = Field(default_factory=list, description="Short consensus notes.")


class IntelligenceReviewPacket(JsonModel):
    """Integrated intelligence packet for review-gate decision meetings."""

    model_config = ConfigDict(extra="forbid")

    consensus: ScenarioDecisionConsensus = Field(
        ...,
        description="Consensus across scenario evaluations.",
    )
    portfolio: PortfolioDecisionReport = Field(
        ...,
        description="Portfolio risk/diversity report for top candidates.",
    )
    review_ready: bool = Field(
        ...,
        description="Whether intelligence outputs are coherent enough for a progression review.",
    )
    notes: list[str] = Field(default_factory=list, description="Review-facing notes.")


class HoldPressureSummary(JsonModel):
    """Summary of hold pressure across scenario evaluations."""

    model_config = ConfigDict(extra="forbid")

    hold_count: int = Field(
        ..., ge=0, description="Number of scenario actions recommending hold."
    )
    total_scenarios: int = Field(
        ..., ge=1, description="Total scenario count considered."
    )
    hold_fraction: float = Field(
        ..., ge=0.0, le=1.0, description="Fraction of hold recommendations."
    )
    high_hold_pressure: bool = Field(
        ..., description="Whether hold pressure crosses escalation threshold."
    )


class ScenarioConfidenceSpread(JsonModel):
    """Spread of scenario confidences for review consistency checks."""

    model_config = ConfigDict(extra="forbid")

    minimum_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Minimum confidence among scenarios."
    )
    maximum_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Maximum confidence among scenarios."
    )
    mean_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Mean confidence across scenarios."
    )
    spread: float = Field(
        ..., ge=0.0, le=1.0, description="Difference between max and min confidence."
    )


class AssessmentMetricCoverageReport(JsonModel):
    """Coverage report for required metrics across candidate assessments."""

    model_config = ConfigDict(extra="forbid")

    required_metrics: list[str] = Field(
        default_factory=list, description="Required metrics for evaluation."
    )
    covered_metrics: list[str] = Field(
        default_factory=list, description="Metrics present in assessments."
    )
    missing_metrics: list[str] = Field(
        default_factory=list, description="Required metrics missing in assessments."
    )
    coverage_ratio: float = Field(
        ..., ge=0.0, le=1.0, description="Fraction of required metrics covered."
    )
    liability_diversity: int = Field(
        default=0,
        ge=0,
        description="Count of unique liability labels across evaluated candidates.",
    )
    mean_residual_risk: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Residual risk estimate derived from metric coverage and liabilities.",
    )


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


class AdvancedIntelligenceReviewPacket(JsonModel):
    """Review packet including escalation and uncertainty-ledger context."""

    model_config = ConfigDict(extra="forbid")

    base_packet: IntelligenceReviewPacket = Field(
        ..., description="Base intelligence review packet."
    )
    escalation: DecisionEscalationFlags = Field(
        ..., description="Escalation flags for decision governance."
    )
    unresolved_questions: UnresolvedQuestionLedger = Field(
        ...,
        description="Deduplicated unresolved question ledger.",
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


class ComparativeCandidateReviewPacket(JsonModel):
    """Evidence-aware comparison between two candidate options."""

    model_config = ConfigDict(extra="forbid")

    program_id: str = Field(..., min_length=1)
    preferred_candidate_id: str = Field(..., min_length=1)
    compared_candidate_id: str = Field(..., min_length=1)
    preferred_rank: int | None = Field(default=None, ge=1)
    compared_rank: int | None = Field(default=None, ge=1)
    preferred_score: float = Field(...)
    compared_score: float = Field(...)
    evidence_support_delta: float = Field(...)
    residual_risk_delta: float = Field(...)
    rationale: list[str] = Field(default_factory=list)


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


def _top_candidate(
    ranking: CandidateRanking,
    risks: list[CandidateRiskProfile],
) -> tuple[str | None, float | None]:
    if not ranking.ranked_candidates:
        return None, None
    candidate_id = ranking.ranked_candidates[0].candidate_id
    risk_map = {risk.candidate_id: risk.residual_risk for risk in risks}
    return candidate_id, risk_map.get(candidate_id)


def _top_candidate_risk_profile(
    ranking: CandidateRanking,
    risks: list[CandidateRiskProfile],
) -> CandidateRiskProfile | None:
    if not ranking.ranked_candidates:
        return None
    candidate_id = ranking.ranked_candidates[0].candidate_id
    for risk in risks:
        if risk.candidate_id == candidate_id:
            return risk
    return None


def _top_candidate_blockers(ranking: CandidateRanking) -> list[str]:
    if not ranking.ranked_candidates:
        return []
    blockers = ranking.ranked_candidates[0].explainability.get("blockers", [])
    if not isinstance(blockers, list):
        return []
    return [str(item) for item in blockers if str(item).strip()]


def _top_candidate_confidence(ranking: CandidateRanking) -> float | None:
    if not ranking.ranked_candidates:
        return None
    confidence = ranking.ranked_candidates[0].explainability.get("confidence")
    if confidence is None:
        return None
    if not isinstance(confidence, (int, float, str)):
        return None
    try:
        return float(confidence)
    except (TypeError, ValueError):
        return None


def evaluate_for_progression(
    program: ProgramSpec,
    ranking: CandidateRanking,
    readiness: DecisionReadiness,
    policy: ProgressionPolicy | None = None,
) -> ScenarioEvaluation:
    """Decide whether the program should progress to the next gated step."""
    policy = policy or ProgressionPolicy(policy_id="progression-default")
    reasons: list[str] = []
    if not readiness.ready:
        reasons.extend(readiness.blockers)
        return ScenarioEvaluation(
            scenario="progression",
            action=ScenarioAction.HOLD,
            reasons=reasons,
            hypothesis_status=HypothesisStatus.WEAKENED,
            key_discriminating_experiment="run orthogonal assay panel to resolve readiness blockers",
            confidence=0.45,
            unresolved_questions=list(readiness.blockers),
        )
    if policy.require_ranked_candidate and not ranking.ranked_candidates:
        return ScenarioEvaluation(
            scenario="progression",
            action=ScenarioAction.REDESIGN,
            reasons=["no ranked candidates remain after screening"],
            hypothesis_status=HypothesisStatus.WEAKENED,
            key_discriminating_experiment="expand candidate generation with mechanism-preserving variants",
            confidence=0.6,
            unresolved_questions=[
                "no prioritized candidate is available for the progression decision"
            ],
        )
    top_blockers = _top_candidate_blockers(ranking)
    top_confidence = _top_candidate_confidence(ranking)
    if (
        top_confidence is not None
        and top_confidence < policy.minimum_top_candidate_confidence
    ):
        return ScenarioEvaluation(
            scenario="progression",
            action=ScenarioAction.HOLD,
            reasons=[
                f"top candidate confidence {top_confidence:.2f} is below policy floor"
            ],
            hypothesis_status=HypothesisStatus.UNRESOLVED,
            key_discriminating_experiment="collect orthogonal evidence to increase top candidate confidence",
            confidence=0.58,
            unresolved_questions=[f"top_candidate_confidence={top_confidence:.2f}"],
        )
    if len(top_blockers) > policy.maximum_blocker_findings_on_top_candidate:
        return ScenarioEvaluation(
            scenario="progression",
            action=ScenarioAction.HOLD,
            reasons=[f"top candidate carries {len(top_blockers)} blocker findings"],
            hypothesis_status=HypothesisStatus.UNRESOLVED,
            key_discriminating_experiment="run focused follow-up assays to resolve top blocker liabilities",
            confidence=0.6,
            unresolved_questions=top_blockers[:5],
        )
    if ranking.ranked_candidates:
        reasons.append(
            f"top candidate {ranking.ranked_candidates[0].candidate_id} is available"
        )
    else:
        reasons.append(
            "evidence is decision-ready even though ranking has not been generated yet"
        )
    reasons.append(
        f"{len(program.review_gates)} review gates are modeled in the program"
    )
    return ScenarioEvaluation(
        scenario="progression",
        action=ScenarioAction.ADVANCE,
        reasons=reasons,
        hypothesis_status=HypothesisStatus.SUPPORTED,
        key_discriminating_experiment=None,
        confidence=0.85,
    )


def evaluate_for_synthesis(
    ranking: CandidateRanking,
    readiness: DecisionReadiness,
    risks: list[CandidateRiskProfile],
    policy: SynthesisPolicy | None = None,
) -> ScenarioEvaluation:
    """Decide whether the program is ready to synthesize a top candidate."""
    policy = policy or SynthesisPolicy(policy_id="synthesis-default")
    candidate_id, residual_risk = _top_candidate(ranking, risks)
    if candidate_id is None:
        return ScenarioEvaluation(
            scenario="synthesis",
            action=ScenarioAction.REDESIGN,
            reasons=["no candidates are available for synthesis"],
            hypothesis_status=HypothesisStatus.WEAKENED,
            key_discriminating_experiment="generate candidates with improved multi-objective profiles",
            confidence=0.55,
            unresolved_questions=["candidate pool is empty for synthesis"],
        )
    if not readiness.ready:
        return ScenarioEvaluation(
            scenario="synthesis",
            action=ScenarioAction.HOLD,
            reasons=readiness.blockers,
            hypothesis_status=HypothesisStatus.UNRESOLVED,
            key_discriminating_experiment="collect missing decisive evidence before synthesis",
            confidence=0.5,
            unresolved_questions=list(readiness.blockers),
        )
    if residual_risk is not None and residual_risk > policy.maximum_residual_risk:
        return ScenarioEvaluation(
            scenario="synthesis",
            action=ScenarioAction.REDESIGN,
            reasons=[
                f"top candidate {candidate_id} has residual risk {residual_risk:.2f}"
            ],
            hypothesis_status=HypothesisStatus.WEAKENED,
            key_discriminating_experiment="run risk-focused assays on top liabilities",
            confidence=0.65,
            unresolved_questions=[
                f"residual_risk={residual_risk:.2f} exceeds policy limit"
            ],
        )
    top_profile = _top_candidate_risk_profile(ranking, risks)
    if top_profile is not None and top_profile.safety_risk > policy.maximum_safety_risk:
        return ScenarioEvaluation(
            scenario="synthesis",
            action=ScenarioAction.REDESIGN,
            reasons=[
                f"top candidate safety risk {top_profile.safety_risk:.2f} exceeds policy"
            ],
            hypothesis_status=HypothesisStatus.WEAKENED,
            key_discriminating_experiment="run safety-focused assays before synthesis commitment",
            confidence=0.66,
            unresolved_questions=[
                f"safety_risk={top_profile.safety_risk:.2f} exceeds policy limit"
            ],
        )
    top_blockers = _top_candidate_blockers(ranking)
    top_confidence = _top_candidate_confidence(ranking)
    if (
        top_confidence is not None
        and top_confidence < policy.minimum_top_candidate_confidence
    ):
        return ScenarioEvaluation(
            scenario="synthesis",
            action=ScenarioAction.HOLD,
            reasons=[
                f"top candidate confidence {top_confidence:.2f} is below synthesis policy floor"
            ],
            hypothesis_status=HypothesisStatus.UNRESOLVED,
            key_discriminating_experiment="collect confirmatory assays before synthesis commitment",
            confidence=0.6,
            unresolved_questions=[f"top_candidate_confidence={top_confidence:.2f}"],
        )
    if len(top_blockers) > policy.maximum_blocker_findings_on_top_candidate:
        return ScenarioEvaluation(
            scenario="synthesis",
            action=ScenarioAction.HOLD,
            reasons=[
                f"top candidate still has {len(top_blockers)} open blocker findings"
            ],
            hypothesis_status=HypothesisStatus.UNRESOLVED,
            key_discriminating_experiment="run blocker-focused assays before synthesis commitment",
            confidence=0.62,
            unresolved_questions=top_blockers[:5],
        )
    return ScenarioEvaluation(
        scenario="synthesis",
        action=ScenarioAction.ADVANCE,
        reasons=[f"top candidate {candidate_id} is supported and within risk budget"],
        hypothesis_status=HypothesisStatus.SUPPORTED,
        key_discriminating_experiment=None,
        confidence=0.85,
    )


def evaluate_for_scale_up(
    ranking: CandidateRanking,
    readiness: DecisionReadiness,
    risks: list[CandidateRiskProfile],
    policy: ScaleUpPolicy | None = None,
) -> ScenarioEvaluation:
    """Decide whether the current top candidate is ready for scale-up."""
    policy = policy or ScaleUpPolicy(policy_id="scale-up-default")
    candidate_id, residual_risk = _top_candidate(ranking, risks)
    if candidate_id is None:
        return ScenarioEvaluation(
            scenario="scale_up",
            action=ScenarioAction.REDESIGN,
            reasons=["scale-up requires at least one prioritized candidate"],
            hypothesis_status=HypothesisStatus.WEAKENED,
            confidence=0.55,
            unresolved_questions=["no prioritized candidate is available for scale-up"],
        )
    if (
        not readiness.ready
        or readiness.coverage.decisive_records < policy.minimum_decisive_records
    ):
        return ScenarioEvaluation(
            scenario="scale_up",
            action=ScenarioAction.HOLD,
            reasons=[
                "scale-up needs decision-ready evidence with at least "
                f"{policy.minimum_decisive_records} decisive records"
            ],
            hypothesis_status=HypothesisStatus.UNRESOLVED,
            confidence=0.5,
            unresolved_questions=[
                "insufficient decisive evidence for scale-up confidence"
            ],
        )
    if residual_risk is not None and residual_risk <= policy.maximum_residual_risk:
        top_profile = _top_candidate_risk_profile(ranking, risks)
        if (
            top_profile is not None
            and top_profile.safety_risk > policy.maximum_safety_risk
        ):
            return ScenarioEvaluation(
                scenario="scale_up",
                action=ScenarioAction.HOLD,
                reasons=["safety-specific risk remains above scale-up policy"],
                hypothesis_status=HypothesisStatus.UNRESOLVED,
                confidence=0.62,
                unresolved_questions=[
                    f"safety_risk={top_profile.safety_risk:.2f} remains above policy"
                ],
            )
        return ScenarioEvaluation(
            scenario="scale_up",
            action=ScenarioAction.SCALE_UP,
            reasons=[f"top candidate {candidate_id} has low residual risk"],
            hypothesis_status=HypothesisStatus.SUPPORTED,
            confidence=0.85,
        )
    return ScenarioEvaluation(
        scenario="scale_up",
        action=ScenarioAction.HOLD,
        reasons=[
            f"top candidate {candidate_id} still carries too much residual risk for scale-up"
        ],
        hypothesis_status=HypothesisStatus.UNRESOLVED,
        confidence=0.6,
        unresolved_questions=[
            f"residual_risk={residual_risk:.2f} remains above scale-up policy"
        ],
    )


def evaluate_for_redesign(
    ranking: CandidateRanking,
    readiness: DecisionReadiness,
    policy: RedesignPolicy | None = None,
) -> ScenarioEvaluation:
    """Decide whether the system should move back into redesign."""
    policy = policy or RedesignPolicy(policy_id="redesign-default")
    if not ranking.ranked_candidates or (
        policy.redesign_on_any_rejection and ranking.rejected_candidates
    ):
        return ScenarioEvaluation(
            scenario="redesign",
            action=ScenarioAction.REDESIGN,
            reasons=["ranking outcomes indicate the current design set is weak"],
            hypothesis_status=HypothesisStatus.WEAKENED,
            confidence=0.7,
            unresolved_questions=["candidate ranking indicates redesign pressure"],
        )
    if not readiness.ready:
        return ScenarioEvaluation(
            scenario="redesign",
            action=ScenarioAction.HOLD,
            reasons=readiness.blockers,
            hypothesis_status=HypothesisStatus.UNRESOLVED,
            confidence=0.5,
            unresolved_questions=list(readiness.blockers),
        )
    return ScenarioEvaluation(
        scenario="redesign",
        action=ScenarioAction.ADVANCE,
        reasons=["current candidates and evidence do not require immediate redesign"],
        hypothesis_status=HypothesisStatus.SUPPORTED,
        confidence=0.8,
    )


def evaluate_all_scenarios(
    program: ProgramSpec,
    ranking: CandidateRanking,
    readiness: DecisionReadiness,
    risks: list[CandidateRiskProfile],
    *,
    policies: EvaluatorPolicyBundle | None = None,
) -> ScenarioSetEvaluation:
    """Evaluate all scenario endpoints under a shared policy bundle."""
    policies = policies or EvaluatorPolicyBundle()
    return ScenarioSetEvaluation(
        progression=evaluate_for_progression(
            program,
            ranking,
            readiness,
            policy=policies.progression,
        ),
        synthesis=evaluate_for_synthesis(
            ranking,
            readiness,
            risks,
            policy=policies.synthesis,
        ),
        scale_up=evaluate_for_scale_up(
            ranking,
            readiness,
            risks,
            policy=policies.scale_up,
        ),
        redesign=evaluate_for_redesign(
            ranking,
            readiness,
            policy=policies.redesign,
        ),
    )


def evaluate_portfolio_balance(
    ranking: CandidateRanking,
    risks: list[CandidateRiskProfile],
    *,
    top_n: int = 3,
) -> PortfolioDecisionReport:
    """Assess whether top ranked candidates form a scientifically balanced portfolio."""
    top_candidates = ranking.ranked_candidates[: max(top_n, 1)]
    selected_ids = [candidate.candidate_id for candidate in top_candidates]
    risk_map = {risk.candidate_id: risk for risk in risks}
    selected_risks = [
        risk_map[candidate_id]
        for candidate_id in selected_ids
        if candidate_id in risk_map
    ]
    liability_labels: set[str] = set()
    for candidate in top_candidates:
        blockers = candidate.explainability.get("blockers", [])
        if isinstance(blockers, list):
            for blocker in blockers:
                liability_labels.add(str(blocker))
    mean_residual_risk = (
        round(
            sum(risk.residual_risk for risk in selected_risks) / len(selected_risks), 4
        )
        if selected_risks
        else 0.0
    )
    notes: list[str] = []
    low_diversity = len(liability_labels) <= 1 and len(top_candidates) > 1
    high_risk = mean_residual_risk > 0.5
    if low_diversity:
        notes.append(
            "top candidates share similar blocker patterns and may limit portfolio diversity"
        )
    if high_risk:
        notes.append("mean residual risk is above preferred portfolio threshold")
    if not notes:
        notes.append("top candidate set shows acceptable diversity and risk posture")
    return PortfolioDecisionReport(
        candidate_count=len(top_candidates),
        liability_diversity=len(liability_labels),
        mean_residual_risk=mean_residual_risk,
        balanced_portfolio=not low_diversity and not high_risk,
        notes=notes,
    )


def summarize_scenario_consensus(
    evaluations: ScenarioSetEvaluation,
) -> ScenarioDecisionConsensus:
    """Summarize grouped scenario evaluations into one consensus action view."""
    scenario_actions = [
        evaluations.progression.action,
        evaluations.synthesis.action,
        evaluations.scale_up.action,
        evaluations.redesign.action,
    ]
    action_counts: dict[str, int] = {}
    for action in scenario_actions:
        action_counts[action.value] = action_counts.get(action.value, 0) + 1
    recommended = max(action_counts, key=lambda action: action_counts[action])
    conflicting_actions = len(action_counts) > 1
    notes = (
        ["scenario actions are mixed and require explicit human arbitration"]
        if conflicting_actions
        else ["scenario actions are aligned"]
    )
    return ScenarioDecisionConsensus(
        recommended_action=ScenarioAction(recommended),
        action_counts=action_counts,
        conflicting_actions=conflicting_actions,
        notes=notes,
    )


def build_intelligence_review_packet(
    evaluations: ScenarioSetEvaluation,
    ranking: CandidateRanking,
    risks: list[CandidateRiskProfile],
) -> IntelligenceReviewPacket:
    """Build a review packet from scenario and portfolio intelligence outputs."""
    consensus = summarize_scenario_consensus(evaluations)
    portfolio = evaluate_portfolio_balance(ranking, risks)
    review_ready = not consensus.conflicting_actions and portfolio.balanced_portfolio
    notes: list[str] = []
    if consensus.conflicting_actions:
        notes.append("scenario recommendations conflict and require adjudication")
    if not portfolio.balanced_portfolio:
        notes.append(
            "portfolio balance is weak and should be improved before progression"
        )
    if not notes:
        notes.append("intelligence outputs are aligned for review discussion")
    return IntelligenceReviewPacket(
        consensus=consensus,
        portfolio=portfolio,
        review_ready=review_ready,
        notes=notes,
    )


def build_comparative_candidate_review_packet(
    ranking: CandidateRanking,
    assessments: list[CandidateAssessment],
    risks: list[CandidateRiskProfile],
    *,
    preferred_candidate_id: str,
    compared_candidate_id: str,
) -> ComparativeCandidateReviewPacket:
    """Explain why one candidate is preferred over another using evidence and risk."""
    ranked_map = {
        candidate.candidate_id: candidate for candidate in ranking.ranked_candidates
    }
    assessment_map = {assessment.candidate_id: assessment for assessment in assessments}
    risk_map = {risk.candidate_id: risk for risk in risks}
    preferred = ranked_map.get(preferred_candidate_id)
    compared = ranked_map.get(compared_candidate_id)
    if preferred is None or compared is None:
        raise ValueError("both candidates must be present in the ranked candidate set")
    preferred_assessment = assessment_map.get(preferred_candidate_id)
    compared_assessment = assessment_map.get(compared_candidate_id)
    if preferred_assessment is None or compared_assessment is None:
        raise ValueError(
            "candidate assessments are required for both compared candidates"
        )
    preferred_risk = risk_map.get(preferred_candidate_id)
    compared_risk = risk_map.get(compared_candidate_id)
    preferred_residual_risk = (
        preferred_risk.residual_risk if preferred_risk is not None else 0.0
    )
    compared_residual_risk = (
        compared_risk.residual_risk if compared_risk is not None else 0.0
    )
    rationale = [
        f"score delta = {preferred.score - compared.score:.4f}",
        f"evidence support delta = {preferred_assessment.evidence_support - compared_assessment.evidence_support:.4f}",
        f"residual risk delta = {compared_residual_risk - preferred_residual_risk:.4f}",
    ]
    if preferred.score <= compared.score:
        rationale.append(
            "preferred candidate is being justified despite a non-positive score delta"
        )
    preferred_drivers = preferred.explainability.get("top_drivers", [])
    if isinstance(preferred_drivers, list) and preferred_drivers:
        rationale.append(
            "preferred drivers: "
            + ", ".join(str(item) for item in preferred_drivers[:3])
        )
    compared_blockers = compared.explainability.get("blockers", [])
    if isinstance(compared_blockers, list) and compared_blockers:
        rationale.append(
            "compared blockers: "
            + ", ".join(str(item) for item in compared_blockers[:3])
        )
    return ComparativeCandidateReviewPacket(
        program_id=ranking.program_id,
        preferred_candidate_id=preferred_candidate_id,
        compared_candidate_id=compared_candidate_id,
        preferred_rank=preferred.rank,
        compared_rank=compared.rank,
        preferred_score=preferred.score,
        compared_score=compared.score,
        evidence_support_delta=round(
            preferred_assessment.evidence_support
            - compared_assessment.evidence_support,
            4,
        ),
        residual_risk_delta=round(
            compared_residual_risk - preferred_residual_risk,
            4,
        ),
        rationale=rationale,
    )


def summarize_hold_pressure(
    evaluations: ScenarioSetEvaluation,
    *,
    threshold: float = 0.5,
) -> HoldPressureSummary:
    """Summarize hold recommendation pressure across scenarios."""
    actions = [
        evaluations.progression.action,
        evaluations.synthesis.action,
        evaluations.scale_up.action,
        evaluations.redesign.action,
    ]
    hold_count = sum(1 for action in actions if action is ScenarioAction.HOLD)
    hold_fraction = round(hold_count / len(actions), 4)
    return HoldPressureSummary(
        hold_count=hold_count,
        total_scenarios=len(actions),
        hold_fraction=hold_fraction,
        high_hold_pressure=hold_fraction >= threshold,
    )


def summarize_scenario_confidence_spread(
    evaluations: ScenarioSetEvaluation,
) -> ScenarioConfidenceSpread:
    """Summarize confidence spread across all scenario evaluations."""
    confidences = [
        evaluations.progression.confidence,
        evaluations.synthesis.confidence,
        evaluations.scale_up.confidence,
        evaluations.redesign.confidence,
    ]
    minimum = min(confidences)
    maximum = max(confidences)
    mean = round(sum(confidences) / len(confidences), 4)
    return ScenarioConfidenceSpread(
        minimum_confidence=minimum,
        maximum_confidence=maximum,
        mean_confidence=mean,
        spread=round(maximum - minimum, 4),
    )


def summarize_uncertainty_preserving_interpretation(
    evaluations: ScenarioSetEvaluation,
) -> UncertaintyPreservingInterpretationSummary:
    """Summarize scenario outputs without flattening disagreement away."""
    scenarios = [
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


def summarize_assessment_metric_coverage(
    assessments: list[CandidateAssessment],
    *,
    required_metrics: list[str],
) -> AssessmentMetricCoverageReport:
    """Summarize required metric coverage across candidate assessments."""
    present: set[str] = set()
    for assessment in assessments:
        present.update(assessment.metric_scores.keys())
    covered = [metric for metric in required_metrics if metric in present]
    missing = [metric for metric in required_metrics if metric not in present]
    liability_labels = {
        liability.summary.strip()
        for assessment in assessments
        for liability in assessment.liabilities
        if liability.summary.strip()
    }
    if not liability_labels:
        liability_labels = set(missing)
    coverage_ratio = (
        round((len(covered) / len(required_metrics)), 4) if required_metrics else 0.0
    )
    missing_ratio = len(missing) / len(required_metrics) if required_metrics else 0.0
    mean_residual_risk = round(
        min(1.0, missing_ratio + (0.1 if missing else 0.0)),
        4,
    )
    return AssessmentMetricCoverageReport(
        required_metrics=required_metrics,
        covered_metrics=covered,
        missing_metrics=missing,
        coverage_ratio=coverage_ratio,
        liability_diversity=len(liability_labels),
        mean_residual_risk=mean_residual_risk,
    )


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
    return FinalDecisionRecommendation(
        action=consensus.recommended_action,
        requires_human_review=escalation.escalate_to_human_review,
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


def build_advanced_review_packet(
    evaluations: ScenarioSetEvaluation,
    ranking: CandidateRanking,
    risks: list[CandidateRiskProfile],
) -> AdvancedIntelligenceReviewPacket:
    """Build advanced review packet with escalation and unresolved question ledger."""
    base = build_intelligence_review_packet(evaluations, ranking, risks)
    escalation = derive_decision_escalation_flags(evaluations)
    ledger = summarize_unresolved_question_ledger(evaluations)
    return AdvancedIntelligenceReviewPacket(
        base_packet=base,
        escalation=escalation,
        unresolved_questions=ledger,
    )
