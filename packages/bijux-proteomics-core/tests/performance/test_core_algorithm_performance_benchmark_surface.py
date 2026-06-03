# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.benchmarks import (
    CoreAlgorithmPerformanceBenchmarkInput,
    build_core_algorithm_performance_benchmark_report,
)


def test_build_core_algorithm_performance_benchmark_report_tracks_runtime_headroom() -> (
    None
):
    report = build_core_algorithm_performance_benchmark_report(
        CoreAlgorithmPerformanceBenchmarkInput(
            algorithm_id="digest",
            workload_unit="proteins",
            generated_unit_count=1_600,
            observed_seconds=0.48,
            baseline_seconds=0.40,
            regression_threshold_ratio=3.0,
        )
    )

    assert report.threshold_seconds == 1.2
    assert report.slowdown_ratio == 1.2
    assert report.regression_detected is False
    assert report.units_per_second > 3_000


def test_build_core_algorithm_performance_benchmark_report_flags_regression() -> None:
    report = build_core_algorithm_performance_benchmark_report(
        CoreAlgorithmPerformanceBenchmarkInput(
            algorithm_id="matrix_rollup",
            workload_unit="protein_targets",
            generated_unit_count=1_200,
            observed_seconds=4.0,
            baseline_seconds=1.2,
            regression_threshold_ratio=3.0,
        )
    )

    assert report.threshold_seconds == 3.6
    assert report.slowdown_ratio > 3.0
    assert report.regression_detected is True
