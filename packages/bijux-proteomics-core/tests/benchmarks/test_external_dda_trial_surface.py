# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.benchmarks.adoption import (
    ExternalDdaTrialInput,
    TrialIssueEntry,
    build_external_strong_user_dda_trial_report,
)


def test_build_external_strong_user_dda_trial_report_tracks_precise_issues() -> None:
    report = build_external_strong_user_dda_trial_report(
        ExternalDdaTrialInput(
            trial_id="trial-dda-01",
            external_user_id="ext-user-a",
            dataset_id="dda-mini-01",
            executed_steps=("dda-import", "qc", "evidence", "review"),
            issues=(
                TrialIssueEntry(
                    issue_id="i-1",
                    summary="review packet missing ambiguity rationale",
                    evidence_pointer="evidence://claim/22",
                    severity="high",
                ),
            ),
        )
    )

    assert report.trial_completed is True
    assert report.precise_issue_count == 1
