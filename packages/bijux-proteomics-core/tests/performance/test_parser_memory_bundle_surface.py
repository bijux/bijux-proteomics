# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from .parser_memory_benchmark_support import (
    benchmark_diann_import_memory,
    benchmark_maxquant_import_memory,
)


def test_generated_large_diann_import_stays_below_memory_ceiling(tmp_path) -> None:
    report = benchmark_diann_import_memory(tmp_path)

    assert report.parser_id == "diann_import"
    assert report.generated_unit_count == 4_000
    assert report.ceiling_respected is True
    assert report.memory_headroom_mb >= 0.0


def test_generated_large_maxquant_import_stays_below_memory_ceiling(tmp_path) -> None:
    report = benchmark_maxquant_import_memory(tmp_path)

    assert report.parser_id == "maxquant_import"
    assert report.generated_unit_count == 4_000
    assert report.ceiling_respected is True
    assert report.memory_headroom_mb >= 0.0
