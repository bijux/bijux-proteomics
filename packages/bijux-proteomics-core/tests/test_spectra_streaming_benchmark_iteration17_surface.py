# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.scale_iteration17 import (
    LargeSpectraStreamingBenchmarkInput,
    build_large_spectra_streaming_benchmark_report,
)


def test_build_large_spectra_streaming_benchmark_report_computes_throughput() -> None:
    report = build_large_spectra_streaming_benchmark_report(
        LargeSpectraStreamingBenchmarkInput(
            format_name="mzml",
            spectrum_count=2_500_000,
            input_size_mb=9500.0,
            parse_seconds=300.0,
            peak_memory_mb=1536.0,
        )
    )

    assert report.throughput_spectra_per_second > 8_000
    assert report.throughput_mb_per_second > 30
