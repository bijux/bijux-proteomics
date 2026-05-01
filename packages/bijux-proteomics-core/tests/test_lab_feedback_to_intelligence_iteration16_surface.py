# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.lab_planning_iteration16 import (
    IntelligenceFeedbackBaseline,
    LabObservedOutcomeSignal,
    apply_lab_feedback_to_intelligence_prioritization,
)


def test_apply_lab_feedback_to_intelligence_prioritization_preserves_history() -> None:
    report = apply_lab_feedback_to_intelligence_prioritization(
        baselines=(
            IntelligenceFeedbackBaseline(
                candidate_id="cand-1",
                baseline_score=0.6,
                historical_snapshot_id="snap-1",
            ),
        ),
        outcomes=(
            LabObservedOutcomeSignal(
                candidate_id="cand-1",
                outcome_strength=0.8,
                evidence_quality=0.9,
            ),
        ),
    )

    adjustment = report.adjustments[0]
    assert adjustment.preserves_history is True
    assert adjustment.adjusted_score > adjustment.baseline_score
