# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.follow_up_learning import (
    IntelligenceFeedbackBaseline,
    LabObservedOutcomeSignal,
    LabQueuePrioritizationInput,
    ObservedOutcomeSignal,
    PlannedRecommendation,
    apply_lab_feedback_to_intelligence_prioritization,
    apply_planned_observed_learning_loop,
    build_lab_queue_prioritization_report,
)


def test_lab_queue_prioritization_favors_evidence_gap_relief_under_lower_burden() -> None:
    report = build_lab_queue_prioritization_report(
        (
            LabQueuePrioritizationInput(
                candidate_id="candidate-a",
                candidate_score=0.82,
                evidence_gap_count=4,
                cost_score=0.2,
                capacity_pressure_score=0.3,
                assay_constraint_penalty=0.1,
            ),
            LabQueuePrioritizationInput(
                candidate_id="candidate-b",
                candidate_score=0.85,
                evidence_gap_count=1,
                cost_score=0.7,
                capacity_pressure_score=0.8,
                assay_constraint_penalty=0.5,
            ),
        )
    )

    assert report.entries[0].candidate_id == "candidate-a"
    assert report.entries[0].queue_rank == 1


def test_lab_feedback_preserves_history_and_penalizes_failed_outcomes() -> None:
    report = apply_lab_feedback_to_intelligence_prioritization(
        baselines=(
            IntelligenceFeedbackBaseline(
                candidate_id="candidate-a",
                baseline_score=0.7,
                historical_snapshot_id="snap-1",
            ),
            IntelligenceFeedbackBaseline(
                candidate_id="candidate-b",
                baseline_score=0.5,
                historical_snapshot_id="snap-2",
            ),
        ),
        outcomes=(
            LabObservedOutcomeSignal(
                candidate_id="candidate-a",
                outcome_strength=-0.8,
                evidence_quality=1.0,
            ),
        ),
    )

    degraded = next(
        entry for entry in report.adjustments if entry.candidate_id == "candidate-a"
    )
    unchanged = next(
        entry for entry in report.adjustments if entry.candidate_id == "candidate-b"
    )
    assert degraded.adjusted_score < degraded.baseline_score
    assert unchanged.adjusted_score == unchanged.baseline_score
    assert all(entry.preserves_history for entry in report.adjustments)


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
