# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.scale_iteration17 import (
    MillionPsmIngestionBenchmarkInput,
    build_million_psm_ingestion_benchmark_report,
)


def test_build_million_psm_ingestion_benchmark_report_computes_throughput() -> None:
    report = build_million_psm_ingestion_benchmark_report(
        MillionPsmIngestionBenchmarkInput(
            psm_count=1_000_000,
            parse_seconds=20.0,
            normalize_seconds=18.0,
            fdr_seconds=25.0,
            trace_export_seconds=10.0,
            peak_memory_mb=3072.0,
        )
    )

    assert report.total_seconds == 73.0
    assert report.throughput_psm_per_second > 13_000
    assert report.bottleneck_stage == "fdr"
