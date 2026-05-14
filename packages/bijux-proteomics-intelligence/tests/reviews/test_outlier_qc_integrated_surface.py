# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.reviews.candidates import (
    QuantOutlierObservation,
    RunQcSummaryLink,
    build_outlier_qc_integrated_report,
)


def test_build_outlier_qc_integrated_report_prioritizes_failed_qc_runs() -> None:
    report = build_outlier_qc_integrated_report(
        outliers=(
            QuantOutlierObservation(
                outlier_id="o-1",
                sample_id="s-1",
                run_id="r-fail",
                protein_id="P1",
                z_score=2.4,
                batch_id="b-1",
            ),
        ),
        qc_summaries=(
            RunQcSummaryLink(
                run_id="r-fail",
                qc_disposition="failed",
                qc_issue_codes=("rt_drift",),
            ),
        ),
    )

    assert report.entries[0].qc_disposition == "failed"
    assert report.entries[0].triage_priority == 1
