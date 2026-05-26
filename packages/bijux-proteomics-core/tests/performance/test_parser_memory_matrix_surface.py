# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from .parser_memory_benchmark_support import (
    benchmark_ms1_feature_table_memory,
    benchmark_transition_table_matrix_memory,
)


def test_generated_large_ms1_feature_table_stays_below_memory_ceiling(
    tmp_path,
) -> None:
    report = benchmark_ms1_feature_table_memory(tmp_path)

    assert report.parser_id == "ms1_feature_table"
    assert report.generated_unit_count == 8_000
    assert report.ceiling_respected is True
    assert report.memory_headroom_mb >= 0.0


def test_generated_large_transition_table_stays_below_memory_ceiling(tmp_path) -> None:
    report = benchmark_transition_table_matrix_memory(tmp_path)

    assert report.parser_id == "transition_table_matrix"
    assert report.generated_unit_count == 8_000
    assert report.ceiling_respected is True
    assert report.memory_headroom_mb >= 0.0
