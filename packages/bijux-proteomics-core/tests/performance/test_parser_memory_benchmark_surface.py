# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.benchmarks import (
    ParserMemoryBenchmarkInput,
    build_parser_memory_benchmark_report,
)


def test_build_parser_memory_benchmark_report_tracks_ceiling_headroom() -> None:
    report = build_parser_memory_benchmark_report(
        ParserMemoryBenchmarkInput(
            parser_id="diann_import",
            workload_unit="rows",
            generated_unit_count=12_000,
            input_size_mb=8.4,
            peak_memory_mb=42.5,
            memory_ceiling_mb=64.0,
        )
    )

    assert report.parser_id == "diann_import"
    assert report.ceiling_respected is True
    assert report.memory_headroom_mb == 21.5
    assert report.memory_per_unit_kb > 0.0


def test_build_parser_memory_benchmark_report_flags_ceiling_breach() -> None:
    report = build_parser_memory_benchmark_report(
        ParserMemoryBenchmarkInput(
            parser_id="transition_table_matrix",
            workload_unit="rows",
            generated_unit_count=5_000,
            input_size_mb=3.2,
            peak_memory_mb=33.0,
            memory_ceiling_mb=24.0,
        )
    )

    assert report.ceiling_respected is False
    assert report.memory_headroom_mb == -9.0
