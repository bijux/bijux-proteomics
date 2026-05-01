# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.study_metadata_iteration08 import (
    ObservedLabOutcome,
    PlannedLabOutcome,
    reconcile_planned_and_observed_lab_outcomes,
)


def test_reconcile_planned_and_observed_lab_outcomes_preserves_planned_state() -> None:
    report = reconcile_planned_and_observed_lab_outcomes(
        planned=(
            PlannedLabOutcome(
                target_id="target-1",
                sample_id="sample-01",
                expected_state="enriched",
                planned_note="primary expectation",
            ),
            PlannedLabOutcome(
                target_id="target-2",
                sample_id="sample-01",
                expected_state="unchanged",
            ),
        ),
        observed=(
            ObservedLabOutcome(
                target_id="target-1",
                sample_id="sample-01",
                observed_state="enriched",
            ),
            ObservedLabOutcome(
                target_id="target-2",
                sample_id="sample-01",
                observed_state="depleted",
            ),
        ),
    )

    assert report.matched_count == 1
    assert report.mismatched_count == 1
    assert report.unobserved_count == 0
    mismatch = next(entry for entry in report.entries if entry.target_id == "target-2")
    assert mismatch.expected_state == "unchanged"
    assert mismatch.observed_state == "depleted"
    assert mismatch.evidence_state == "contradicted"
