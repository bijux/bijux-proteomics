# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.scale_iteration17 import (
    DenseQuantMatrixBenchmarkInput,
    build_dense_quant_matrix_benchmark_report,
)


def test_build_dense_quant_matrix_benchmark_report_tracks_cells_and_bottleneck() -> (
    None
):
    report = build_dense_quant_matrix_benchmark_report(
        DenseQuantMatrixBenchmarkInput(
            matrix_rows=40_000,
            matrix_columns=120,
            normalization_seconds=12.0,
            rollup_seconds=19.0,
            missingness_seconds=8.0,
            da_prep_seconds=6.0,
            peak_memory_mb=2048.0,
            output_size_mb=512.0,
        )
    )

    assert report.matrix_cells == 4_800_000
    assert report.bottleneck_stage == "rollup"
