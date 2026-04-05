# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Design briefs and candidate ranking for protein programs."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.programs import MeasurementDirection, ProgramSpec
from bijux_proteomics_knowledge import EvidenceBundle, evidence_gaps
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

    program_id: str = Field(..., min_length=1, description="Program identifier.")
    target_id: str = Field(..., min_length=1, description="Target identifier.")
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

    candidate_id: str = Field(..., min_length=1, description="Stable candidate identifier.")
    sequence: str = Field(..., min_length=1, description="Candidate protein sequence.")
    metric_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Observed or predicted metrics keyed by metric name.",
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

    candidate_id: str = Field(..., min_length=1, description="Stable candidate identifier.")
    score: float = Field(..., description="Composite ranking score.")
    rank: int = Field(..., ge=1, description="Position in the ordered list.")
    reasons: list[str] = Field(
        default_factory=list,
        description="Short explanations for the ranking outcome.",
    )


class CandidateRanking(JsonModel):
    """Ordered candidate list for a program."""

    model_config = ConfigDict(extra="forbid")

    program_id: str = Field(..., min_length=1, description="Program identifier.")
    ranked_candidates: list[RankedCandidate] = Field(
        default_factory=list,
        description="Candidates ordered from strongest to weakest.",
    )
    rejected_candidates: list[str] = Field(
        default_factory=list,
        description="Candidates screened out for missing minimum requirements.",
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


def prioritize_candidates(
    program: ProgramSpec,
    candidates: list[CandidateAssessment],
) -> CandidateRanking:
    """Rank candidates with transparent penalties for risk and weak support."""
    scored: list[tuple[CandidateAssessment, float, list[str]]] = []
    rejected: list[str] = []
    for candidate in candidates:
        criterion_score = _criterion_score(candidate, program)
        if program.success_criteria and criterion_score <= 0:
            rejected.append(candidate.candidate_id)
            continue
        liability_penalty = sum(flag.severity for flag in candidate.liabilities) * 0.15
        support_bonus = candidate.evidence_support * 0.5
        score = criterion_score + support_bonus - liability_penalty
        reasons = [
            f"criteria_score={criterion_score:.2f}",
            f"evidence_support={candidate.evidence_support:.2f}",
        ]
        if candidate.liabilities:
            reasons.append(
                "liabilities="
                + ",".join(
                    flag.code for flag in sorted(candidate.liabilities, key=lambda item: item.code)
                )
            )
        scored.append((candidate, score, reasons))

    ranked = sorted(scored, key=lambda item: item[1], reverse=True)
    return CandidateRanking(
        program_id=program.program_id,
        ranked_candidates=[
            RankedCandidate(
                candidate_id=candidate.candidate_id,
                score=round(score, 4),
                rank=index,
                reasons=reasons,
            )
            for index, (candidate, score, reasons) in enumerate(ranked, start=1)
        ],
        rejected_candidates=rejected,
    )
