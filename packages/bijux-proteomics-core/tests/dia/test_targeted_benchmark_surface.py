# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.dia.benchmarks import (
    TargetedCalibrationStandardObservation,
    TargetedHandoffHonestyObservation,
    TargetedHeavyLightPairObservation,
    TargetedOutcomeReconciliationObservation,
    WorkflowScientificSupportTier,
    build_targeted_raw_to_reviewed_bundle_report,
    build_targeted_workflow_benchmark_report,
)


def test_targeted_workflow_benchmark_report_surfaces_calibration_pairing_and_interference() -> (
    None
):
    report = build_targeted_workflow_benchmark_report(
        calibration_observations=(
            TargetedCalibrationStandardObservation(
                standard_id="std-a",
                sample_id="run-1",
                expected_ratio=1.0,
                observed_ratio=0.97,
                within_tolerance=True,
            ),
            TargetedCalibrationStandardObservation(
                standard_id="std-b",
                sample_id="run-1",
                expected_ratio=1.0,
                observed_ratio=1.34,
                within_tolerance=False,
            ),
        ),
        heavy_light_pairs=(
            TargetedHeavyLightPairObservation(
                pair_id="pair-a",
                light_candidate_id="pep-a-light",
                heavy_candidate_id="pep-a-heavy",
                pair_complete=True,
                heavy_light_ratio=1.02,
                interference_fraction=0.08,
            ),
            TargetedHeavyLightPairObservation(
                pair_id="pair-b",
                light_candidate_id="pep-b-light",
                heavy_candidate_id="pep-b-heavy",
                pair_complete=False,
                interference_fraction=0.22,
            ),
        ),
    )

    assert report.calibration_supported_count == 1
    assert report.calibration_failed_count == 1
    assert report.complete_heavy_light_pair_count == 1
    assert report.missing_heavy_light_pair_count == 1
    assert report.interference_flag_count == 1
    assert report.support_tier is WorkflowScientificSupportTier.PARTIAL
    assert "partial targeted support means" in report.partial_support_definition
    assert report.ready_for_transition_handoff is False


def test_targeted_raw_to_reviewed_bundle_report_links_qc_handoff_and_outcomes() -> None:
    benchmark = build_targeted_workflow_benchmark_report(
        calibration_observations=(
            TargetedCalibrationStandardObservation(
                standard_id="std-a",
                sample_id="run-1",
                expected_ratio=1.0,
                observed_ratio=1.0,
                within_tolerance=True,
            ),
        ),
        heavy_light_pairs=(
            TargetedHeavyLightPairObservation(
                pair_id="pair-a",
                light_candidate_id="pep-a-light",
                heavy_candidate_id="pep-a-heavy",
                pair_complete=True,
                heavy_light_ratio=1.0,
                interference_fraction=0.02,
            ),
        ),
    )

    report = build_targeted_raw_to_reviewed_bundle_report(
        chromatogram_failed_metric_rows=0,
        benchmark_report=benchmark,
        handoff_observations=(
            TargetedHandoffHonestyObservation(
                handoff_id="handoff-a",
                claimed_transition_ready=True,
                calibration_failures_visible=True,
                interference_failures_visible=True,
                control_gaps_visible=True,
            ),
            TargetedHandoffHonestyObservation(
                handoff_id="handoff-b",
                claimed_transition_ready=True,
                calibration_failures_visible=False,
                interference_failures_visible=True,
                control_gaps_visible=True,
            ),
        ),
        outcome_observations=(
            TargetedOutcomeReconciliationObservation(
                handoff_id="handoff-a",
                observed_transition_failure=False,
                reconciliation_recorded=False,
                corrective_action_visible=False,
            ),
            TargetedOutcomeReconciliationObservation(
                handoff_id="handoff-b",
                observed_transition_failure=True,
                reconciliation_recorded=False,
                corrective_action_visible=False,
            ),
        ),
    )

    assert report.chromatogram_surface_reviewable is True
    assert report.honest_handoff_count == 1
    assert report.inflated_handoff_count == 1
    assert report.reconciled_outcome_count == 1
    assert report.unreconciled_outcome_count == 1
    assert report.ready_for_reviewed_handoff is False
