# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from .core_algorithm_benchmark_support import CORE_ALGORITHM_BENCHMARK_CASES


def test_core_algorithm_benchmark_cases_cover_required_algorithms() -> None:
    assert set(CORE_ALGORITHM_BENCHMARK_CASES) == {
        "digest",
        "peptide_index",
        "fdr",
        "matrix_rollup",
        "enrichment",
        "graph_query",
    }


def test_core_algorithm_benchmark_cases_preserve_governed_workload_units() -> None:
    workload_units = {
        algorithm_id: case.workload_unit
        for algorithm_id, case in CORE_ALGORITHM_BENCHMARK_CASES.items()
    }

    assert workload_units == {
        "digest": "proteins",
        "peptide_index": "proteins",
        "fdr": "psms",
        "matrix_rollup": "protein_targets",
        "enrichment": "membership_rows",
        "graph_query": "protein_queries",
    }
