# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from .core_algorithm_benchmark_support import (
    CORE_ALGORITHM_BENCHMARK_CASES,
    benchmark_digest_runtime,
    benchmark_peptide_index_runtime,
)


def test_digest_runtime_stays_within_baseline_threshold() -> None:
    report = benchmark_digest_runtime()

    assert report.algorithm_id == "digest"
    assert report.workload_unit == "proteins"
    assert report.generated_unit_count == CORE_ALGORITHM_BENCHMARK_CASES["digest"].generated_unit_count
    assert report.regression_detected is False


def test_peptide_index_runtime_stays_within_baseline_threshold() -> None:
    report = benchmark_peptide_index_runtime()

    assert report.algorithm_id == "peptide_index"
    assert report.workload_unit == "proteins"
    assert report.generated_unit_count == CORE_ALGORITHM_BENCHMARK_CASES["peptide_index"].generated_unit_count
    assert report.regression_detected is False
