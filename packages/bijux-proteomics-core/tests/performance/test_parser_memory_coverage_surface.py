# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from . import parser_memory_benchmark_support as support


def test_parser_memory_benchmark_cases_cover_required_parser_families() -> None:
    assert set(support.PARSER_MEMORY_BENCHMARK_CASES) == {
        "mgf_streaming",
        "mzml_streaming",
        "diann_import",
        "maxquant_import",
        "fragpipe_import",
        "ms1_feature_table",
        "transition_table_matrix",
    }


def test_parser_memory_benchmark_cases_match_benchmark_helpers() -> None:
    benchmark_helpers = {
        "mgf_streaming": support.benchmark_mgf_streaming_memory,
        "mzml_streaming": support.benchmark_mzml_streaming_memory,
        "diann_import": support.benchmark_diann_import_memory,
        "maxquant_import": support.benchmark_maxquant_import_memory,
        "fragpipe_import": support.benchmark_fragpipe_import_memory,
        "ms1_feature_table": support.benchmark_ms1_feature_table_memory,
        "transition_table_matrix": support.benchmark_transition_table_matrix_memory,
    }

    assert set(benchmark_helpers) == set(support.PARSER_MEMORY_BENCHMARK_CASES)

    for parser_id, case in support.PARSER_MEMORY_BENCHMARK_CASES.items():
        assert case.parser_id == parser_id
        assert case.generated_unit_count > 0
        assert case.memory_ceiling_mb > 0.0
        assert case.workload_unit == "spectra" or case.workload_unit == "rows"
        assert callable(benchmark_helpers[parser_id])
