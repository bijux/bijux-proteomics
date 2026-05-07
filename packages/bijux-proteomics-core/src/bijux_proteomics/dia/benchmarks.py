# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Scientific benchmark surfaces for DIA-targeted and transition workflows."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class TargetedCalibrationStandardObservation(JsonModel):
    """Observed calibration-standard behavior for one targeted benchmark sample."""

    model_config = ConfigDict(extra="forbid")

    standard_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    expected_ratio: float = Field(..., gt=0.0)
    observed_ratio: float = Field(..., gt=0.0)
    within_tolerance: bool


class TargetedHeavyLightPairObservation(JsonModel):
    """Observed heavy/light pairing and interference behavior."""

    model_config = ConfigDict(extra="forbid")

    pair_id: str = Field(..., min_length=1)
    light_candidate_id: str = Field(..., min_length=1)
    heavy_candidate_id: str = Field(..., min_length=1)
    pair_complete: bool
    heavy_light_ratio: float | None = Field(default=None, gt=0.0)
    interference_fraction: float = Field(..., ge=0.0, le=1.0)


class TargetedWorkflowBenchmarkReport(JsonModel):
    """Targeted workflow benchmark over calibration, pairing, and interference."""

    model_config = ConfigDict(extra="forbid")

    calibration_supported_count: int = Field(..., ge=0)
    calibration_failed_count: int = Field(..., ge=0)
    complete_heavy_light_pair_count: int = Field(..., ge=0)
    missing_heavy_light_pair_count: int = Field(..., ge=0)
    interference_flag_count: int = Field(..., ge=0)
    ready_for_transition_handoff: bool
    note: str = Field(..., min_length=1)


def build_targeted_workflow_benchmark_report(
    *,
    calibration_observations: tuple[TargetedCalibrationStandardObservation, ...],
    heavy_light_pairs: tuple[TargetedHeavyLightPairObservation, ...],
    max_interference_fraction: float = 0.15,
) -> TargetedWorkflowBenchmarkReport:
    """Benchmark targeted support against calibration, pairing, and interference pressure."""

    calibration_supported = sum(
        1 for observation in calibration_observations if observation.within_tolerance
    )
    calibration_failed = len(calibration_observations) - calibration_supported
    complete_pairs = sum(1 for pair in heavy_light_pairs if pair.pair_complete)
    missing_pairs = len(heavy_light_pairs) - complete_pairs
    interference_flag_count = sum(
        1
        for pair in heavy_light_pairs
        if pair.interference_fraction > max_interference_fraction
    )
    ready = (
        calibration_failed == 0
        and missing_pairs == 0
        and interference_flag_count == 0
        and bool(calibration_observations)
        and bool(heavy_light_pairs)
    )
    return TargetedWorkflowBenchmarkReport(
        calibration_supported_count=calibration_supported,
        calibration_failed_count=calibration_failed,
        complete_heavy_light_pair_count=complete_pairs,
        missing_heavy_light_pair_count=missing_pairs,
        interference_flag_count=interference_flag_count,
        ready_for_transition_handoff=ready,
        note=(
            "targeted workflow clears calibration, heavy/light pairing, and interference pressure"
            if ready
            else "targeted workflow remains limited by calibration failure, incomplete pairing, or transition interference"
        ),
    )
