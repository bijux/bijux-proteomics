# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.follow_up_learning import (
    ObservedOutcomeSignal,
    OutcomeLearningDisposition,
    PlannedRecommendation,
    apply_planned_observed_learning_loop,
)


def test_planned_observed_learning_loop_locks_history_for_missing_outcomes() -> None:
    report = apply_planned_observed_learning_loop(
        planned=(
            PlannedRecommendation(
                decision_id="decision-a",
                candidate_id="candidate-a",
                recommended_action="targeted follow-up",
                score=0.72,
                rationale="contradiction pressure remains high",
            ),
        ),
        observed=(
            ObservedOutcomeSignal(
                decision_id="decision-b",
                matched_expectation=True,
                outcome_strength=1.0,
            ),
        ),
    )

    update = report.updated_recommendations[0]
    assert update.updated_score == update.previous_score
    assert update.score_delta == 0.0
    assert update.posture_shift == "unchanged_without_observation"
    assert update.historical_decision_locked is True


def test_planned_observed_learning_loop_holds_after_contradictory_outcome() -> None:
    report = apply_planned_observed_learning_loop(
        planned=(
            PlannedRecommendation(
                decision_id="decision-a",
                candidate_id="candidate-a",
                recommended_action="advance to targeted follow-up",
                score=0.78,
                rationale="grounded evidence and good assay feasibility",
            ),
        ),
        observed=(
            ObservedOutcomeSignal(
                decision_id="decision-a",
                matched_expectation=False,
                outcome_strength=0.9,
            ),
        ),
    )

    update = report.updated_recommendations[0]
    assert update.recommended_action == "hold for contradiction review"
    assert update.posture_shift == "hold_for_recheck"
    assert update.updated_score < update.previous_score
    assert report.hold_decision_count == 1


def test_planned_observed_learning_loop_redesigns_operationally_blocked_follow_up() -> (
    None
):
    report = apply_planned_observed_learning_loop(
        planned=(
            PlannedRecommendation(
                decision_id="decision-b",
                candidate_id="candidate-b",
                recommended_action="advance to multiplex follow-up",
                score=0.74,
                rationale="analytically strong but operationally heavier path",
            ),
        ),
        observed=(
            ObservedOutcomeSignal(
                decision_id="decision-b",
                matched_expectation=False,
                outcome_strength=0.8,
                disposition=OutcomeLearningDisposition.OPERATIONALLY_BLOCKED,
                follow_up_burden=0.7,
            ),
        ),
    )

    update = report.updated_recommendations[0]
    assert update.recommended_action == "redesign follow-up before retry"
    assert update.posture_shift == "redesign_follow_up"
    assert update.updated_score < update.previous_score
    assert report.redesign_pressure_count == 1
