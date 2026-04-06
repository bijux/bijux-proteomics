# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Design briefs and candidate ranking for protein programs."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.programs import MeasurementDirection, ProgramSpec
from bijux_proteomics_foundation import CandidateId, ProgramId, TargetId
from bijux_proteomics_knowledge import EvidenceBundle, evidence_gaps
from bijux_proteomics_intelligence.outcomes import (
    CandidateRejection,
    RejectionReasonCode,
    TieBreakExplanation,
    build_rejection_action_plan,
)
from bijux_proteomics_intelligence.policies import (
    RankingFactor,
    RankingPolicy,
    ScientificMetricClass,
    TieBreakRule,
    classify_metric_name,
)
from bijux_proteomics_intelligence.serialization import JsonModel


class OptimizationAxis(StrEnum):
    """Optimization dimensions used to compare protein candidates."""

    ACTIVITY = "activity"
    AFFINITY = "affinity"
    STABILITY = "stability"
    SPECIFICITY = "specificity"
    DEVELOPABILITY = "developability"
    SAFETY = "safety"


class LiabilityFlag(JsonModel):
    """A program or candidate risk that should shape ranking."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1, description="Stable liability code.")
    summary: str = Field(..., min_length=1, description="Human-readable risk summary.")
    severity: int = Field(..., ge=1, le=5, description="Risk severity from low to high.")
    source: str = Field(..., min_length=1, description="Where the liability came from.")


class DesignBrief(JsonModel):
    """Condensed program intent for design and review work."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    target_id: TargetId = Field(..., description="Target identifier.")
    objective: str = Field(..., min_length=1, description="Program objective.")
    mechanism: str = Field(..., min_length=1, description="Target mechanism hypothesis.")
    optimization_axes: list[OptimizationAxis] = Field(
        default_factory=list,
        description="Ordered optimization dimensions for candidate ranking.",
    )
    blocking_assays: list[str] = Field(
        default_factory=list,
        description="Assays that block expensive downstream work.",
    )
    review_gate_ids: list[str] = Field(
        default_factory=list,
        description="Human approvals that must clear the design.",
    )
    evidence_gaps: list[str] = Field(
        default_factory=list,
        description="Evidence kinds still missing for decision readiness.",
    )
    liabilities: list[LiabilityFlag] = Field(
        default_factory=list,
        description="Current liabilities that must be actively managed.",
    )
    ranking_priorities: list[str] = Field(
        default_factory=list,
        description="Ordered priorities to apply during candidate ranking.",
    )
    downstream_lab_assumptions: list[str] = Field(
        default_factory=list,
        description="Assumptions that downstream lab planning should validate.",
    )
    risk_appetite: str = Field(
        default="balanced",
        min_length=1,
        description="Risk appetite for this decision context.",
    )
    prohibited_failure_modes: list[str] = Field(
        default_factory=list,
        description="Failure modes that must not be tolerated in candidate selection.",
    )


class CandidateAssessment(JsonModel):
    """A candidate with explicit scoring context."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: CandidateId = Field(..., description="Stable candidate identifier.")
    sequence: str = Field(..., min_length=1, description="Candidate protein sequence.")
    metric_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Observed or predicted metrics keyed by metric name.",
    )
    manufacturability_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="How easy the candidate is to express and handle.",
    )
    uncertainty: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Uncertainty in the candidate assessment.",
    )
    liabilities: list[LiabilityFlag] = Field(
        default_factory=list,
        description="Candidate-specific risks.",
    )
    evidence_support: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="How well the candidate is supported by current evidence.",
    )


class RankedCandidate(JsonModel):
    """A ranked candidate with transparent reasoning."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: CandidateId = Field(..., description="Stable candidate identifier.")
    score: float = Field(..., description="Composite ranking score.")
    rank: int = Field(..., ge=1, description="Position in the ordered list.")
    reasons: list[str] = Field(
        default_factory=list,
        description="Short explanations for the ranking outcome.",
    )
    explainability: dict[str, object] = Field(
        default_factory=dict,
        description="Structured explanation for the ranking outcome.",
    )


class CandidateRanking(JsonModel):
    """Ordered candidate list for a program."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    ranked_candidates: list[RankedCandidate] = Field(
        default_factory=list,
        description="Candidates ordered from strongest to weakest.",
    )
    rejected_candidates: list[str] = Field(
        default_factory=list,
        description="Candidates screened out for missing minimum requirements.",
    )
    rejections: list[CandidateRejection] = Field(
        default_factory=list,
        description="Structured rejection details for screened-out candidates.",
    )
    tie_breaks: list[TieBreakExplanation] = Field(
        default_factory=list,
        description="Tie-break decisions that affected ranking order.",
    )


class CandidateExplainabilitySummary(JsonModel):
    """Review-ready explanation for one ranked candidate."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: CandidateId = Field(..., description="Stable candidate identifier.")
    strengths: list[str] = Field(
        default_factory=list,
        description="Why the candidate remains attractive.",
    )
    open_risks: list[str] = Field(
        default_factory=list,
        description="Liabilities or uncertainty that still need attention.",
    )
    evidence_gaps: list[str] = Field(
        default_factory=list,
        description="Evidence gaps that still affect confidence in the candidate.",
    )


class CandidateScoreBreakdown(JsonModel):
    """Detailed score decomposition for one ranked candidate."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: CandidateId = Field(..., description="Stable candidate identifier.")
    normalized_factor_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Per-factor normalized scores before weighting.",
    )
    weighted_contributions: dict[str, float] = Field(
        default_factory=dict,
        description="Per-factor weighted score contributions.",
    )
    base_score: float = Field(..., ge=0.0, description="Weighted score before uncertainty penalty.")
    uncertainty_penalty: float = Field(
        ...,
        ge=0.0,
        description="Penalty subtracted due to uncertainty.",
    )
    final_score: float = Field(..., ge=0.0, description="Final score after penalty.")


class LiabilityFocusSummary(JsonModel):
    """Summary of dominant liabilities in a ranked candidate set."""

    model_config = ConfigDict(extra="forbid")

    liability_counts: dict[str, int] = Field(
        default_factory=dict,
        description="Count of liabilities by code across ranked candidates.",
    )
    top_liabilities: list[str] = Field(
        default_factory=list,
        description="Most frequent liability codes in ranking order.",
    )


def _metric_weight_name(metric: str) -> OptimizationAxis:
    metric_class = classify_metric_name(metric)
    if metric_class is ScientificMetricClass.AFFINITY:
        return OptimizationAxis.AFFINITY
    if metric_class is ScientificMetricClass.STABILITY:
        return OptimizationAxis.STABILITY
    if metric_class is ScientificMetricClass.SPECIFICITY:
        return OptimizationAxis.SPECIFICITY
    if metric_class is ScientificMetricClass.SAFETY:
        return OptimizationAxis.SAFETY
    if metric_class is ScientificMetricClass.DEVELOPABILITY:
        return OptimizationAxis.DEVELOPABILITY
    return OptimizationAxis.ACTIVITY


def build_design_brief(
    program: ProgramSpec,
    bundle: EvidenceBundle | None = None,
) -> DesignBrief:
    """Build a design brief from program intent and current evidence."""
    axes: list[OptimizationAxis] = []
    for criterion in program.success_criteria:
        axis = _metric_weight_name(criterion.metric)
        if axis not in axes:
            axes.append(axis)
    if not axes:
        axes.append(OptimizationAxis.ACTIVITY)

    liabilities = [
        LiabilityFlag(
            code=constraint.constraint_id,
            summary=constraint.statement,
            severity=4 if constraint.threshold is not None else 3,
            source="constraint",
        )
        for constraint in program.constraints
    ]
    liabilities.extend(
        LiabilityFlag(
            code=f"blocked-outcome-{index}",
            summary=outcome,
            severity=4,
            source="target",
        )
        for index, outcome in enumerate(program.target.blocked_outcomes, start=1)
    )

    required_kinds = [need.value for need in program.evidence_needs]
    gaps = evidence_gaps(bundle, required_kinds) if bundle else required_kinds
    return DesignBrief(
        program_id=program.program_id,
        target_id=program.target.target_id,
        objective=program.objective,
        mechanism=program.target.mechanism,
        optimization_axes=axes,
        blocking_assays=[
            assay.assay_id for assay in program.assay_panel if assay.blocking
        ],
        review_gate_ids=[gate.gate_id for gate in program.review_gates if gate.blocking],
        evidence_gaps=gaps,
        liabilities=liabilities,
        ranking_priorities=[axis.value for axis in axes],
        downstream_lab_assumptions=(
            [assay.purpose for assay in program.assay_panel]
            if program.assay_panel
            else ["define assays that can validate candidate progression assumptions"]
        ),
        risk_appetite=(
            "cautious"
            if program.stage.value in {"review", "lab_ready"}
            else "balanced"
        ),
        prohibited_failure_modes=sorted(
            {
                liability.summary
                for liability in liabilities
                if liability.severity >= 4
            }
        ),
    )


def _criterion_score(candidate: CandidateAssessment, program: ProgramSpec) -> float:
    total = 0.0
    for criterion in program.success_criteria:
        value = candidate.metric_scores.get(criterion.metric, 0.0)
        if criterion.direction is MeasurementDirection.MAXIMIZE:
            total += min(value / criterion.threshold, 1.5)
        elif criterion.direction is MeasurementDirection.MINIMIZE:
            if value <= 0:
                total += 1.0
            else:
                total += min(criterion.threshold / value, 1.5)
        else:
            distance = abs(value - criterion.threshold)
            scale = max(abs(criterion.threshold), 1.0)
            total += max(0.0, 1.0 - (distance / scale))
    return total


def _screen_candidate(
    candidate: CandidateAssessment,
    program: ProgramSpec,
    profile: RankingPolicy,
) -> tuple[bool, list[str], list[RejectionReasonCode], float]:
    criterion_score = _criterion_score(candidate, program)
    threshold_count = max(len(program.success_criteria), 1)
    mean_fraction = criterion_score / threshold_count
    reasons: list[str] = []
    reason_codes: list[RejectionReasonCode] = []

    if program.success_criteria and mean_fraction < profile.minimum_metric_fraction:
        reasons.append("below minimum criterion fraction")
        reason_codes.append(RejectionReasonCode.LOW_METRIC_FRACTION)
    if candidate.evidence_support < profile.minimum_evidence_support:
        reasons.append("insufficient evidence support")
        reason_codes.append(RejectionReasonCode.LOW_EVIDENCE_SUPPORT)
    if (
        profile.require_manufacturability_floor
        and candidate.manufacturability_score < profile.manufacturability_floor
    ):
        reasons.append("below manufacturability floor")
        reason_codes.append(RejectionReasonCode.LOW_MANUFACTURABILITY)
    return (not reasons, reasons, reason_codes, criterion_score)


def prioritize_candidates(
    program: ProgramSpec,
    candidates: list[CandidateAssessment],
    policy: RankingPolicy | None = None,
) -> CandidateRanking:
    """Rank candidates with transparent penalties for risk and weak support."""
    policy = policy or RankingPolicy(policy_id="default-balance")
    scored: list[tuple[CandidateAssessment, float, list[str], dict[str, float]]] = []
    rejected: list[str] = []
    rejections: list[CandidateRejection] = []
    for candidate in candidates:
        passed, rejection_reasons, rejection_reason_codes, criterion_score = _screen_candidate(
            candidate,
            program,
            policy,
        )
        if not passed:
            rejected.append(candidate.candidate_id)
            rejection = CandidateRejection(
                candidate_id=candidate.candidate_id,
                reasons=rejection_reasons,
                reason_codes=rejection_reason_codes,
            )
            rejections.append(rejection)
            action_plan = build_rejection_action_plan(rejection)
            rejections[-1] = rejection.model_copy(
                update={
                    "recommended_experiments": action_plan.experiments,
                    "reopen_conditions": action_plan.revisit_conditions,
                }
            )
            continue
        threshold_count = max(len(program.success_criteria), 1)
        factor_scores = {
            RankingFactor.CRITERIA.value: round(
                min(criterion_score / (threshold_count * 1.5), 1.0), 4
            ),
            RankingFactor.EVIDENCE.value: round(candidate.evidence_support, 4),
            RankingFactor.MANUFACTURABILITY.value: round(candidate.manufacturability_score, 4),
            RankingFactor.LIABILITY.value: round(
                max(0.0, 1.0 - (sum(flag.severity for flag in candidate.liabilities) / 10.0)),
                4,
            ),
            RankingFactor.UNCERTAINTY.value: round(max(0.0, 1.0 - candidate.uncertainty), 4),
        }
        score = sum(
            factor_scores[factor.value] * weight
            for factor, weight in policy.factor_weights.items()
        )
        reasons = [
            f"criteria_factor={factor_scores[RankingFactor.CRITERIA.value]:.2f}",
            f"evidence_factor={factor_scores[RankingFactor.EVIDENCE.value]:.2f}",
            f"manufacturability_factor={factor_scores[RankingFactor.MANUFACTURABILITY.value]:.2f}",
            f"uncertainty_factor={factor_scores[RankingFactor.UNCERTAINTY.value]:.2f}",
        ]
        if candidate.liabilities:
            reasons.append(
                "liabilities="
                + ",".join(
                    flag.code for flag in sorted(candidate.liabilities, key=lambda item: item.code)
                )
            )
        scored.append((candidate, score, reasons, factor_scores))

    ranked = sorted(
        scored,
        key=lambda item: (
            item[1],
            item[0].evidence_support if TieBreakRule.EVIDENCE_SUPPORT in policy.tie_break_rules else 0.0,
            item[0].manufacturability_score if TieBreakRule.MANUFACTURABILITY in policy.tie_break_rules else 0.0,
            -item[0].uncertainty if TieBreakRule.LOWER_UNCERTAINTY in policy.tie_break_rules else 0.0,
            -len(item[0].liabilities) if TieBreakRule.FEWER_LIABILITIES in policy.tie_break_rules else 0.0,
        ),
        reverse=True,
    )
    tie_breaks: list[TieBreakExplanation] = []
    for left, right in zip(ranked, ranked[1:]):
        if round(left[1], 4) == round(right[1], 4):
            tie_breaks.append(
                TieBreakExplanation(
                    winner_candidate_id=left[0].candidate_id,
                    compared_candidate_id=right[0].candidate_id,
                    rules_applied=[rule.value for rule in policy.tie_break_rules],
                )
            )

    return CandidateRanking(
        program_id=program.program_id,
        ranked_candidates=[
            RankedCandidate(
                candidate_id=candidate.candidate_id,
                score=round(score, 4),
                rank=index,
                reasons=reasons,
                explainability={
                    "top_drivers": reasons[:3],
                    "blockers": [
                        flag.summary for flag in candidate.liabilities[:3]
                    ],
                    "confidence": round(1.0 - candidate.uncertainty, 4),
                    "factor_scores": factor_scores,
                    "missing_evidence": [],
                },
            )
            for index, (candidate, score, reasons, factor_scores) in enumerate(ranked, start=1)
        ],
        rejected_candidates=rejected,
        rejections=rejections,
        tie_breaks=tie_breaks,
    )


def summarize_candidate_explainability(
    ranking: CandidateRanking,
    brief: DesignBrief,
) -> list[CandidateExplainabilitySummary]:
    """Build review-ready summaries for ranked candidates."""
    summaries: list[CandidateExplainabilitySummary] = []
    for candidate in ranking.ranked_candidates:
        blockers = list(candidate.explainability.get("blockers", []))
        strengths = list(candidate.explainability.get("top_drivers", []))
        missing_evidence = brief.evidence_gaps
        if candidate.explainability.get("confidence", 0.0) >= 0.75:
            strengths.append("assessment confidence remains high enough for active consideration")
        summaries.append(
            CandidateExplainabilitySummary(
                candidate_id=candidate.candidate_id,
                strengths=strengths,
                open_risks=blockers,
                evidence_gaps=missing_evidence,
            )
        )
    return summaries


def candidate_score_breakdown(
    ranked_candidate: RankedCandidate,
    policy: RankingPolicy,
) -> CandidateScoreBreakdown:
    """Return a normalized and weighted score decomposition."""
    factor_scores = {
        str(key): float(value)
        for key, value in dict(ranked_candidate.explainability.get("factor_scores", {})).items()
    }
    weighted = {
        factor.value: round(
            factor_scores.get(factor.value, 0.0) * weight,
            4,
        )
        for factor, weight in policy.factor_weights.items()
    }
    base_score = round(sum(weighted.values()), 4)
    uncertainty_factor = factor_scores.get(RankingFactor.UNCERTAINTY.value, 1.0)
    uncertainty_penalty = round((1.0 - uncertainty_factor) * policy.uncertainty_penalty_weight, 4)
    final_score = max(0.0, round(base_score - uncertainty_penalty, 4))
    return CandidateScoreBreakdown(
        candidate_id=ranked_candidate.candidate_id,
        normalized_factor_scores=factor_scores,
        weighted_contributions=weighted,
        base_score=base_score,
        uncertainty_penalty=uncertainty_penalty,
        final_score=final_score,
    )


def summarize_liability_focus(
    ranking: CandidateRanking,
) -> LiabilityFocusSummary:
    """Summarize dominant liability codes across ranked candidates."""
    counts: dict[str, int] = {}
    for candidate in ranking.ranked_candidates:
        blockers = list(candidate.explainability.get("blockers", []))
        for blocker in blockers:
            counts[blocker] = counts.get(blocker, 0) + 1
    top = sorted(counts, key=lambda code: counts[code], reverse=True)
    return LiabilityFocusSummary(
        liability_counts=counts,
        top_liabilities=top[:5],
    )
