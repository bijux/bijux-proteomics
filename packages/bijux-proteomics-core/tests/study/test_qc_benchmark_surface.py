# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.study.qc_benchmarks import (
    ContaminationCleanupObservation,
    QcCarryoverObservation,
    QcContaminationPropagationObservation,
    QcControlCoverageObservation,
    QcDecisionOutcomeObservation,
    QcDriftObservation,
    QcPromotionBlockObservation,
    SamplePrepDigestionObservation,
    build_contamination_cleanup_dossier_report,
    build_qc_carryover_benchmark_report,
    build_qc_contamination_propagation_report,
    build_qc_control_coverage_report,
    build_qc_decision_validity_benchmark_report,
    build_qc_drift_benchmark_report,
    build_qc_promotion_block_report,
    build_sample_prep_digestion_realism_report,
    build_workflow_minimum_control_report,
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


def test_build_qc_carryover_benchmark_report_requires_cross_surface_visibility() -> (
    None
):
    report = build_qc_carryover_benchmark_report(
        (
            QcCarryoverObservation(
                run_id="run-a",
                carryover_fraction=0.08,
                blank_control_present=True,
                wash_step_documented=True,
                lab_advisory_triggered=True,
                runtime_report_flagged=True,
            ),
            QcCarryoverObservation(
                run_id="run-b",
                carryover_fraction=0.12,
                blank_control_present=False,
                wash_step_documented=True,
                lab_advisory_triggered=False,
                runtime_report_flagged=True,
            ),
        )
    )

    assert report.elevated_carryover_count == 2
    assert report.unresolved_carryover_count == 1
    assert report.spans_core_lab_runtime is False
    assert report.ready_for_promotion is False


def test_build_sample_prep_digestion_realism_report_blocks_decoupled_success() -> None:
    report = build_sample_prep_digestion_realism_report(
        (
            SamplePrepDigestionObservation(
                sample_id="sample-a",
                missed_cleavage_rate=0.31,
                semi_specific_fraction=0.12,
                contaminant_fraction=0.05,
                chemistry_layer_passed=True,
                sample_prep_failure_visible=True,
            ),
            SamplePrepDigestionObservation(
                sample_id="sample-b",
                missed_cleavage_rate=0.08,
                semi_specific_fraction=0.04,
                contaminant_fraction=0.03,
                chemistry_layer_passed=True,
                sample_prep_failure_visible=False,
            ),
        )
    )

    assert report.digestion_failure_count == 1
    assert report.decoupled_success_count == 1
    assert report.ready_for_sequence_level_claims is False


def test_build_workflow_minimum_control_report_names_controls_for_each_workflow() -> (
    None
):
    report = build_workflow_minimum_control_report()

    assert {entry.workflow_family for entry in report.entries} == {
        "dda",
        "dia",
        "lfq",
        "multiplex",
        "ptm",
        "targeted",
    }
    targeted = next(
        entry for entry in report.entries if entry.workflow_family == "targeted"
    )
    assert targeted.minimum_controls == (
        "blank",
        "heavy_reference",
        "calibration_standard",
    )


def test_build_contamination_cleanup_dossier_report_requires_full_propagation() -> None:
    report = build_contamination_cleanup_dossier_report(
        (
            ContaminationCleanupObservation(
                run_id="run-a",
                contamination_fraction=0.18,
                cleanup_control_present=True,
                carryover_suspected=False,
                identification_posture_changed=True,
                quant_posture_changed=True,
                interpretation_posture_changed=True,
                corrective_action_visible=True,
            ),
            ContaminationCleanupObservation(
                run_id="run-b",
                contamination_fraction=0.14,
                cleanup_control_present=False,
                carryover_suspected=True,
                identification_posture_changed=True,
                quant_posture_changed=False,
                interpretation_posture_changed=True,
                corrective_action_visible=False,
            ),
        )
    )

    assert report.full_propagation_count == 1
    assert report.unresolved_cleanup_failure_count == 1
    assert report.scientifically_defensible is False
