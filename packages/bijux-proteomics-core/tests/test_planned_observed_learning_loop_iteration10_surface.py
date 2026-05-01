# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics.lab_planning_iteration10 import (
    ObservedOutcomeSignal,
    PlannedRecommendation,
    apply_planned_observed_learning_loop,
)


def test_apply_planned_observed_learning_loop_updates_scores_and_keeps_history_locked() -> (
    None
):
    report = apply_planned_observed_learning_loop(
        planned=(
            PlannedRecommendation(
                decision_id="d1",
                candidate_id="cand-1",
                recommended_action="validate",
                score=0.7,
                rationale="strong evidence",
            ),
        ),
        observed=(
            ObservedOutcomeSignal(
                decision_id="d1",
                matched_expectation=False,
                outcome_strength=0.5,
            ),
        ),
    )

    update = report.updated_recommendations[0]
    assert update.previous_score == pytest.approx(0.7)
    assert update.updated_score == pytest.approx(0.6)
    assert update.historical_decision_locked is True
