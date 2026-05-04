# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.adoption import (
    ExternalDiaTrialInput,
    TrialIssueEntry,
    build_external_strong_user_dia_trial_report,
)


def test_build_external_strong_user_dia_trial_report_requires_quant_step() -> None:
    report = build_external_strong_user_dia_trial_report(
        ExternalDiaTrialInput(
            trial_id="trial-dia-01",
            external_user_id="ext-user-b",
            dataset_id="dia-mini-03",
            executed_steps=("dia-import", "qc", "evidence"),
            issues=(
                TrialIssueEntry(
                    issue_id="i-22",
                    summary="quant matrix column mismatch",
                    evidence_pointer="evidence://run/12",
                    severity="medium",
                ),
            ),
        )
    )

    assert report.trial_completed is False
    assert report.precise_issue_count == 1
