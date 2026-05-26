# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from .core_algorithm_benchmark_support import (
    CORE_ALGORITHM_BENCHMARK_CASES,
    benchmark_matrix_rollup_runtime,
    benchmark_psm_fdr_runtime,
)


def test_psm_fdr_runtime_stays_within_baseline_threshold() -> None:
    report = benchmark_psm_fdr_runtime()

    assert report.algorithm_id == "fdr"
    assert report.workload_unit == "psms"
    assert report.generated_unit_count == CORE_ALGORITHM_BENCHMARK_CASES["fdr"].generated_unit_count
    assert report.regression_detected is False


def test_matrix_rollup_runtime_stays_within_baseline_threshold() -> None:
    report = benchmark_matrix_rollup_runtime()

    assert report.algorithm_id == "matrix_rollup"
    assert report.workload_unit == "protein_targets"
    assert report.generated_unit_count == CORE_ALGORITHM_BENCHMARK_CASES["matrix_rollup"].generated_unit_count
    assert report.regression_detected is False
