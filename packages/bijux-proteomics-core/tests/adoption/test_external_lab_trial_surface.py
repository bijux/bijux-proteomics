# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.adoption import (
    ExternalLabTrialInput,
    TrialIssueEntry,
    build_external_strong_user_lab_trial_report,
)


def test_build_external_strong_user_lab_trial_report_validates_required_steps() -> None:
    report = build_external_strong_user_lab_trial_report(
        ExternalLabTrialInput(
            trial_id="trial-lab-04",
            external_user_id="ext-user-e",
            lab_program_id="lab-cycle-12",
            executed_steps=("assay-plan", "risk-review", "handoff-export"),
            issues=(
                TrialIssueEntry(
                    issue_id="lab-2",
                    summary="handoff field naming inconsistent",
                    evidence_pointer="evidence://lab/export/8",
                    severity="low",
                ),
            ),
        )
    )

    assert report.trial_completed is True
    assert report.precise_issue_count == 1
