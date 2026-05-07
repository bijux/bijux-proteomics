# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.dia.benchmarks import (
    TargetedCalibrationStandardObservation,
    TargetedHeavyLightPairObservation,
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
    assert report.ready_for_transition_handoff is False
