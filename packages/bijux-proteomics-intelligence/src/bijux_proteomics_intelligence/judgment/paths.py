# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""End-to-end decision paths that keep recommendations readable and explicit."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.program_spec import ProgramSpec
from bijux_proteomics.lab.qc import InstrumentBatchQcReport
from bijux_proteomics.quantification import ReplicateCorrelationReport
from bijux_proteomics_foundation import JsonModel, ProgramId
from bijux_proteomics_intelligence.candidates.lifecycle import (
    CandidateRiskProfile,
    build_risk_profile,
)
from bijux_proteomics_intelligence.candidates.ranking import (
    CandidateAssessment,
    CandidateRanking,
    build_design_brief,
    prioritize_candidates,
    summarize_candidate_explainability,
)
from bijux_proteomics_intelligence.interpretation import (
    OutlierInterpretationClass,
    explain_outlier_samples,
)
from bijux_proteomics_intelligence.judgment.policies import RankingPolicy
from bijux_proteomics_intelligence.judgment.recommendations import (
    summarize_unresolved_question_ledger,
)
from bijux_proteomics_intelligence.judgment.scenarios import (
    EvaluatorPolicyBundle,
    ScenarioSetEvaluation,
    evaluate_all_scenarios,
)
from bijux_proteomics_intelligence.reviews.decision_briefs import (
    ReviewBoardPacket,
    build_review_board_packet,
)
from bijux_proteomics_knowledge.memory.models.evidence import (
    DecisionReadiness,
    EvidenceBundle,
    assess_decision_readiness,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)


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


class ReviewBoardDecisionPath(JsonModel):
    """End-to-end path from normalized evidence to a review-board packet."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    workflow_family: KnowledgeWorkflowFamily | None = Field(default=None)
    follow_up_path: FollowUpCandidatePath = Field(
        ..., description="Readable follow-up candidate path."
    )
    risks: list[CandidateRiskProfile] = Field(default_factory=list)
    evaluations: ScenarioSetEvaluation = Field(
        ..., description="Scenario evaluations over the same evidence state."
    )
    packet: ReviewBoardPacket = Field(
        ..., description="Review-board packet aligned with ranking and evidence."
    )
    recommendation: str = Field(..., min_length=1)
    explanation: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)


class AnomalyInterpretationRecommendation(JsonModel):
    """Cautious interpretation output for one observed anomaly."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    classification: OutlierInterpretationClass
    recommendation: str = Field(..., min_length=1)
    explanation: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)


class CautiousAnomalyInterpretationPath(JsonModel):
    """End-to-end path from observed anomalies to cautious interpretation."""

    model_config = ConfigDict(extra="forbid")

    interpretation_count: int = Field(..., ge=0)
    overall_recommendation: str = Field(..., min_length=1)
    interpretations: list[AnomalyInterpretationRecommendation] = Field(
        default_factory=list
    )
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


def build_review_board_decision_path(
    program: ProgramSpec,
    assessments: list[CandidateAssessment],
    evidence_bundle: EvidenceBundle,
    *,
    workflow_family: KnowledgeWorkflowFamily | None = None,
    ranking_policy: RankingPolicy | None = None,
    evaluator_policies: EvaluatorPolicyBundle | None = None,
) -> ReviewBoardDecisionPath:
    """Build a review-board packet from normalized evidence and candidate inputs."""
    follow_up_path = build_follow_up_candidate_path(
        program,
        assessments,
        evidence_bundle,
        workflow_family=workflow_family,
        ranking_policy=ranking_policy,
    )
    risks = [build_risk_profile(assessment) for assessment in assessments]
    evaluations = evaluate_all_scenarios(
        program,
        follow_up_path.ranking,
        follow_up_path.readiness,
        risks,
        policies=evaluator_policies,
    )
    packet = build_review_board_packet(
        evaluations,
        follow_up_path.ranking,
        assessments,
        evidence_bundle=evidence_bundle,
        qc_caveats=follow_up_path.readiness.blockers,
        workflow_family=workflow_family,
    )
    unresolved = _dedupe_nonblank(
        follow_up_path.unresolved_questions
        + summarize_unresolved_question_ledger(evaluations).prioritized_questions
    )
    if (
        not unresolved
        and packet.recommendation.gate_result is not None
        and packet.recommendation.gate_result.refusal is not None
    ):
        unresolved = _dedupe_nonblank(
            [
                packet.recommendation.gate_result.refusal.reason,
                *packet.recommendation.gate_result.refusal.reason_details,
            ]
        )
    return ReviewBoardDecisionPath(
        program_id=program.program_id,
        workflow_family=workflow_family,
        follow_up_path=follow_up_path,
        risks=risks,
        evaluations=evaluations,
        packet=packet,
        recommendation=(
            f"{packet.recommendation.action.value.replace('_', ' ')} via review-board review"
        ),
        explanation=_dedupe_nonblank(
            packet.recommendation.reasons[:4] + packet.next_step_proposals[:3]
        ),
        unresolved_questions=unresolved,
    )


def build_cautious_anomaly_interpretation_path(
    batch_report: InstrumentBatchQcReport,
    replicate_report: ReplicateCorrelationReport,
    *,
    low_correlation_threshold: float = 0.85,
) -> CautiousAnomalyInterpretationPath:
    """Build cautious interpretation outputs from observed anomaly signals."""
    explanations = explain_outlier_samples(
        batch_report,
        replicate_report,
        low_correlation_threshold=low_correlation_threshold,
    )
    interpretations: list[AnomalyInterpretationRecommendation] = []
    unresolved_questions: list[str] = []

    for explanation in explanations:
        if explanation.classification is OutlierInterpretationClass.TECHNICAL_ANOMALY:
            recommendation = (
                "hold biological interpretation until the technical anomaly is resolved"
            )
            questions = ["root cause of the technical anomaly remains unresolved"]
        elif explanation.classification is OutlierInterpretationClass.MIXED_SIGNAL:
            recommendation = "treat the anomaly as unresolved until orthogonal evidence separates technical and biological signal"
            questions = [
                "orthogonal evidence must separate technical artifact from biological effect"
            ]
        else:
            recommendation = "preserve the anomaly for biological follow-up with orthogonal confirmation"
            questions = ["orthogonal evidence should confirm the biological separation"]
        unresolved_questions.extend(questions)
        interpretations.append(
            AnomalyInterpretationRecommendation(
                sample_id=explanation.sample_id,
                classification=explanation.classification,
                recommendation=recommendation,
                explanation=_dedupe_nonblank(
                    list(explanation.reasons)
                    + list(explanation.technical_reasons)
                    + list(explanation.biological_reasons)
                ),
                unresolved_questions=questions,
            )
        )

    if any(
        entry.classification is OutlierInterpretationClass.TECHNICAL_ANOMALY
        for entry in interpretations
    ):
        overall = (
            "hold mechanistic interpretation until technical anomalies are resolved"
        )
    elif any(
        entry.classification is OutlierInterpretationClass.MIXED_SIGNAL
        for entry in interpretations
    ):
        overall = "treat observed anomalies as unresolved until orthogonal evidence reduces ambiguity"
    else:
        overall = (
            "preserve observed anomalies for biological follow-up with explicit caution"
        )

    return CautiousAnomalyInterpretationPath(
        interpretation_count=len(interpretations),
        overall_recommendation=overall,
        interpretations=interpretations,
        unresolved_questions=_dedupe_nonblank(unresolved_questions),
    )


__all__ = [
    "AnomalyInterpretationRecommendation",
    "CautiousAnomalyInterpretationPath",
    "FollowUpCandidatePath",
    "FollowUpCandidateRecommendation",
    "ReviewBoardDecisionPath",
    "build_cautious_anomaly_interpretation_path",
    "build_follow_up_candidate_path",
    "build_review_board_decision_path",
]
