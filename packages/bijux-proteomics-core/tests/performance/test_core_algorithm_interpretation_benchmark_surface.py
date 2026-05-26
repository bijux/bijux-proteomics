# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from .core_algorithm_benchmark_support import (
    CORE_ALGORITHM_BENCHMARK_CASES,
    benchmark_enrichment_runtime,
    benchmark_graph_query_runtime,
)


def test_enrichment_runtime_stays_within_baseline_threshold() -> None:
    report = benchmark_enrichment_runtime()

    assert report.algorithm_id == "enrichment"
    assert report.workload_unit == "membership_rows"
    assert report.generated_unit_count == CORE_ALGORITHM_BENCHMARK_CASES["enrichment"].generated_unit_count
    assert report.regression_detected is False


def test_graph_query_runtime_stays_within_baseline_threshold(tmp_path: Path) -> None:
    report = benchmark_graph_query_runtime(tmp_path)

    assert report.algorithm_id == "graph_query"
    assert report.workload_unit == "protein_queries"
    assert report.generated_unit_count == CORE_ALGORITHM_BENCHMARK_CASES["graph_query"].generated_unit_count
    assert report.regression_detected is False
