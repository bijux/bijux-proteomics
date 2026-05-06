# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Recommendation learning from planned decisions and observed outcomes."""

from __future__ import annotations

from enum import StrEnum

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
    disposition: "OutcomeLearningDisposition | None" = None
    follow_up_burden: float = Field(default=0.0, ge=0.0, le=1.0)


class OutcomeLearningDisposition(StrEnum):
    """How one observed outcome should reshape future analytical posture."""

    CONFIRMED = "confirmed"
    CONTRADICTED = "contradicted"
    OPERATIONALLY_BLOCKED = "operationally_blocked"
    INCONCLUSIVE = "inconclusive"


class LearningAdjustedRecommendation(JsonModel):
    """Learning-loop recommendation update with historical trace preservation."""

    model_config = ConfigDict(extra="forbid")

    decision_id: str = Field(..., min_length=1)
    candidate_id: str = Field(..., min_length=1)
    recommended_action: str = Field(..., min_length=1)
    previous_score: float = Field(..., ge=0.0, le=1.0)
    updated_score: float = Field(..., ge=0.0, le=1.0)
    score_delta: float
    posture_shift: str = Field(..., min_length=1)
    next_review_action: str = Field(..., min_length=1)
    learning_rationale: tuple[str, ...] = Field(default_factory=tuple)
    historical_decision_locked: bool


class PlannedObservedLearningLoopReport(JsonModel):
    """Learning-loop report over planned recommendations and observed outcomes."""

    model_config = ConfigDict(extra="forbid")

    updated_recommendations: tuple[LearningAdjustedRecommendation, ...] = Field(
        default_factory=tuple
    )
    reinforced_decision_count: int = Field(default=0, ge=0)
    hold_decision_count: int = Field(default=0, ge=0)
    redesign_pressure_count: int = Field(default=0, ge=0)


def _effective_disposition(
    outcome: ObservedOutcomeSignal,
) -> OutcomeLearningDisposition:
    if outcome.disposition is not None:
        return outcome.disposition
    if outcome.matched_expectation:
        return OutcomeLearningDisposition.CONFIRMED
    return OutcomeLearningDisposition.CONTRADICTED


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
                    posture_shift="unchanged_without_observation",
                    next_review_action="keep the original analytical posture until an outcome arrives",
                    learning_rationale=(
                        "no observed outcome was linked to this decision",
                    ),
                    historical_decision_locked=True,
                )
            )
            continue

        disposition = _effective_disposition(outcome)
        recommended_action = recommendation.recommended_action
        posture_shift = "reinforced"
        next_review_action = "keep the current analytical posture for the next review"
        learning_rationale: list[str] = []
        if disposition is OutcomeLearningDisposition.CONFIRMED:
            delta = 0.2 * outcome.outcome_strength
            learning_rationale.append(
                "observed outcome confirmed the planned expectation"
            )
        elif disposition is OutcomeLearningDisposition.CONTRADICTED:
            delta = -(0.25 * outcome.outcome_strength)
            posture_shift = "hold_for_recheck"
            recommended_action = "hold for contradiction review"
            next_review_action = (
                "collect contradiction-resolving follow-up before re-ranking"
            )
            learning_rationale.append(
                "observed outcome contradicted the planned expectation"
            )
        elif disposition is OutcomeLearningDisposition.OPERATIONALLY_BLOCKED:
            delta = -(0.15 * outcome.outcome_strength) - (
                0.1 * outcome.follow_up_burden
            )
            posture_shift = "redesign_follow_up"
            recommended_action = "redesign follow-up before retry"
            next_review_action = (
                "lower execution burden before repeating the recommendation"
            )
            learning_rationale.append(
                "observed outcome exposed operational fragility in the planned follow-up"
            )
        else:
            delta = -(0.05 * outcome.outcome_strength)
            posture_shift = "collect_clearer_signal"
            recommended_action = "collect clearer outcome signal"
            next_review_action = (
                "gather a cleaner outcome before strengthening analytical claims"
            )
            learning_rationale.append(
                "observed outcome stayed too inconclusive to strengthen the analytical posture"
            )
        updated_score = min(1.0, max(0.0, recommendation.score + delta))
        learning_rationale.append(f"outcome_strength={outcome.outcome_strength:.2f}")
        if outcome.follow_up_burden > 0.0:
            learning_rationale.append(
                f"follow_up_burden={outcome.follow_up_burden:.2f}"
            )
        updates.append(
            LearningAdjustedRecommendation(
                decision_id=recommendation.decision_id,
                candidate_id=recommendation.candidate_id,
                recommended_action=recommended_action,
                previous_score=recommendation.score,
                updated_score=updated_score,
                score_delta=updated_score - recommendation.score,
                posture_shift=posture_shift,
                next_review_action=next_review_action,
                learning_rationale=tuple(learning_rationale),
                historical_decision_locked=True,
            )
        )

    reinforced_decision_count = sum(
        1 for update in updates if update.posture_shift == "reinforced"
    )
    hold_decision_count = sum(
        1 for update in updates if update.posture_shift == "hold_for_recheck"
    )
    redesign_pressure_count = sum(
        1 for update in updates if update.posture_shift == "redesign_follow_up"
    )
    return PlannedObservedLearningLoopReport(
        updated_recommendations=tuple(
            sorted(updates, key=lambda entry: (entry.candidate_id, entry.decision_id))
        ),
        reinforced_decision_count=reinforced_decision_count,
        hold_decision_count=hold_decision_count,
        redesign_pressure_count=redesign_pressure_count,
    )
