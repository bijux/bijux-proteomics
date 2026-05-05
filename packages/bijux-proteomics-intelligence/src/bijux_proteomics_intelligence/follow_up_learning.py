# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Recommendation learning from planned decisions and observed outcomes."""

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

