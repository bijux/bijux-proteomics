# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.follow_up_learning import (
    ObservedOutcomeSignal,
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
    assert update.historical_decision_locked is True
