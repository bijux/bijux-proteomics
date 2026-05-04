# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.adoption import (
    ExternalQuantTrialInput,
    TrialIssueEntry,
    build_external_strong_user_quant_trial_report,
)


def test_build_external_strong_user_quant_trial_report_checks_required_steps() -> None:
    report = build_external_strong_user_quant_trial_report(
        ExternalQuantTrialInput(
            trial_id="trial-quant-01",
            external_user_id="ext-user-c",
            mini_study_id="lfq-mini-02",
            executed_steps=("normalization", "differential-abundance", "review"),
            issues=(
                TrialIssueEntry(
                    issue_id="q-1",
                    summary="volcano threshold narrative mismatch",
                    evidence_pointer="evidence://quant/report/1",
                    severity="medium",
                ),
            ),
        )
    )

    assert report.trial_completed is True
    assert report.precise_issue_count == 1
