# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Scenario evaluators for progression decisions."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.program_spec import ProgramSpec
from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_intelligence.candidates.lifecycle import CandidateRiskProfile
from bijux_proteomics_intelligence.candidates.ranking import (
    CandidateAssessment,
    CandidateRanking,
)
from bijux_proteomics_knowledge.memory.models.evidence import DecisionReadiness


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
                (
                    "scale-up needs decision-ready evidence with at least "
                    f"{policy.minimum_decisive_records} decisive records"
                )
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
