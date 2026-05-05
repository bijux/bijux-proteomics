# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""End-to-end decision paths that keep recommendations readable and explicit."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.programs import ProgramSpec
from bijux_proteomics_foundation import JsonModel, ProgramId
from bijux_proteomics_intelligence.briefs import (
    CandidateAssessment,
    CandidateRanking,
    RankingPolicy,
    build_design_brief,
    prioritize_candidates,
    summarize_candidate_explainability,
)
from bijux_proteomics_knowledge import (
    DecisionReadiness,
    EvidenceBundle,
    assess_decision_readiness,
)
from bijux_proteomics_knowledge.references import KnowledgeWorkflowFamily


class FollowUpCandidateRecommendation(JsonModel):
    """Scientist-facing follow-up recommendation for one ranked candidate."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    rank: int = Field(..., ge=1)
    score: float
    recommendation: str = Field(..., min_length=1)
    explanation: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    next_step_proposals: list[str] = Field(default_factory=list)


class FollowUpCandidatePath(JsonModel):
    """End-to-end path from normalized evidence to ranked follow-up candidates."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    workflow_family: KnowledgeWorkflowFamily | None = Field(default=None)
    decision_ready: bool = Field(
        ..., description="Whether current evidence is decision-ready."
    )
    readiness: DecisionReadiness = Field(
        ..., description="Decision-readiness assessment over the evidence bundle."
    )
    ranking: CandidateRanking = Field(
        ..., description="Transparent ranking produced from the evidence bundle."
    )
    recommendations: list[FollowUpCandidateRecommendation] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)


def _required_evidence_kinds(program: ProgramSpec) -> list[str]:
    required = [need.value for need in program.evidence_needs]
    return required or ["literature", "assay"]


def _dedupe_nonblank(values: list[str]) -> list[str]:
    return sorted({value.strip() for value in values if value.strip()})


def _next_step_proposals(questions: list[str]) -> list[str]:
    proposals: list[str] = []
    for question in questions:
        if question.startswith("missing required evidence kinds: "):
            suffix = question.removeprefix("missing required evidence kinds: ")
            proposals.append(f"collect {suffix} evidence before candidate signoff")
        elif question.startswith("mean confidence "):
            proposals.append("replace exploratory evidence with stronger corroboration")
        elif question.startswith("not enough decisive evidence"):
            proposals.append("add decisive assay or structural evidence")
        else:
            proposals.append(f"resolve: {question}")
    return _dedupe_nonblank(proposals)


def build_follow_up_candidate_path(
    program: ProgramSpec,
    assessments: list[CandidateAssessment],
    evidence_bundle: EvidenceBundle,
    *,
    workflow_family: KnowledgeWorkflowFamily | None = None,
    ranking_policy: RankingPolicy | None = None,
) -> FollowUpCandidatePath:
    """Build a readable follow-up candidate path from evidence to ranking output."""
    readiness = assess_decision_readiness(
        evidence_bundle,
        _required_evidence_kinds(program),
    )
    ranking = prioritize_candidates(
        program,
        assessments,
        ranking_policy,
        evidence_bundle=evidence_bundle,
        workflow_family=workflow_family,
    )
    design_brief = build_design_brief(program, evidence_bundle)
    explainability_map = {
        summary.candidate_id: summary
        for summary in summarize_candidate_explainability(ranking, design_brief)
    }

    recommendations: list[FollowUpCandidateRecommendation] = []
    unresolved_questions = list(readiness.blockers)
    for ranked_candidate in ranking.ranked_candidates:
        summary = explainability_map.get(ranked_candidate.candidate_id)
        candidate_questions = []
        if summary is not None:
            candidate_questions.extend(summary.open_risks)
            candidate_questions.extend(summary.evidence_gaps)
        candidate_questions = _dedupe_nonblank(candidate_questions)
        unresolved_questions.extend(candidate_questions)
        explanation = list(ranked_candidate.reasons[:4])
        if summary is not None:
            explanation.extend(summary.strengths[:2])
        recommendation = (
            f"prioritize {ranked_candidate.candidate_id} for follow-up review"
            if not candidate_questions
            else f"advance {ranked_candidate.candidate_id} only with explicit blocker review"
        )
        recommendations.append(
            FollowUpCandidateRecommendation(
                candidate_id=ranked_candidate.candidate_id,
                rank=ranked_candidate.rank,
                score=ranked_candidate.score,
                recommendation=recommendation,
                explanation=_dedupe_nonblank(explanation),
                unresolved_questions=candidate_questions,
                next_step_proposals=_next_step_proposals(
                    list(readiness.blockers) + candidate_questions
                ),
            )
        )

    return FollowUpCandidatePath(
        program_id=program.program_id,
        workflow_family=workflow_family,
        decision_ready=readiness.ready,
        readiness=readiness,
        ranking=ranking,
        recommendations=recommendations,
        unresolved_questions=_dedupe_nonblank(unresolved_questions),
    )


__all__ = [
    "FollowUpCandidatePath",
    "FollowUpCandidateRecommendation",
    "build_follow_up_candidate_path",
]
