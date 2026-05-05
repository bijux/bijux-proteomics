# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Recommendation learning for follow-up and lab-priority decisions."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class PlannedRecommendation(JsonModel):
    """Planned recommendation snapshot tied to a historical decision."""

    model_config = ConfigDict(extra="forbid")

    decision_id: str = Field(..., min_length=1)
    candidate_id: str = Field(..., min_length=1)
    recommended_action: str = Field(..., min_length=1)
    score: float = Field(..., ge=0.0, le=1.0)
    rationale: str = Field(..., min_length=1)


class ObservedOutcomeSignal(JsonModel):
    """Observed lab outcome used for recommendation learning updates."""

    model_config = ConfigDict(extra="forbid")

    decision_id: str = Field(..., min_length=1)
    matched_expectation: bool
    outcome_strength: float = Field(..., ge=0.0, le=1.0)


class LearningAdjustedRecommendation(JsonModel):
    """Learning-loop recommendation update with historical trace preservation."""

    model_config = ConfigDict(extra="forbid")

    decision_id: str = Field(..., min_length=1)
    candidate_id: str = Field(..., min_length=1)
    recommended_action: str = Field(..., min_length=1)
    previous_score: float = Field(..., ge=0.0, le=1.0)
    updated_score: float = Field(..., ge=0.0, le=1.0)
    score_delta: float
    historical_decision_locked: bool


class PlannedObservedLearningLoopReport(JsonModel):
    """Learning-loop report over planned recommendations and observed outcomes."""

    model_config = ConfigDict(extra="forbid")

    updated_recommendations: tuple[LearningAdjustedRecommendation, ...] = Field(
        default_factory=tuple
    )


def apply_planned_observed_learning_loop(
    planned: tuple[PlannedRecommendation, ...],
    observed: tuple[ObservedOutcomeSignal, ...],
) -> PlannedObservedLearningLoopReport:
    """Update recommendations from outcomes without mutating historical decisions."""

    outcome_by_decision = {entry.decision_id: entry for entry in observed}
    updates: list[LearningAdjustedRecommendation] = []

    for recommendation in planned:
        outcome = outcome_by_decision.get(recommendation.decision_id)
        if outcome is None:
            updates.append(
                LearningAdjustedRecommendation(
                    decision_id=recommendation.decision_id,
                    candidate_id=recommendation.candidate_id,
                    recommended_action=recommendation.recommended_action,
                    previous_score=recommendation.score,
                    updated_score=recommendation.score,
                    score_delta=0.0,
                    historical_decision_locked=True,
                )
            )
            continue

        direction = 1.0 if outcome.matched_expectation else -1.0
        delta = direction * (0.2 * outcome.outcome_strength)
        updated_score = min(1.0, max(0.0, recommendation.score + delta))
        updates.append(
            LearningAdjustedRecommendation(
                decision_id=recommendation.decision_id,
                candidate_id=recommendation.candidate_id,
                recommended_action=recommendation.recommended_action,
                previous_score=recommendation.score,
                updated_score=updated_score,
                score_delta=updated_score - recommendation.score,
                historical_decision_locked=True,
            )
        )

    return PlannedObservedLearningLoopReport(
        updated_recommendations=tuple(
            sorted(updates, key=lambda entry: (entry.candidate_id, entry.decision_id))
        )
    )


class LabQueuePrioritizationInput(JsonModel):
    """Inputs used to prioritize candidate placement in a follow-up queue."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    candidate_score: float = Field(..., ge=0.0, le=1.0)
    evidence_gap_count: int = Field(..., ge=0)
    cost_score: float = Field(..., ge=0.0, le=1.0)
    capacity_pressure_score: float = Field(..., ge=0.0, le=1.0)
    assay_constraint_penalty: float = Field(..., ge=0.0, le=1.0)


class LabQueuePrioritizationEntry(JsonModel):
    """Prioritized follow-up queue entry with rationale score."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    queue_priority_score: float
    queue_rank: int = Field(..., ge=1)


class LabQueuePrioritizationReport(JsonModel):
    """Queue prioritization report for candidate follow-up actions."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[LabQueuePrioritizationEntry, ...] = Field(default_factory=tuple)


def build_lab_queue_prioritization_report(
    items: tuple[LabQueuePrioritizationInput, ...],
) -> LabQueuePrioritizationReport:
    """Prioritize follow-up queue placement with explicit evidence and burden tradeoffs."""

    scored = []
    for item in items:
        gap_bonus = min(1.0, item.evidence_gap_count / 5.0)
        score = (
            (0.4 * item.candidate_score)
            + (0.2 * gap_bonus)
            + (0.15 * (1.0 - item.cost_score))
            + (0.15 * (1.0 - item.capacity_pressure_score))
            + (0.1 * (1.0 - item.assay_constraint_penalty))
        )
        scored.append((item.candidate_id, score))

    scored.sort(key=lambda row: (-row[1], row[0]))
    entries = tuple(
        LabQueuePrioritizationEntry(
            candidate_id=candidate_id,
            queue_priority_score=score,
            queue_rank=index + 1,
        )
        for index, (candidate_id, score) in enumerate(scored)
    )
    return LabQueuePrioritizationReport(entries=entries)


class IntelligenceFeedbackBaseline(JsonModel):
    """Baseline prioritization state preserved from historical decisions."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    baseline_score: float = Field(..., ge=0.0, le=1.0)
    historical_snapshot_id: str = Field(..., min_length=1)


class LabObservedOutcomeSignal(JsonModel):
    """Observed lab outcome signal used to adjust future prioritization."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    outcome_strength: float = Field(..., ge=-1.0, le=1.0)
    evidence_quality: float = Field(..., ge=0.0, le=1.0)


class IntelligenceFeedbackAdjustment(JsonModel):
    """Adjusted score for future prioritization while retaining historical snapshots."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    historical_snapshot_id: str = Field(..., min_length=1)
    baseline_score: float = Field(..., ge=0.0, le=1.0)
    adjusted_score: float = Field(..., ge=0.0, le=1.0)
    preserves_history: bool


class IntelligenceFeedbackReport(JsonModel):
    """Feedback report from lab outcomes into future prioritization."""

    model_config = ConfigDict(extra="forbid")

    adjustments: tuple[IntelligenceFeedbackAdjustment, ...] = Field(
        default_factory=tuple
    )


def apply_lab_feedback_to_intelligence_prioritization(
    *,
    baselines: tuple[IntelligenceFeedbackBaseline, ...],
    outcomes: tuple[LabObservedOutcomeSignal, ...],
) -> IntelligenceFeedbackReport:
    """Apply lab outcomes to future prioritization without rewriting historical snapshots."""

    outcomes_by_candidate = {outcome.candidate_id: outcome for outcome in outcomes}
    adjustments: list[IntelligenceFeedbackAdjustment] = []
    for baseline in baselines:
        outcome = outcomes_by_candidate.get(baseline.candidate_id)
        if outcome is None:
            adjusted = baseline.baseline_score
        else:
            delta = 0.2 * outcome.outcome_strength * outcome.evidence_quality
            adjusted = max(0.0, min(1.0, baseline.baseline_score + delta))

        adjustments.append(
            IntelligenceFeedbackAdjustment(
                candidate_id=baseline.candidate_id,
                historical_snapshot_id=baseline.historical_snapshot_id,
                baseline_score=baseline.baseline_score,
                adjusted_score=adjusted,
                preserves_history=True,
            )
        )

    adjustments.sort(key=lambda item: item.candidate_id)
    return IntelligenceFeedbackReport(adjustments=tuple(adjustments))
