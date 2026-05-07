# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.study.qc_benchmarks import (
    QcContaminationPropagationObservation,
    QcControlCoverageObservation,
    QcDecisionOutcomeObservation,
    QcDriftObservation,
    QcPromotionBlockObservation,
    build_qc_contamination_propagation_report,
    build_qc_control_coverage_report,
    build_qc_decision_validity_benchmark_report,
    build_qc_drift_benchmark_report,
    build_qc_promotion_block_report,
)


def test_build_qc_decision_validity_benchmark_report_checks_predictive_strength() -> (
    None
):
    report = build_qc_decision_validity_benchmark_report(
        (
            QcDecisionOutcomeObservation(
                run_id="run-a",
                qc_flagged=True,
                downstream_evidence_failed=True,
                downstream_lab_follow_up_failed=False,
            ),
            QcDecisionOutcomeObservation(
                run_id="run-b",
                qc_flagged=True,
                downstream_evidence_failed=True,
                downstream_lab_follow_up_failed=True,
            ),
            QcDecisionOutcomeObservation(
                run_id="run-c",
                qc_flagged=False,
                downstream_evidence_failed=False,
                downstream_lab_follow_up_failed=False,
            ),
            QcDecisionOutcomeObservation(
                run_id="run-d",
                qc_flagged=True,
                downstream_evidence_failed=False,
                downstream_lab_follow_up_failed=False,
            ),
        )
    )

    assert report.true_positive_count == 2
    assert report.false_positive_count == 1
    assert report.true_negative_count == 1
    assert report.false_negative_count == 0
    assert report.predictive_precision == 2 / 3
    assert report.predictive_recall == 1.0
    assert report.qc_findings_predictive is False


def test_build_qc_control_coverage_report_blocks_parseable_but_undercontrolled_runs() -> (
    None
):
    report = build_qc_control_coverage_report(
        (
            QcControlCoverageObservation(
                run_id="run-a",
                workflow_family="lfq",
                required_controls=("blank", "pooled_reference"),
                observed_controls=("blank",),
                computationally_parseable=True,
            ),
            QcControlCoverageObservation(
                run_id="run-b",
                workflow_family="ptm",
                required_controls=("enrichment_blank",),
                observed_controls=("enrichment_blank",),
                computationally_parseable=True,
            ),
        )
    )

    run_a = next(entry for entry in report.entries if entry.run_id == "run-a")
    assert run_a.scientifically_interpretable is False
    assert run_a.promotion_blocked is True
    assert run_a.missing_controls == ("pooled_reference",)
    assert report.parseable_but_uninterpretable_count == 1
    assert report.promotion_blocked_count == 1


def test_build_qc_promotion_block_report_rejects_annotation_only_failures() -> None:
    report = build_qc_promotion_block_report(
        (
            QcPromotionBlockObservation(
                run_id="run-a",
                failed_qc=True,
                attempted_decision_promotion=True,
                promotion_prevented=True,
                blocking_reason="identification_rate",
            ),
            QcPromotionBlockObservation(
                run_id="run-b",
                failed_qc=True,
                attempted_decision_promotion=True,
                promotion_prevented=False,
                blocking_reason="carryover",
            ),
        )
    )

    assert report.failed_qc_blocked_count == 1
    assert report.annotation_only_failure_count == 1
    assert report.ready_for_decision_promotion is False


def test_build_qc_contamination_propagation_report_links_burden_to_consequence() -> (
    None
):
    report = build_qc_contamination_propagation_report(
        (
            QcContaminationPropagationObservation(
                run_id="run-a",
                contaminant_psm_fraction=0.18,
                identification_rate_drop_fraction=0.22,
                quant_distortion_fraction=0.31,
                interpretation_advisory_triggered=True,
            ),
            QcContaminationPropagationObservation(
                run_id="run-b",
                contaminant_psm_fraction=0.12,
                identification_rate_drop_fraction=0.16,
                quant_distortion_fraction=0.18,
                interpretation_advisory_triggered=True,
            ),
        )
    )

    assert report.high_burden_count == 2
    assert report.propagated_consequence_count == 2
    assert report.unresolved_high_burden_count == 0
    assert report.contamination_is_scientifically_material is True


def test_build_qc_drift_benchmark_report_requires_dual_drift_blocking() -> None:
    report = build_qc_drift_benchmark_report(
        (
            QcDriftObservation(
                run_id="run-a",
                batch_id="batch-1",
                run_level_drift_score=1.2,
                batch_level_drift_score=1.1,
                promotion_blocked=True,
            ),
            QcDriftObservation(
                run_id="run-b",
                batch_id="batch-1",
                run_level_drift_score=1.4,
                batch_level_drift_score=1.3,
                promotion_blocked=False,
            ),
        )
    )

    assert report.run_level_drift_count == 2
    assert report.batch_level_drift_count == 2
    assert report.dual_drift_count == 2
    assert report.unblocked_dual_drift_count == 1
    assert report.ready_for_cohort_interpretation is False
