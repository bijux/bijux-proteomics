# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.benchmarks.adoption import (
    ExternalPtmTrialInput,
    TrialIssueEntry,
    build_external_strong_user_ptm_trial_report,
)


def test_build_external_strong_user_ptm_trial_report_requires_handoff_step() -> None:
    report = build_external_strong_user_ptm_trial_report(
        ExternalPtmTrialInput(
            trial_id="trial-ptm-03",
            external_user_id="ext-user-d",
            ptm_study_id="ptm-mini-03",
            executed_steps=("ptm-ambiguity-review",),
            issues=(
                TrialIssueEntry(
                    issue_id="ptm-5",
                    summary="localization uncertainty too coarse",
                    evidence_pointer="evidence://ptm/site/44",
                    severity="high",
                ),
            ),
        )
    )

    assert report.trial_completed is False
    assert report.precise_issue_count == 1
