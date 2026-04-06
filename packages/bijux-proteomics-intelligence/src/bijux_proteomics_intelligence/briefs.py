# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Design briefs and candidate ranking for protein programs."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.programs import MeasurementDirection, ProgramSpec
from bijux_proteomics_foundation import CandidateId, ProgramId, TargetId
from bijux_proteomics_knowledge import EvidenceBundle, evidence_gaps
from bijux_proteomics_intelligence.outcomes import CandidateRejection, TieBreakExplanation
from bijux_proteomics_intelligence.policies import RankingFactor, RankingPolicy, TieBreakRule
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


def _metric_weight_name(metric: str) -> OptimizationAxis:
    lowered = metric.lower()
    if "affin" in lowered or "bind" in lowered:
        return OptimizationAxis.AFFINITY
    if "stabil" in lowered or "tm" in lowered or "fold" in lowered:
        return OptimizationAxis.STABILITY
    if "specif" in lowered or "off-target" in lowered:
        return OptimizationAxis.SPECIFICITY
    if "tox" in lowered or "immun" in lowered or "safety" in lowered:
        return OptimizationAxis.SAFETY
    if "yield" in lowered or "express" in lowered or "aggregation" in lowered:
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
) -> tuple[bool, list[str], float]:
    criterion_score = _criterion_score(candidate, program)
    threshold_count = max(len(program.success_criteria), 1)
    mean_fraction = criterion_score / threshold_count
    reasons: list[str] = []

    if program.success_criteria and mean_fraction < profile.minimum_metric_fraction:
        reasons.append("below minimum criterion fraction")
    if candidate.evidence_support < profile.minimum_evidence_support:
        reasons.append("insufficient evidence support")
    if (
        profile.require_manufacturability_floor
        and candidate.manufacturability_score < profile.manufacturability_floor
    ):
        reasons.append("below manufacturability floor")
    return (not reasons, reasons, criterion_score)


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
        passed, rejection_reasons, criterion_score = _screen_candidate(
            candidate,
            program,
            policy,
        )
        if not passed:
            rejected.append(candidate.candidate_id)
            rejections.append(
                CandidateRejection(
                    candidate_id=candidate.candidate_id,
                    reasons=rejection_reasons,
                )
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
