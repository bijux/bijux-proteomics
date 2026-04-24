# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Design briefs and candidate ranking for protein programs."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.programs import MeasurementDirection, ProgramSpec
from bijux_proteomics_foundation import CandidateId, ProgramId, TargetId
from bijux_proteomics_intelligence.outcomes import (
    CandidateRejection,
    RejectionReasonCode,
    RejectionSummary,
    TieBreakExplanation,
    build_rejection_action_plan,
    summarize_rejections,
)
from bijux_proteomics_intelligence.policies import (
    RankingFactor,
    RankingPolicy,
    ScientificMetricClass,
    TieBreakRule,
    classify_metric_name,
)
from bijux_proteomics_intelligence.serialization import JsonModel
from bijux_proteomics_knowledge import EvidenceBundle, evidence_gaps


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
    severity: int = Field(
        ..., ge=1, le=5, description="Risk severity from low to high."
    )
    source: str = Field(..., min_length=1, description="Where the liability came from.")


class DesignBrief(JsonModel):
    """Condensed program intent for design and review work."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    target_id: TargetId = Field(..., description="Target identifier.")
    objective: str = Field(..., min_length=1, description="Program objective.")
    mechanism: str = Field(
        ..., min_length=1, description="Target mechanism hypothesis."
    )
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
    base_score: float = Field(
        ..., ge=0.0, description="Weighted score before uncertainty penalty."
    )
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


class UncertaintyPressureSummary(JsonModel):
    """Summary of uncertainty pressure across ranked candidates."""

    model_config = ConfigDict(extra="forbid")

    candidate_count: int = Field(
        ..., ge=0, description="Number of ranked candidates considered."
    )
    mean_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Mean confidence across ranked candidates."
    )
    low_confidence_candidate_ids: list[str] = Field(
        default_factory=list,
        description="Candidates below the confidence floor.",
    )
    uncertainty_pressure_high: bool = Field(
        ...,
        description="Whether uncertainty pressure is high enough to warrant a hold/redesign lens.",
    )


class NoveltyDiversitySummary(JsonModel):
    """Summary of sequence and liability diversity in ranked candidates."""

    model_config = ConfigDict(extra="forbid")

    candidate_count: int = Field(
        ..., ge=0, description="Number of ranked candidates considered."
    )
    unique_sequence_signatures: int = Field(
        ...,
        ge=0,
        description="Number of unique lightweight sequence signatures across ranked candidates.",
    )
    unique_liability_codes: int = Field(
        ...,
        ge=0,
        description="Number of unique liability blocker codes across ranked candidates.",
    )
    diversity_score: float = Field(
        ..., ge=0.0, le=1.0, description="Normalized diversity score."
    )


class RankingRobustnessReport(JsonModel):
    """Decision-facing robustness report for ranked candidate sets."""

    model_config = ConfigDict(extra="forbid")

    robustness_score: float = Field(
        ..., ge=0.0, le=1.0, description="Overall robustness score."
    )
    uncertainty_summary: UncertaintyPressureSummary = Field(
        ...,
        description="Uncertainty pressure summary used in robustness scoring.",
    )
    diversity_summary: NoveltyDiversitySummary = Field(
        ...,
        description="Diversity summary used in robustness scoring.",
    )
    notes: list[str] = Field(
        default_factory=list, description="Short notes explaining robustness posture."
    )


class MetricCoverageSummary(JsonModel):
    """Coverage summary of candidate metrics against program criteria."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: CandidateId = Field(..., description="Candidate identifier.")
    required_metrics: list[str] = Field(
        default_factory=list, description="Metrics required by program criteria."
    )
    provided_metrics: list[str] = Field(
        default_factory=list, description="Metrics present on candidate assessment."
    )
    missing_metrics: list[str] = Field(
        default_factory=list, description="Required metrics missing on candidate."
    )
    coverage_fraction: float = Field(
        ..., ge=0.0, le=1.0, description="Fraction of required metrics provided."
    )


class CriterionSatisfactionItem(JsonModel):
    """Per-criterion satisfaction entry for one candidate."""

    model_config = ConfigDict(extra="forbid")

    criterion_id: str = Field(..., min_length=1, description="Criterion identifier.")
    metric: str = Field(..., min_length=1, description="Metric key.")
    observed_value: float | None = Field(
        default=None, description="Observed candidate value."
    )
    satisfied: bool = Field(..., description="Whether criterion is satisfied.")


class CriterionSatisfactionVector(JsonModel):
    """Per-candidate vector of criterion satisfaction."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: CandidateId = Field(..., description="Candidate identifier.")
    items: list[CriterionSatisfactionItem] = Field(
        default_factory=list,
        description="Per-criterion satisfaction items.",
    )
    satisfied_fraction: float = Field(
        ..., ge=0.0, le=1.0, description="Fraction of criteria satisfied."
    )


class RankingDriftItem(JsonModel):
    """Rank movement for one candidate between two ranking snapshots."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: CandidateId = Field(..., description="Candidate identifier.")
    previous_rank: int | None = Field(
        default=None, ge=1, description="Previous rank if present."
    )
    current_rank: int | None = Field(
        default=None, ge=1, description="Current rank if present."
    )
    rank_shift: int = Field(
        ..., description="Positive when candidate moved up in ranking."
    )


class RankingDriftReport(JsonModel):
    """Audit report describing ranking drift between two snapshots."""

    model_config = ConfigDict(extra="forbid")

    moved_candidates: list[RankingDriftItem] = Field(
        default_factory=list, description="Candidates with rank movement."
    )
    newly_ranked_candidate_ids: list[str] = Field(
        default_factory=list, description="Candidates newly entering ranking."
    )
    dropped_candidate_ids: list[str] = Field(
        default_factory=list, description="Candidates dropped from ranking."
    )


class RankingDiagnostics(JsonModel):
    """Combined diagnostics for a ranking snapshot."""

    model_config = ConfigDict(extra="forbid")

    robustness: RankingRobustnessReport = Field(
        ..., description="Ranking robustness summary."
    )
    rejection_summary: RejectionSummary = Field(
        ..., description="Rejection analytics summary."
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
        review_gate_ids=[
            gate.gate_id for gate in program.review_gates if gate.blocking
        ],
        evidence_gaps=gaps,
        liabilities=liabilities,
        ranking_priorities=[axis.value for axis in axes],
        downstream_lab_assumptions=(
            [assay.purpose for assay in program.assay_panel]
            if program.assay_panel
            else ["define assays that can validate candidate progression assumptions"]
        ),
        risk_appetite=(
            "cautious" if program.stage.value in {"review", "lab_ready"} else "balanced"
        ),
        prohibited_failure_modes=sorted(
            {liability.summary for liability in liabilities if liability.severity >= 4}
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
    required_metrics = {criterion.metric for criterion in program.success_criteria}
    metric_coverage = (
        len(
            [metric for metric in required_metrics if metric in candidate.metric_scores]
        )
        / len(required_metrics)
        if required_metrics
        else 1.0
    )
    reasons: list[str] = []
    reason_codes: list[RejectionReasonCode] = []

    if program.success_criteria and mean_fraction < profile.minimum_metric_fraction:
        reasons.append("below minimum criterion fraction")
        reason_codes.append(RejectionReasonCode.LOW_METRIC_FRACTION)
    if (
        program.success_criteria
        and metric_coverage < profile.minimum_metric_coverage
        and RejectionReasonCode.LOW_METRIC_FRACTION not in reason_codes
    ):
        reasons.append("insufficient required metric coverage")
        reason_codes.append(RejectionReasonCode.LOW_METRIC_COVERAGE)
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
        passed, rejection_reasons, rejection_reason_codes, criterion_score = (
            _screen_candidate(
                candidate,
                program,
                policy,
            )
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
            RankingFactor.MANUFACTURABILITY.value: round(
                candidate.manufacturability_score, 4
            ),
            RankingFactor.LIABILITY.value: round(
                max(
                    0.0,
                    1.0 - (sum(flag.severity for flag in candidate.liabilities) / 10.0),
                ),
                4,
            ),
            RankingFactor.UNCERTAINTY.value: round(
                max(0.0, 1.0 - candidate.uncertainty), 4
            ),
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
                    flag.code
                    for flag in sorted(
                        candidate.liabilities, key=lambda item: item.code
                    )
                )
            )
        scored.append((candidate, score, reasons, factor_scores))

    ranked = sorted(
        scored,
        key=lambda item: (
            item[1],
            item[0].evidence_support
            if TieBreakRule.EVIDENCE_SUPPORT in policy.tie_break_rules
            else 0.0,
            item[0].manufacturability_score
            if TieBreakRule.MANUFACTURABILITY in policy.tie_break_rules
            else 0.0,
            -item[0].uncertainty
            if TieBreakRule.LOWER_UNCERTAINTY in policy.tie_break_rules
            else 0.0,
            -len(item[0].liabilities)
            if TieBreakRule.FEWER_LIABILITIES in policy.tie_break_rules
            else 0.0,
        ),
        reverse=True,
    )
    tie_breaks: list[TieBreakExplanation] = []
    for left, right in zip(ranked, ranked[1:], strict=False):
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
                    "blockers": [flag.summary for flag in candidate.liabilities[:3]],
                    "confidence": round(1.0 - candidate.uncertainty, 4),
                    "factor_scores": factor_scores,
                    "missing_evidence": [],
                },
            )
            for index, (candidate, score, reasons, factor_scores) in enumerate(
                ranked, start=1
            )
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
        raw_blockers = candidate.explainability.get("blockers", [])
        blockers = (
            [str(item) for item in raw_blockers]
            if isinstance(raw_blockers, list)
            else []
        )
        raw_strengths = candidate.explainability.get("top_drivers", [])
        strengths = (
            [str(item) for item in raw_strengths]
            if isinstance(raw_strengths, list)
            else []
        )
        missing_evidence = brief.evidence_gaps
        confidence_raw = candidate.explainability.get("confidence", 0.0)
        confidence = (
            float(confidence_raw) if isinstance(confidence_raw, (int, float)) else 0.0
        )
        if confidence >= 0.75:
            strengths.append(
                "assessment confidence remains high enough for active consideration"
            )
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
    raw_factor_scores = ranked_candidate.explainability.get("factor_scores", {})
    parsed_factor_scores: dict[str, float] = {}
    if isinstance(raw_factor_scores, dict):
        for key, value in raw_factor_scores.items():
            if isinstance(value, (int, float)):
                parsed_factor_scores[str(key)] = float(value)
    factor_scores = parsed_factor_scores
    weighted = {
        factor.value: round(
            factor_scores.get(factor.value, 0.0) * weight,
            4,
        )
        for factor, weight in policy.factor_weights.items()
    }
    base_score = round(sum(weighted.values()), 4)
    uncertainty_factor = factor_scores.get(RankingFactor.UNCERTAINTY.value, 1.0)
    uncertainty_penalty = round(
        (1.0 - uncertainty_factor) * policy.uncertainty_penalty_weight, 4
    )
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
        raw_blockers = candidate.explainability.get("blockers", [])
        blockers = (
            [str(item) for item in raw_blockers]
            if isinstance(raw_blockers, list)
            else []
        )
        for blocker in blockers:
            counts[blocker] = counts.get(blocker, 0) + 1
    top = sorted(counts, key=lambda code: counts[code], reverse=True)
    return LiabilityFocusSummary(
        liability_counts=counts,
        top_liabilities=top[:5],
    )


def summarize_uncertainty_pressure(
    ranking: CandidateRanking,
    *,
    confidence_floor: float = 0.65,
) -> UncertaintyPressureSummary:
    """Summarize confidence and uncertainty pressure across ranked candidates."""
    if not ranking.ranked_candidates:
        return UncertaintyPressureSummary(
            candidate_count=0,
            mean_confidence=0.0,
            low_confidence_candidate_ids=[],
            uncertainty_pressure_high=False,
        )
    confidence_by_candidate: dict[str, float] = {}
    for candidate in ranking.ranked_candidates:
        confidence_raw = candidate.explainability.get("confidence", 0.0)
        confidence_by_candidate[candidate.candidate_id] = (
            float(confidence_raw) if isinstance(confidence_raw, (int, float)) else 0.0
        )
    low_confidence = sorted(
        candidate_id
        for candidate_id, confidence in confidence_by_candidate.items()
        if confidence < confidence_floor
    )
    mean_confidence = round(
        sum(confidence_by_candidate.values()) / len(confidence_by_candidate),
        4,
    )
    return UncertaintyPressureSummary(
        candidate_count=len(ranking.ranked_candidates),
        mean_confidence=mean_confidence,
        low_confidence_candidate_ids=low_confidence,
        uncertainty_pressure_high=len(low_confidence)
        >= max(1, len(ranking.ranked_candidates) // 2),
    )


def summarize_novelty_diversity(
    ranking: CandidateRanking,
) -> NoveltyDiversitySummary:
    """Summarize diversity signals across ranked candidates."""
    if not ranking.ranked_candidates:
        return NoveltyDiversitySummary(
            candidate_count=0,
            unique_sequence_signatures=0,
            unique_liability_codes=0,
            diversity_score=0.0,
        )
    sequence_signatures = {
        candidate.candidate_id.split("-")[0] + f":{candidate.candidate_id[-1:]}"
        for candidate in ranking.ranked_candidates
    }
    liability_codes: set[str] = set()
    for candidate in ranking.ranked_candidates:
        blockers = candidate.explainability.get("blockers", [])
        if isinstance(blockers, list):
            for blocker in blockers:
                liability_codes.add(str(blocker))
    seq_ratio = len(sequence_signatures) / len(ranking.ranked_candidates)
    liability_ratio = len(liability_codes) / max(len(ranking.ranked_candidates), 1)
    diversity_score = round(min((seq_ratio * 0.5) + (liability_ratio * 0.5), 1.0), 4)
    return NoveltyDiversitySummary(
        candidate_count=len(ranking.ranked_candidates),
        unique_sequence_signatures=len(sequence_signatures),
        unique_liability_codes=len(liability_codes),
        diversity_score=diversity_score,
    )


def build_ranking_robustness_report(
    ranking: CandidateRanking,
) -> RankingRobustnessReport:
    """Build an integrated robustness report for ranked candidates."""
    uncertainty = summarize_uncertainty_pressure(ranking)
    diversity = summarize_novelty_diversity(ranking)
    robustness = round(
        max(
            0.0,
            min(
                (uncertainty.mean_confidence * 0.6) + (diversity.diversity_score * 0.4),
                1.0,
            ),
        ),
        4,
    )
    notes: list[str] = []
    if uncertainty.uncertainty_pressure_high:
        notes.append("confidence pressure is high across ranked candidates")
    if diversity.diversity_score < 0.5:
        notes.append(
            "candidate diversity is limited and may reduce portfolio resilience"
        )
    if not notes:
        notes.append("ranking appears robust for current decision stage")
    return RankingRobustnessReport(
        robustness_score=robustness,
        uncertainty_summary=uncertainty,
        diversity_summary=diversity,
        notes=notes,
    )


def summarize_metric_coverage(
    candidate: CandidateAssessment,
    program: ProgramSpec,
) -> MetricCoverageSummary:
    """Summarize metric completeness for one candidate against program criteria."""
    required_metrics = sorted(
        {criterion.metric for criterion in program.success_criteria}
    )
    provided_metrics = sorted(candidate.metric_scores.keys())
    missing_metrics = sorted(
        metric for metric in required_metrics if metric not in candidate.metric_scores
    )
    coverage_fraction = (
        round((len(required_metrics) - len(missing_metrics)) / len(required_metrics), 4)
        if required_metrics
        else 1.0
    )
    return MetricCoverageSummary(
        candidate_id=candidate.candidate_id,
        required_metrics=required_metrics,
        provided_metrics=provided_metrics,
        missing_metrics=missing_metrics,
        coverage_fraction=coverage_fraction,
    )


def criterion_satisfaction_vector(
    candidate: CandidateAssessment,
    program: ProgramSpec,
) -> CriterionSatisfactionVector:
    """Build per-criterion satisfaction vector for one candidate."""
    items: list[CriterionSatisfactionItem] = []
    satisfied_count = 0
    for criterion in program.success_criteria:
        observed = candidate.metric_scores.get(criterion.metric)
        if observed is None:
            satisfied = False
        elif criterion.direction is MeasurementDirection.MAXIMIZE:
            satisfied = observed >= criterion.threshold
        elif criterion.direction is MeasurementDirection.MINIMIZE:
            satisfied = observed <= criterion.threshold
        else:
            upper = (
                criterion.upper_threshold
                if criterion.upper_threshold is not None
                else criterion.threshold
            )
            lower = min(criterion.threshold, upper)
            higher = max(criterion.threshold, upper)
            satisfied = lower <= observed <= higher
        if satisfied:
            satisfied_count += 1
        items.append(
            CriterionSatisfactionItem(
                criterion_id=criterion.criterion_id,
                metric=criterion.metric,
                observed_value=observed,
                satisfied=satisfied,
            )
        )
    fraction = round((satisfied_count / len(items)), 4) if items else 1.0
    return CriterionSatisfactionVector(
        candidate_id=candidate.candidate_id,
        items=items,
        satisfied_fraction=fraction,
    )


def summarize_ranking_drift(
    previous: CandidateRanking,
    current: CandidateRanking,
) -> RankingDriftReport:
    """Summarize rank movement between previous and current ranking snapshots."""
    previous_rank = {
        item.candidate_id: item.rank for item in previous.ranked_candidates
    }
    current_rank = {item.candidate_id: item.rank for item in current.ranked_candidates}
    shared_ids = sorted(set(previous_rank).intersection(current_rank))
    moved: list[RankingDriftItem] = []
    for candidate_id in shared_ids:
        prev_rank = previous_rank[candidate_id]
        curr_rank = current_rank[candidate_id]
        if prev_rank != curr_rank:
            moved.append(
                RankingDriftItem(
                    candidate_id=candidate_id,
                    previous_rank=prev_rank,
                    current_rank=curr_rank,
                    rank_shift=prev_rank - curr_rank,
                )
            )
    newly_ranked = sorted(set(current_rank) - set(previous_rank))
    dropped = sorted(set(previous_rank) - set(current_rank))
    return RankingDriftReport(
        moved_candidates=moved,
        newly_ranked_candidate_ids=newly_ranked,
        dropped_candidate_ids=dropped,
    )


def build_ranking_diagnostics(
    ranking: CandidateRanking,
) -> RankingDiagnostics:
    """Build combined diagnostics for one ranking snapshot."""
    return RankingDiagnostics(
        robustness=build_ranking_robustness_report(ranking),
        rejection_summary=summarize_rejections(ranking.rejections),
    )
