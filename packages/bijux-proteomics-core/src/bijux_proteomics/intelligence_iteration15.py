# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Intelligence and review production surfaces for iteration 15."""

from __future__ import annotations

from enum import StrEnum
import hashlib
import json

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class EnrichmentCorrectionMethod(StrEnum):
    """Multiple-testing correction method for enrichment analyses."""

    BENJAMINI_HOCHBERG = "benjamini_hochberg"
    BONFERRONI = "bonferroni"
    NONE = "none"


class EnrichmentBackgroundProvenance(JsonModel):
    """Background and statistical provenance for one enrichment output."""

    model_config = ConfigDict(extra="forbid")

    analysis_id: str = Field(..., min_length=1)
    universe_id: str = Field(..., min_length=1)
    filter_expression: str = Field(..., min_length=1)
    statistical_test: str = Field(..., min_length=1)
    correction_method: EnrichmentCorrectionMethod
    input_evidence_ids: tuple[str, ...] = Field(default_factory=tuple)
    notes: tuple[str, ...] = Field(default_factory=tuple)


def build_enrichment_background_provenance(
    *,
    analysis_id: str,
    universe_id: str,
    filter_expression: str,
    statistical_test: str,
    correction_method: EnrichmentCorrectionMethod,
    input_evidence_ids: tuple[str, ...],
    notes: tuple[str, ...] = (),
) -> EnrichmentBackgroundProvenance:
    """Record universe, filter, test, correction, and evidence provenance."""

    if not input_evidence_ids:
        raise ValueError("enrichment provenance requires input evidence pointers")

    return EnrichmentBackgroundProvenance(
        analysis_id=analysis_id,
        universe_id=universe_id,
        filter_expression=filter_expression,
        statistical_test=statistical_test,
        correction_method=correction_method,
        input_evidence_ids=tuple(sorted(set(input_evidence_ids))),
        notes=tuple(sorted(set(notes))),
    )


class PathwayInterpretationState(StrEnum):
    """Interpretation class for pathway/network outputs."""

    EXPLORATORY = "exploratory"
    SUPPORTED = "supported"
    MECHANISTIC_CLAIM_REFUSED = "mechanistic_claim_refused"


class PathwayCautionIssue(JsonModel):
    """Caution issue attached to one pathway interpretation output."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class PathwayCautionReport(JsonModel):
    """Caution model separating exploratory interpretation from mechanism claims."""

    model_config = ConfigDict(extra="forbid")

    pathway_id: str = Field(..., min_length=1)
    interpretation_state: PathwayInterpretationState
    supporting_evidence_count: int = Field(..., ge=0)
    contradiction_count: int = Field(..., ge=0)
    issue_list: tuple[PathwayCautionIssue, ...] = Field(default_factory=tuple)


def build_pathway_network_caution_report(
    *,
    pathway_id: str,
    supporting_evidence_count: int,
    contradiction_count: int,
    claims_mechanistic_truth: bool,
) -> PathwayCautionReport:
    """Classify pathway/network interpretation while refusing unsupported mechanism claims."""

    issues: list[PathwayCautionIssue] = []
    if supporting_evidence_count < 2:
        issues.append(
            PathwayCautionIssue(
                code="limited_support",
                message="pathway interpretation is based on sparse evidence",
            )
        )
    if contradiction_count > 0:
        issues.append(
            PathwayCautionIssue(
                code="contradicted",
                message="pathway evidence contains unresolved contradictions",
            )
        )
    if claims_mechanistic_truth and (
        supporting_evidence_count < 4 or contradiction_count > 0
    ):
        issues.append(
            PathwayCautionIssue(
                code="mechanistic_overreach",
                message="mechanistic claim refused without convergent contradiction-free evidence",
            )
        )
        state = PathwayInterpretationState.MECHANISTIC_CLAIM_REFUSED
    elif supporting_evidence_count >= 4 and contradiction_count == 0:
        state = PathwayInterpretationState.SUPPORTED
    else:
        state = PathwayInterpretationState.EXPLORATORY

    return PathwayCautionReport(
        pathway_id=pathway_id,
        interpretation_state=state,
        supporting_evidence_count=supporting_evidence_count,
        contradiction_count=contradiction_count,
        issue_list=tuple(issues),
    )


class QuantOutlierObservation(JsonModel):
    """Observed quant outlier bound to run/sample/protein context."""

    model_config = ConfigDict(extra="forbid")

    outlier_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    protein_id: str = Field(..., min_length=1)
    z_score: float
    batch_id: str = Field(..., min_length=1)


class RunQcSummaryLink(JsonModel):
    """QC linkage for one run."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    qc_disposition: str = Field(..., min_length=1)
    qc_issue_codes: tuple[str, ...] = Field(default_factory=tuple)


class OutlierQcIntegratedEntry(JsonModel):
    """One outlier with integrated QC and batch/sample metadata context."""

    model_config = ConfigDict(extra="forbid")

    outlier_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    protein_id: str = Field(..., min_length=1)
    batch_id: str = Field(..., min_length=1)
    z_score: float
    qc_disposition: str = Field(..., min_length=1)
    qc_issue_codes: tuple[str, ...] = Field(default_factory=tuple)
    triage_priority: int = Field(..., ge=1, le=3)


class OutlierQcIntegratedReport(JsonModel):
    """Outlier analysis integrated with quant, QC, batch, and sample metadata."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[OutlierQcIntegratedEntry, ...] = Field(default_factory=tuple)


def build_outlier_qc_integrated_report(
    *,
    outliers: tuple[QuantOutlierObservation, ...],
    qc_summaries: tuple[RunQcSummaryLink, ...],
) -> OutlierQcIntegratedReport:
    """Connect outliers to run QC summaries, batch assignment, and sample-level metadata."""

    qc_by_run = {summary.run_id: summary for summary in qc_summaries}
    entries: list[OutlierQcIntegratedEntry] = []

    for outlier in outliers:
        qc = qc_by_run.get(outlier.run_id)
        if qc is None:
            qc_disposition = "unknown"
            qc_issue_codes: tuple[str, ...] = ()
            triage_priority = 3
        else:
            qc_disposition = qc.qc_disposition
            qc_issue_codes = qc.qc_issue_codes
            if qc.qc_disposition in {"failed", "refused"}:
                triage_priority = 1
            elif abs(outlier.z_score) >= 3.0 or qc_issue_codes:
                triage_priority = 2
            else:
                triage_priority = 3

        entries.append(
            OutlierQcIntegratedEntry(
                outlier_id=outlier.outlier_id,
                sample_id=outlier.sample_id,
                run_id=outlier.run_id,
                protein_id=outlier.protein_id,
                batch_id=outlier.batch_id,
                z_score=outlier.z_score,
                qc_disposition=qc_disposition,
                qc_issue_codes=qc_issue_codes,
                triage_priority=triage_priority,
            )
        )

    entries.sort(key=lambda entry: (entry.triage_priority, entry.outlier_id))
    return OutlierQcIntegratedReport(entries=tuple(entries))


class EvidenceGraphCandidate(JsonModel):
    """Candidate projection from the evidence graph for prioritization."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    evidence_strength: float = Field(..., ge=0.0, le=1.0)
    novelty_score: float = Field(..., ge=0.0, le=1.0)
    lab_feasibility: float = Field(..., ge=0.0, le=1.0)
    risk_score: float = Field(..., ge=0.0, le=1.0)
    missing_evidence_penalty: float = Field(..., ge=0.0, le=1.0)


class CandidatePriorityEntry(JsonModel):
    """Prioritization entry for one evidence-graph candidate."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    priority_score: float = Field(..., ge=0.0)
    rank: int = Field(..., ge=1)


class CandidatePriorityReport(JsonModel):
    """Candidate ranking by evidence strength, novelty, feasibility, and risk."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[CandidatePriorityEntry, ...] = Field(default_factory=tuple)


def prioritize_candidates_from_evidence_graph(
    candidates: tuple[EvidenceGraphCandidate, ...],
) -> CandidatePriorityReport:
    """Rank candidates from evidence graph features without hiding risk penalties."""

    if not candidates:
        return CandidatePriorityReport(entries=())

    scored = [
        (
            candidate.candidate_id,
            0.35 * candidate.evidence_strength
            + 0.2 * candidate.novelty_score
            + 0.25 * candidate.lab_feasibility
            + 0.1 * (1.0 - candidate.risk_score)
            + 0.1 * (1.0 - candidate.missing_evidence_penalty),
        )
        for candidate in candidates
    ]
    scored.sort(key=lambda item: (-item[1], item[0]))

    entries = tuple(
        CandidatePriorityEntry(
            candidate_id=candidate_id, priority_score=score, rank=index + 1
        )
        for index, (candidate_id, score) in enumerate(scored)
    )
    return CandidatePriorityReport(entries=entries)


class MultiObjectiveRankingInput(JsonModel):
    """Candidate objective inputs for multi-objective ranking."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    evidence_score: float = Field(..., ge=0.0, le=1.0)
    novelty_score: float = Field(..., ge=0.0, le=1.0)
    lab_feasibility_score: float = Field(..., ge=0.0, le=1.0)
    cost_penalty: float = Field(..., ge=0.0, le=1.0)
    risk_penalty: float = Field(..., ge=0.0, le=1.0)
    expected_gain_score: float = Field(..., ge=0.0, le=1.0)


class MultiObjectiveRankingEntry(JsonModel):
    """Multi-objective score and ranking result for one candidate."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    objective_score: float
    rank: int = Field(..., ge=1)


class MultiObjectiveRankingReport(JsonModel):
    """Ranking report across evidence, novelty, feasibility, cost, risk, and gain."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[MultiObjectiveRankingEntry, ...] = Field(default_factory=tuple)


def build_multi_objective_ranking_report(
    candidates: tuple[MultiObjectiveRankingInput, ...],
) -> MultiObjectiveRankingReport:
    """Rank candidates across weighted objectives while keeping penalties explicit."""

    scored = [
        (
            candidate.candidate_id,
            0.24 * candidate.evidence_score
            + 0.14 * candidate.novelty_score
            + 0.2 * candidate.lab_feasibility_score
            + 0.22 * candidate.expected_gain_score
            + 0.1 * (1.0 - candidate.cost_penalty)
            + 0.1 * (1.0 - candidate.risk_penalty),
        )
        for candidate in candidates
    ]
    scored.sort(key=lambda item: (-item[1], item[0]))
    return MultiObjectiveRankingReport(
        entries=tuple(
            MultiObjectiveRankingEntry(
                candidate_id=candidate_id,
                objective_score=score,
                rank=index + 1,
            )
            for index, (candidate_id, score) in enumerate(scored)
        )
    )


class RankingPolicyRule(JsonModel):
    """One ranking policy rule for inspectable scoring behavior."""

    model_config = ConfigDict(extra="forbid")

    metric: str = Field(..., min_length=1)
    weight: float = Field(..., ge=0.0)
    transform: str = Field(default="identity", min_length=1)
    direction: str = Field(default="maximize", pattern=r"^(maximize|minimize)$")


class RankingPolicyLanguageDocument(JsonModel):
    """Versioned and inspectable ranking policy language document."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(..., min_length=1)
    policy_version: str = Field(..., min_length=1)
    rules: tuple[RankingPolicyRule, ...] = Field(default_factory=tuple)
    policy_digest: str = Field(..., min_length=64, max_length=64)


def build_ranking_policy_language_document(
    *,
    policy_id: str,
    policy_version: str,
    rules: tuple[RankingPolicyRule, ...],
) -> RankingPolicyLanguageDocument:
    """Build canonical versioned ranking policy with reproducible digest."""

    if not rules:
        raise ValueError("ranking policy requires at least one rule")
    total_weight = sum(rule.weight for rule in rules)
    if total_weight <= 0.0:
        raise ValueError("ranking policy total weight must be positive")

    normalized_rules = tuple(
        sorted(
            (
                RankingPolicyRule(
                    metric=rule.metric,
                    weight=rule.weight / total_weight,
                    transform=rule.transform,
                    direction=rule.direction,
                )
                for rule in rules
            ),
            key=lambda rule: (rule.metric, rule.direction, rule.transform),
        )
    )
    digest = hashlib.sha256(
        json.dumps(
            {
                "policy_id": policy_id,
                "policy_version": policy_version,
                "rules": [rule.model_dump(mode="json") for rule in normalized_rules],
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    return RankingPolicyLanguageDocument(
        policy_id=policy_id,
        policy_version=policy_version,
        rules=normalized_rules,
        policy_digest=digest,
    )


class CandidateComparisonInput(JsonModel):
    """Scored candidate inputs used to explain ranking differences."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    rank: int = Field(..., ge=1)
    evidence_score: float = Field(..., ge=0.0, le=1.0)
    novelty_score: float = Field(..., ge=0.0, le=1.0)
    feasibility_score: float = Field(..., ge=0.0, le=1.0)
    risk_penalty: float = Field(..., ge=0.0, le=1.0)
    caveat_ids: tuple[str, ...] = Field(default_factory=tuple)
    evidence_pointer_ids: tuple[str, ...] = Field(default_factory=tuple)


class CandidateComparisonPacket(JsonModel):
    """Justification packet for why one candidate outranks another."""

    model_config = ConfigDict(extra="forbid")

    preferred_candidate_id: str = Field(..., min_length=1)
    other_candidate_id: str = Field(..., min_length=1)
    reasons: tuple[str, ...] = Field(default_factory=tuple)
    caveat_ids: tuple[str, ...] = Field(default_factory=tuple)
    evidence_pointer_ids: tuple[str, ...] = Field(default_factory=tuple)


def build_candidate_comparison_packet(
    *,
    preferred: CandidateComparisonInput,
    other: CandidateComparisonInput,
) -> CandidateComparisonPacket:
    """Generate evidence-linked packet describing why one candidate outranks another."""

    reasons: list[str] = []
    if preferred.rank > other.rank:
        raise ValueError(
            "preferred candidate rank must be better or equal to comparator"
        )
    if preferred.evidence_score > other.evidence_score:
        reasons.append("preferred candidate has stronger evidence support")
    if preferred.novelty_score > other.novelty_score:
        reasons.append("preferred candidate offers higher novelty value")
    if preferred.feasibility_score > other.feasibility_score:
        reasons.append("preferred candidate is more feasible for lab follow-up")
    if preferred.risk_penalty < other.risk_penalty:
        reasons.append("preferred candidate carries lower risk burden")
    if not reasons:
        reasons.append(
            "preferred candidate retains tie-break priority in ranking policy"
        )

    merged_caveats = tuple(sorted(set(preferred.caveat_ids + other.caveat_ids)))
    merged_evidence = tuple(
        sorted(set(preferred.evidence_pointer_ids + other.evidence_pointer_ids))
    )
    return CandidateComparisonPacket(
        preferred_candidate_id=preferred.candidate_id,
        other_candidate_id=other.candidate_id,
        reasons=tuple(reasons),
        caveat_ids=merged_caveats,
        evidence_pointer_ids=merged_evidence,
    )


class ReviewBoardVote(StrEnum):
    """Review-board vote states for candidate decisions."""

    APPROVE = "approve"
    DEFER = "defer"
    REJECT = "reject"


class ReviewBoardAgendaEntry(JsonModel):
    """One agenda item for review-board workflow execution."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    agenda_reason: str = Field(..., min_length=1)


class ReviewBoardVoteEntry(JsonModel):
    """Reviewer vote captured in review-board workflow."""

    model_config = ConfigDict(extra="forbid")

    reviewer_id: str = Field(..., min_length=1)
    candidate_id: str = Field(..., min_length=1)
    vote: ReviewBoardVote
    rationale: str = Field(..., min_length=1)


class ReviewBoardDecisionEntry(JsonModel):
    """Aggregated decision for one candidate after board vote resolution."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    decision: ReviewBoardVote
    disagreement: bool
    follow_up_actions: tuple[str, ...] = Field(default_factory=tuple)


class ReviewBoardWorkflowReport(JsonModel):
    """Review-board workflow covering agenda, votes, decisions, disagreements, and follow-ups."""

    model_config = ConfigDict(extra="forbid")

    board_id: str = Field(..., min_length=1)
    agenda: tuple[ReviewBoardAgendaEntry, ...] = Field(default_factory=tuple)
    decisions: tuple[ReviewBoardDecisionEntry, ...] = Field(default_factory=tuple)


def run_review_board_workflow(
    *,
    board_id: str,
    agenda: tuple[ReviewBoardAgendaEntry, ...],
    votes: tuple[ReviewBoardVoteEntry, ...],
) -> ReviewBoardWorkflowReport:
    """Model review-board decisions with vote disagreements and follow-up actions."""

    votes_by_candidate: dict[str, list[ReviewBoardVoteEntry]] = {}
    for vote in votes:
        votes_by_candidate.setdefault(vote.candidate_id, []).append(vote)

    decisions: list[ReviewBoardDecisionEntry] = []
    for entry in agenda:
        candidate_votes = votes_by_candidate.get(entry.candidate_id, [])
        counts = {
            ReviewBoardVote.APPROVE: 0,
            ReviewBoardVote.DEFER: 0,
            ReviewBoardVote.REJECT: 0,
        }
        for vote in candidate_votes:
            counts[vote.vote] += 1

        decision = max(counts.items(), key=lambda item: (item[1], item[0].value))[0]
        disagreement = len({vote.vote for vote in candidate_votes}) > 1
        follow_ups: list[str] = []
        if disagreement:
            follow_ups.append("schedule contradiction-focused evidence review")
        if decision is ReviewBoardVote.DEFER:
            follow_ups.append("collect additional evidence before next board cycle")
        if decision is ReviewBoardVote.REJECT:
            follow_ups.append("archive candidate with explicit rationale trace")

        decisions.append(
            ReviewBoardDecisionEntry(
                candidate_id=entry.candidate_id,
                decision=decision,
                disagreement=disagreement,
                follow_up_actions=tuple(follow_ups),
            )
        )

    decisions.sort(key=lambda decision: decision.candidate_id)
    return ReviewBoardWorkflowReport(
        board_id=board_id, agenda=agenda, decisions=tuple(decisions)
    )


class EvidenceFreshnessState(StrEnum):
    """Evidence freshness states used to detect stale or superseded inputs."""

    FRESH = "fresh"
    STALE = "stale"
    SUPERSEDED = "superseded"


class EvidenceFreshnessEntry(JsonModel):
    """Freshness status for one evidence item."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(..., min_length=1)
    freshness_state: EvidenceFreshnessState
    age_days: int = Field(..., ge=0)
    superseded_by: str | None = None
    requires_review: bool
    reason: str = Field(..., min_length=1)


class EvidenceFreshnessReport(JsonModel):
    """Freshness report requiring review on stale or superseded evidence."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[EvidenceFreshnessEntry, ...] = Field(default_factory=tuple)


def build_evidence_freshness_report(
    *,
    evidence_age_days: dict[str, int],
    superseded_edges: dict[str, str],
    stale_after_days: int = 30,
) -> EvidenceFreshnessReport:
    """Track stale/superseded evidence and require explicit review when needed."""

    entries: list[EvidenceFreshnessEntry] = []
    for evidence_id in sorted(set(evidence_age_days) | set(superseded_edges)):
        age_days = evidence_age_days.get(evidence_id, 0)
        superseded_by = superseded_edges.get(evidence_id)

        if superseded_by:
            state = EvidenceFreshnessState.SUPERSEDED
            requires_review = True
            reason = f"evidence superseded by {superseded_by}"
        elif age_days >= stale_after_days:
            state = EvidenceFreshnessState.STALE
            requires_review = True
            reason = (
                f"evidence age {age_days}d exceeds stale threshold {stale_after_days}d"
            )
        else:
            state = EvidenceFreshnessState.FRESH
            requires_review = False
            reason = "evidence freshness is within policy threshold"

        entries.append(
            EvidenceFreshnessEntry(
                evidence_id=evidence_id,
                freshness_state=state,
                age_days=age_days,
                superseded_by=superseded_by,
                requires_review=requires_review,
                reason=reason,
            )
        )

    return EvidenceFreshnessReport(entries=tuple(entries))


class DecisionRelevantContradiction(JsonModel):
    """Contradiction requiring potential lab resolution."""

    model_config = ConfigDict(extra="forbid")

    contradiction_id: str = Field(..., min_length=1)
    candidate_id: str = Field(..., min_length=1)
    decision_impact: float = Field(..., ge=0.0, le=1.0)
    unresolved_risk: float = Field(..., ge=0.0, le=1.0)
    suggested_experiment: str = Field(..., min_length=1)


class ContradictionAwareLabRecommendation(JsonModel):
    """Lab recommendation targeting high-impact unresolved contradictions."""

    model_config = ConfigDict(extra="forbid")

    contradiction_id: str = Field(..., min_length=1)
    candidate_id: str = Field(..., min_length=1)
    suggested_experiment: str = Field(..., min_length=1)
    resolution_priority_score: float = Field(..., ge=0.0)
    rationale: str = Field(..., min_length=1)


class ContradictionAwareLabRecommendationReport(JsonModel):
    """Recommendation report for contradiction-resolving experiments."""

    model_config = ConfigDict(extra="forbid")

    recommendations: tuple[ContradictionAwareLabRecommendation, ...] = Field(
        default_factory=tuple
    )


def build_contradiction_aware_lab_recommendation_report(
    contradictions: tuple[DecisionRelevantContradiction, ...],
) -> ContradictionAwareLabRecommendationReport:
    """Recommend experiments that resolve the most decision-relevant contradictions."""

    ranked: list[ContradictionAwareLabRecommendation] = []
    for contradiction in contradictions:
        score = (
            0.7 * contradiction.decision_impact + 0.3 * contradiction.unresolved_risk
        )
        ranked.append(
            ContradictionAwareLabRecommendation(
                contradiction_id=contradiction.contradiction_id,
                candidate_id=contradiction.candidate_id,
                suggested_experiment=contradiction.suggested_experiment,
                resolution_priority_score=score,
                rationale=(
                    "prioritized by decision impact and unresolved risk to maximize "
                    "decision-relevant contradiction resolution"
                ),
            )
        )

    ranked.sort(
        key=lambda rec: (
            -rec.resolution_priority_score,
            rec.candidate_id,
            rec.contradiction_id,
        )
    )
    return ContradictionAwareLabRecommendationReport(recommendations=tuple(ranked))
