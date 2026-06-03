# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_lab.handoffs.qc_feedback import (
    LabRunQcFeedbackReasonCode,
    LabRunQcFeedbackStatus,
    LabRunQcObservation,
    build_lab_run_qc_feedback_report,
)
from bijux_proteomics_lab.outcomes.observations import (
    AssayObservationRecord,
    QcState,
)


def test_build_lab_run_qc_feedback_report_groups_observations_by_run_status_and_reason() -> (
    None
):
    report = build_lab_run_qc_feedback_report(
        (
            LabRunQcObservation(
                run_id="run-control-1.raw",
                sample_id="control_1",
                observation=AssayObservationRecord(
                    assay_id="assay_cv_screen",
                    metric="coefficient_of_variation",
                    value=0.42,
                    replicate_values=[0.40, 0.42, 0.44],
                    qc_state=QcState.FAILED,
                    qc_passed=False,
                    dispersion=0.42,
                    normalization_method="median",
                    interpretation_confidence=0.7,
                ),
            ),
            LabRunQcObservation(
                run_id="run-control-1.raw",
                sample_id="control_1",
                observation=AssayObservationRecord(
                    assay_id="assay_signal_floor",
                    metric="signal_floor",
                    value=12.0,
                    qc_state=QcState.WARNING,
                    qc_passed=True,
                    below_detection_limit=True,
                    normalization_method="median",
                    interpretation_confidence=0.5,
                ),
            ),
            LabRunQcObservation(
                run_id="run-treatment-1.raw",
                sample_id="treatment_1",
                observation=AssayObservationRecord(
                    assay_id="assay_signal_floor",
                    metric="signal_floor",
                    value=140.0,
                    qc_state=QcState.PASSED,
                    qc_passed=True,
                    normalization_method="median",
                    interpretation_confidence=0.95,
                ),
            ),
        )
    )

    assert report.failed_count == 1
    assert report.caution_count == 0
    assert report.passed_count == 1

    by_run = {entry.run_id: entry for entry in report.entries}
    failed = by_run["run-control-1.raw"]
    passed = by_run["run-treatment-1.raw"]

    assert failed.status is LabRunQcFeedbackStatus.FAILED
    assert failed.composite_quality < passed.composite_quality
    assert failed.supporting_assay_ids == (
        "assay_cv_screen",
        "assay_signal_floor",
    )
    assert LabRunQcFeedbackReasonCode.QC_FAILED in failed.reason_codes
    assert LabRunQcFeedbackReasonCode.BELOW_DETECTION_LIMIT in failed.reason_codes
    assert LabRunQcFeedbackReasonCode.LOW_REPRODUCIBILITY in failed.reason_codes
    assert all(
        source_ref.startswith("lab_qc:run-control-1.raw:")
        for source_ref in failed.source_refs
    )
    assert "qc_failed" in failed.note
    assert passed.status is LabRunQcFeedbackStatus.PASSED
