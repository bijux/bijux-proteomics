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
