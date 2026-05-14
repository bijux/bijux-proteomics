# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Board workflow, freshness, and contradiction-resolution review contracts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


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


class ReviewEvidenceFreshnessState(StrEnum):
    """Review-board freshness states used to detect stale or superseded inputs."""

    FRESH = "fresh"
    STALE = "stale"
    SUPERSEDED = "superseded"


class EvidenceFreshnessEntry(JsonModel):
    """Freshness status for one evidence item."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(..., min_length=1)
    freshness_state: ReviewEvidenceFreshnessState
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
            state = ReviewEvidenceFreshnessState.SUPERSEDED
            requires_review = True
            reason = f"evidence superseded by {superseded_by}"
        elif age_days >= stale_after_days:
            state = ReviewEvidenceFreshnessState.STALE
            requires_review = True
            reason = (
                f"evidence age {age_days}d exceeds stale threshold {stale_after_days}d"
            )
        else:
            state = ReviewEvidenceFreshnessState.FRESH
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
