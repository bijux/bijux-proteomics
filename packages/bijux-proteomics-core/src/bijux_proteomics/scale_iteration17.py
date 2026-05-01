# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Scale and reproducibility capability surfaces for iteration 17."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class MillionPsmIngestionBenchmarkInput(JsonModel):
    """Timing and memory observations for million-PSM ingestion benchmark."""

    model_config = ConfigDict(extra="forbid")

    psm_count: int = Field(..., ge=1)
    parse_seconds: float = Field(..., gt=0.0)
    normalize_seconds: float = Field(..., gt=0.0)
    fdr_seconds: float = Field(..., gt=0.0)
    trace_export_seconds: float = Field(..., gt=0.0)
    peak_memory_mb: float = Field(..., gt=0.0)


class MillionPsmIngestionBenchmarkReport(JsonModel):
    """Benchmark report for parsing/normalization/FDR/trace export at million-PSM scale."""

    model_config = ConfigDict(extra="forbid")

    psm_count: int = Field(..., ge=1)
    total_seconds: float = Field(..., gt=0.0)
    throughput_psm_per_second: float = Field(..., gt=0.0)
    peak_memory_mb: float = Field(..., gt=0.0)
    bottleneck_stage: str = Field(..., min_length=1)


def build_million_psm_ingestion_benchmark_report(
    payload: MillionPsmIngestionBenchmarkInput,
) -> MillionPsmIngestionBenchmarkReport:
    """Measure parse/normalize/FDR/trace-export throughput for large PSM corpora."""

    stage_durations = {
        "parse": payload.parse_seconds,
        "normalize": payload.normalize_seconds,
        "fdr": payload.fdr_seconds,
        "trace_export": payload.trace_export_seconds,
    }
    total_seconds = sum(stage_durations.values())
    throughput = payload.psm_count / total_seconds
    bottleneck_stage = max(stage_durations.items(), key=lambda row: row[1])[0]

    return MillionPsmIngestionBenchmarkReport(
        psm_count=payload.psm_count,
        total_seconds=total_seconds,
        throughput_psm_per_second=throughput,
        peak_memory_mb=payload.peak_memory_mb,
        bottleneck_stage=bottleneck_stage,
    )


class DenseQuantMatrixBenchmarkInput(JsonModel):
    """Timing and memory observations for dense quantification-matrix workloads."""

    model_config = ConfigDict(extra="forbid")

    matrix_rows: int = Field(..., ge=1)
    matrix_columns: int = Field(..., ge=1)
    normalization_seconds: float = Field(..., gt=0.0)
    rollup_seconds: float = Field(..., gt=0.0)
    missingness_seconds: float = Field(..., gt=0.0)
    da_prep_seconds: float = Field(..., gt=0.0)
    peak_memory_mb: float = Field(..., gt=0.0)
    output_size_mb: float = Field(..., gt=0.0)


class DenseQuantMatrixBenchmarkReport(JsonModel):
    """Benchmark report for dense quant normalization/rollup/missingness/DA prep."""

    model_config = ConfigDict(extra="forbid")

    matrix_rows: int = Field(..., ge=1)
    matrix_columns: int = Field(..., ge=1)
    matrix_cells: int = Field(..., ge=1)
    total_seconds: float = Field(..., gt=0.0)
    cells_per_second: float = Field(..., gt=0.0)
    peak_memory_mb: float = Field(..., gt=0.0)
    output_size_mb: float = Field(..., gt=0.0)
    bottleneck_stage: str = Field(..., min_length=1)


def build_dense_quant_matrix_benchmark_report(
    payload: DenseQuantMatrixBenchmarkInput,
) -> DenseQuantMatrixBenchmarkReport:
    """Measure dense quant matrix normalization/rollup/missingness/DA-prep performance."""

    stage_durations = {
        "normalization": payload.normalization_seconds,
        "rollup": payload.rollup_seconds,
        "missingness": payload.missingness_seconds,
        "da_prep": payload.da_prep_seconds,
    }
    total_seconds = sum(stage_durations.values())
    matrix_cells = payload.matrix_rows * payload.matrix_columns
    cells_per_second = matrix_cells / total_seconds
    bottleneck_stage = max(stage_durations.items(), key=lambda row: row[1])[0]
    return DenseQuantMatrixBenchmarkReport(
        matrix_rows=payload.matrix_rows,
        matrix_columns=payload.matrix_columns,
        matrix_cells=matrix_cells,
        total_seconds=total_seconds,
        cells_per_second=cells_per_second,
        peak_memory_mb=payload.peak_memory_mb,
        output_size_mb=payload.output_size_mb,
        bottleneck_stage=bottleneck_stage,
    )


class LargeSpectraStreamingBenchmarkInput(JsonModel):
    """Observed metrics for large MGF/mzML streaming parse workloads."""

    model_config = ConfigDict(extra="forbid")

    format_name: str = Field(..., min_length=1)
    spectrum_count: int = Field(..., ge=1)
    input_size_mb: float = Field(..., gt=0.0)
    parse_seconds: float = Field(..., gt=0.0)
    peak_memory_mb: float = Field(..., gt=0.0)


class LargeSpectraStreamingBenchmarkReport(JsonModel):
    """Benchmark report for large spectra streaming throughput and memory behavior."""

    model_config = ConfigDict(extra="forbid")

    format_name: str = Field(..., min_length=1)
    spectrum_count: int = Field(..., ge=1)
    throughput_spectra_per_second: float = Field(..., gt=0.0)
    throughput_mb_per_second: float = Field(..., gt=0.0)
    peak_memory_mb: float = Field(..., gt=0.0)


def build_large_spectra_streaming_benchmark_report(
    payload: LargeSpectraStreamingBenchmarkInput,
) -> LargeSpectraStreamingBenchmarkReport:
    """Measure large MGF/mzML streaming throughput and memory footprint."""

    return LargeSpectraStreamingBenchmarkReport(
        format_name=payload.format_name,
        spectrum_count=payload.spectrum_count,
        throughput_spectra_per_second=payload.spectrum_count / payload.parse_seconds,
        throughput_mb_per_second=payload.input_size_mb / payload.parse_seconds,
        peak_memory_mb=payload.peak_memory_mb,
    )


class EvidenceGraphScaleBenchmarkInput(JsonModel):
    """Stage timings for evidence-graph build/query/packet/export at scale."""

    model_config = ConfigDict(extra="forbid")

    node_count: int = Field(..., ge=1)
    edge_count: int = Field(..., ge=0)
    build_seconds: float = Field(..., gt=0.0)
    query_seconds: float = Field(..., gt=0.0)
    packet_seconds: float = Field(..., gt=0.0)
    export_seconds: float = Field(..., gt=0.0)


class EvidenceGraphScaleBenchmarkReport(JsonModel):
    """Scale benchmark report for evidence-graph processing surfaces."""

    model_config = ConfigDict(extra="forbid")

    node_count: int = Field(..., ge=1)
    edge_count: int = Field(..., ge=0)
    total_seconds: float = Field(..., gt=0.0)
    edges_processed_per_second: float = Field(..., gt=0.0)
    bottleneck_stage: str = Field(..., min_length=1)


def build_evidence_graph_scale_benchmark_report(
    payload: EvidenceGraphScaleBenchmarkInput,
) -> EvidenceGraphScaleBenchmarkReport:
    """Measure evidence-graph build/query/review-packet/export bottlenecks."""

    durations = {
        "build": payload.build_seconds,
        "query": payload.query_seconds,
        "packet": payload.packet_seconds,
        "export": payload.export_seconds,
    }
    total = sum(durations.values())
    edges_processed = max(1, payload.edge_count)
    return EvidenceGraphScaleBenchmarkReport(
        node_count=payload.node_count,
        edge_count=payload.edge_count,
        total_seconds=total,
        edges_processed_per_second=edges_processed / total,
        bottleneck_stage=max(durations.items(), key=lambda row: row[1])[0],
    )
