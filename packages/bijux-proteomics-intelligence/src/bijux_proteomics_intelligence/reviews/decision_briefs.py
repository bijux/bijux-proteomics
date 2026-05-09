# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Decision-brief owners for intelligence recommendation surfaces."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_intelligence.candidates.lifecycle import CandidateRiskProfile
from bijux_proteomics_intelligence.candidates.ranking import (
    CandidateAssessment,
    CandidateRanking,
)
from bijux_proteomics_intelligence.judgment.recommendations import (
    DecisionEscalationFlags,
    FinalDecisionRecommendation,
    UnresolvedQuestionLedger,
    build_final_decision_recommendation,
    derive_decision_escalation_flags,
    summarize_unresolved_question_ledger,
)
from bijux_proteomics_intelligence.judgment.scenarios import (
    PortfolioDecisionReport,
    ScenarioDecisionConsensus,
    ScenarioSetEvaluation,
    evaluate_portfolio_balance,
    summarize_scenario_consensus,
)
from bijux_proteomics_intelligence.posture.evidence import (
    EvidenceContradictionSummary,
    summarize_evidence_contradictions,
)
from bijux_proteomics_knowledge.memory.models.evidence import EvidenceBundle
from bijux_proteomics_knowledge.references.workflows.briefings import (
    build_workflow_reference_briefing,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)


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


class ReviewBoardEvidenceLine(JsonModel):
    """One ranked evidence line for a scientific review board packet."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    rank: int | None = Field(default=None, ge=1)
    score: float = Field(...)
    evidence_support: float = Field(..., ge=0.0, le=1.0)
    contradiction_pressure: float = Field(..., ge=0.0, le=1.0)
    freshness_pressure: float = Field(..., ge=0.0, le=1.0)
    reasons: list[str] = Field(default_factory=list)
    qc_caveats: list[str] = Field(default_factory=list)
    next_step_proposals: list[str] = Field(default_factory=list)


class ReviewBoardPacket(JsonModel):
    """Review-board packet that keeps ranking, contradictions, and QC caveats aligned."""

    model_config = ConfigDict(extra="forbid")

    consensus: ScenarioDecisionConsensus = Field(...)
    recommendation: FinalDecisionRecommendation = Field(...)
    contradiction_summary: EvidenceContradictionSummary | None = Field(default=None)
    ranked_evidence: list[ReviewBoardEvidenceLine] = Field(default_factory=list)
    qc_caveats: list[str] = Field(default_factory=list)
    next_step_proposals: list[str] = Field(default_factory=list)
    data_says: str = Field(..., min_length=1)
    benchmark_allows: str = Field(..., min_length=1)
    literature_suggests: str = Field(..., min_length=1)
    we_still_do_not_know: tuple[str, ...] = Field(default_factory=tuple)


class AdvancedIntelligenceReviewPacket(JsonModel):
    """Review packet including escalation and uncertainty-ledger context."""

    model_config = ConfigDict(extra="forbid")

    base_packet: IntelligenceReviewPacket = Field(
        ..., description="Base intelligence decision brief."
    )
    escalation: DecisionEscalationFlags = Field(
        ..., description="Escalation flags for decision governance."
    )
    unresolved_questions: UnresolvedQuestionLedger = Field(
        ...,
        description="Deduplicated unresolved question ledger.",
    )


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
    scientific_value_delta: float = Field(default=0.0)
    assay_feasibility_delta: float = Field(default=0.0)
    novelty_delta: float = Field(default=0.0)
    lab_cost_efficiency_delta: float = Field(default=0.0)
    operational_reliability_delta: float = Field(default=0.0)
    rationale: list[str] = Field(default_factory=list)


def build_intelligence_review_packet(
    evaluations: ScenarioSetEvaluation,
    ranking: CandidateRanking,
    risks: list[CandidateRiskProfile],
) -> IntelligenceReviewPacket:
    """Build a decision brief from scenario and portfolio intelligence outputs."""

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


def _candidate_next_step_proposals(
    candidate: CandidateAssessment | None,
    ranked_candidate_reasons: list[str],
    qc_caveats: list[str],
    unresolved_questions: list[str],
    contradiction_pressure: float,
) -> list[str]:
    proposals: list[str] = []
    if candidate is not None and candidate.evidence_support < 0.6:
        proposals.append("collect stronger orthogonal evidence before advancement")
    if contradiction_pressure > 0.0:
        proposals.append("resolve conflicting evidence before making a strong claim")
    if qc_caveats:
        proposals.append("clear QC caveats before treating the ranking as decisive")
    if unresolved_questions:
        proposals.append("address the highest-frequency unresolved review questions")
    if not proposals and ranked_candidate_reasons:
        proposals.append(
            "advance the top-ranked follow-up while keeping rationale visible"
        )
    return sorted(dict.fromkeys(proposals))


def _build_claim_partition(
    *,
    ranking: CandidateRanking,
    evidence_bundle: EvidenceBundle | None,
    contradiction_summary: EvidenceContradictionSummary | None,
    unresolved_questions: list[str],
    workflow_family: KnowledgeWorkflowFamily | None,
) -> tuple[str, str, str, tuple[str, ...]]:
    top_candidate_id = (
        ranking.ranked_candidates[0].candidate_id
        if ranking.ranked_candidates
        else "no-ranked-candidate"
    )
    if evidence_bundle is None:
        data_says = "direct evidence was not attached to this decision brief"
    elif contradiction_summary is None:
        data_says = f"direct evidence was attached for {top_candidate_id}, but contradiction posture was not summarized"
    elif contradiction_summary.posture.value == "blocking":
        data_says = f"direct evidence remains contradictory for {top_candidate_id} and cannot support a clean recommendation"
    elif contradiction_summary.posture.value == "unresolved":
        data_says = f"direct evidence keeps {top_candidate_id} reviewable, but unresolved contradictions still weaken confidence"
    else:
        data_says = f"direct evidence currently supports {top_candidate_id} without explicit contradiction pressure"

    if workflow_family is None:
        benchmark_allows = "no workflow-family benchmark briefing was attached to bound this recommendation"
        literature_suggests = "no workflow-family literature briefing was attached to shape downstream interpretation"
        unknowns = tuple(unresolved_questions)
        return data_says, benchmark_allows, literature_suggests, unknowns

    briefing = build_workflow_reference_briefing(workflow_family)
    benchmark_allows = briefing.evidence_claim.narrative_text
    literature_suggests = (
        briefing.literature_groups[0].curation_note
        if briefing.literature_groups
        else briefing.limitation.narrative_text
    )
    unknowns = tuple(
        dict.fromkeys(
            [
                *unresolved_questions,
                *briefing.scope_limit_notes[:2],
            ]
        )
    )
    return data_says, benchmark_allows, literature_suggests, unknowns


def build_review_board_packet(
    evaluations: ScenarioSetEvaluation,
    ranking: CandidateRanking,
    assessments: list[CandidateAssessment],
    *,
    evidence_bundle: EvidenceBundle | None = None,
    qc_caveats: list[str] | tuple[str, ...] = (),
    workflow_family: KnowledgeWorkflowFamily | None = None,
) -> ReviewBoardPacket:
    """Build a review-board packet with ranked evidence, contradictions, and QC caveats."""

    consensus = summarize_scenario_consensus(evaluations)
    recommendation = build_final_decision_recommendation(
        evaluations,
        evidence_bundle=evidence_bundle,
        workflow_family=workflow_family,
    )
    contradiction_summary = (
        summarize_evidence_contradictions(evidence_bundle)
        if evidence_bundle is not None
        else None
    )
    assessment_map = {assessment.candidate_id: assessment for assessment in assessments}
    qc_caveat_list = sorted(
        {str(item).strip() for item in qc_caveats if str(item).strip()}
    )
    unresolved_ledger = summarize_unresolved_question_ledger(evaluations)
    data_says, benchmark_allows, literature_suggests, unknowns = _build_claim_partition(
        ranking=ranking,
        evidence_bundle=evidence_bundle,
        contradiction_summary=contradiction_summary,
        unresolved_questions=unresolved_ledger.prioritized_questions,
        workflow_family=workflow_family,
    )
    ranked_evidence: list[ReviewBoardEvidenceLine] = []
    for ranked_candidate in ranking.ranked_candidates[:5]:
        assessment = assessment_map.get(ranked_candidate.candidate_id)
        explainability = ranked_candidate.explainability
        contradiction_pressure = float(
            explainability.get("contradiction_pressure", 0.0)
        )
        freshness_pressure = float(explainability.get("freshness_pressure", 0.0))
        ranked_reasons = [str(reason) for reason in ranked_candidate.reasons[:4]]
        ranked_evidence.append(
            ReviewBoardEvidenceLine(
                candidate_id=ranked_candidate.candidate_id,
                rank=ranked_candidate.rank,
                score=ranked_candidate.score,
                evidence_support=(
                    assessment.evidence_support if assessment is not None else 0.0
                ),
                contradiction_pressure=contradiction_pressure,
                freshness_pressure=freshness_pressure,
                reasons=ranked_reasons,
                qc_caveats=qc_caveat_list,
                next_step_proposals=_candidate_next_step_proposals(
                    assessment,
                    ranked_reasons,
                    qc_caveat_list,
                    unresolved_ledger.prioritized_questions,
                    contradiction_pressure,
                ),
            )
        )
    next_step_proposals = sorted(
        dict.fromkeys(
            proposal
            for line in ranked_evidence
            for proposal in line.next_step_proposals
        )
    )
    if recommendation.gate_result is not None and recommendation.gate_result.refusal:
        next_step_proposals.append(recommendation.gate_result.refusal.reason)
    return ReviewBoardPacket(
        consensus=consensus,
        recommendation=recommendation,
        contradiction_summary=contradiction_summary,
        ranked_evidence=ranked_evidence,
        qc_caveats=qc_caveat_list,
        next_step_proposals=sorted(dict.fromkeys(next_step_proposals)),
        data_says=data_says,
        benchmark_allows=benchmark_allows,
        literature_suggests=literature_suggests,
        we_still_do_not_know=unknowns,
    )


def _candidate_multi_objective_profile(
    ranking: CandidateRanking,
    candidate_id: str,
) -> dict[str, float]:
    for candidate in ranking.ranked_candidates:
        if candidate.candidate_id != candidate_id:
            continue
        raw = candidate.explainability.get("multi_objective_profile", {})
        if not isinstance(raw, dict):
            return {}
        return {
            str(key): float(value)
            for key, value in raw.items()
            if isinstance(value, (int, float))
        }
    return {}


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
    preferred_profile = _candidate_multi_objective_profile(
        ranking, preferred_candidate_id
    )
    compared_profile = _candidate_multi_objective_profile(
        ranking, compared_candidate_id
    )
    scientific_value_delta = round(
        preferred_profile.get("scientific_value", 0.0)
        - compared_profile.get("scientific_value", 0.0),
        4,
    )
    assay_feasibility_delta = round(
        preferred_profile.get("assay_feasibility", 0.0)
        - compared_profile.get("assay_feasibility", 0.0),
        4,
    )
    novelty_delta = round(
        preferred_profile.get("novelty", 0.0) - compared_profile.get("novelty", 0.0),
        4,
    )
    lab_cost_efficiency_delta = round(
        preferred_profile.get("lab_cost_efficiency", 0.0)
        - compared_profile.get("lab_cost_efficiency", 0.0),
        4,
    )
    operational_reliability_delta = round(
        preferred_profile.get("operational_reliability", 0.0)
        - compared_profile.get("operational_reliability", 0.0),
        4,
    )
    rationale = [
        f"score delta = {preferred.score - compared.score:.4f}",
        f"evidence support delta = {preferred_assessment.evidence_support - compared_assessment.evidence_support:.4f}",
        f"residual risk delta = {compared_residual_risk - preferred_residual_risk:.4f}",
        f"scientific value delta = {scientific_value_delta:.4f}",
        f"assay feasibility delta = {assay_feasibility_delta:.4f}",
    ]
    if preferred.score <= compared.score:
        rationale.append(
            "preferred candidate is being justified despite a non-positive score delta"
        )
    if novelty_delta > 0:
        rationale.append(
            f"preferred candidate preserves more differentiated learning value ({novelty_delta:.4f})"
        )
    if lab_cost_efficiency_delta < 0 or operational_reliability_delta < 0:
        rationale.append(
            "preferred candidate carries higher operational cost or fragility and needs explicit justification"
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
        scientific_value_delta=scientific_value_delta,
        assay_feasibility_delta=assay_feasibility_delta,
        novelty_delta=novelty_delta,
        lab_cost_efficiency_delta=lab_cost_efficiency_delta,
        operational_reliability_delta=operational_reliability_delta,
        rationale=rationale,
    )


def build_advanced_review_packet(
    evaluations: ScenarioSetEvaluation,
    ranking: CandidateRanking,
    risks: list[CandidateRiskProfile],
) -> AdvancedIntelligenceReviewPacket:
    """Build advanced decision brief with escalation and unresolved question ledger."""

    base = build_intelligence_review_packet(evaluations, ranking, risks)
    escalation = derive_decision_escalation_flags(evaluations)
    ledger = summarize_unresolved_question_ledger(evaluations)
    return AdvancedIntelligenceReviewPacket(
        base_packet=base,
        escalation=escalation,
        unresolved_questions=ledger,
    )
