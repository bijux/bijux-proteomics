# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Calibration-aware benchmarks for target-decoy generation strategies."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.fdr.confidence import (
    EmpiricalScoreCalibrationReport,
    build_empirical_score_calibration_report,
)
from bijux_proteomics.identification.contracts import PsmRecord
from bijux_proteomics.sequences.core import (
    DecoyGenerationMode,
    NormalizedProteinRecord,
    build_decoy_generation_manifest,
    generate_decoy_records,
    validate_target_decoy_database,
)
from bijux_proteomics_foundation import JsonModel


class TargetDecoyCalibrationBenchmarkInput(JsonModel):
    """One target-decoy calibration benchmark fixture."""

    model_config = ConfigDict(extra="forbid")

    benchmark_id: str = Field(..., min_length=1)
    decoy_mode: DecoyGenerationMode
    target_records: tuple[NormalizedProteinRecord, ...] = Field(default_factory=tuple)
    psm_records: tuple[PsmRecord, ...] = Field(default_factory=tuple)
    prefix: str = Field(default="DECOY_", min_length=1)
    seed: int = Field(default=17, ge=0)


class TargetDecoyCalibrationBenchmarkEntry(JsonModel):
    """One benchmarked decoy-generation strategy with calibration evidence."""

    model_config = ConfigDict(extra="forbid")

    benchmark_id: str = Field(..., min_length=1)
    decoy_mode: DecoyGenerationMode
    reproducibility_hash: str = Field(..., min_length=64, max_length=64)
    database_valid: bool
    target_count: int = Field(..., ge=0)
    decoy_count: int = Field(..., ge=0)
    top_fraction_decoy_share: float = Field(..., ge=0.0, le=1.0)
    top_fraction_decoy_interval_width: float = Field(..., ge=0.0, le=1.0)
    calibration_advisory: str = Field(..., min_length=1)
    calibration_report: EmpiricalScoreCalibrationReport


class TargetDecoyCalibrationBenchmarkReport(JsonModel):
    """Cross-strategy target-decoy benchmark report."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[TargetDecoyCalibrationBenchmarkEntry, ...] = Field(
        default_factory=tuple
    )
    release_blocked: bool
    blocked_benchmarks: tuple[str, ...] = Field(default_factory=tuple)


def build_target_decoy_calibration_benchmark_report(
    inputs: tuple[TargetDecoyCalibrationBenchmarkInput, ...],
    *,
    score_orientation: str = "higher_better",
) -> TargetDecoyCalibrationBenchmarkReport:
    """Benchmark decoy-generation modes on both database validity and calibration behavior."""

    entries: list[TargetDecoyCalibrationBenchmarkEntry] = []
    blocked: list[str] = []
    for payload in inputs:
        decoys = generate_decoy_records(
            payload.target_records,
            mode=payload.decoy_mode,
            prefix=payload.prefix,
            seed=payload.seed,
        )
        combined_records = (*payload.target_records, *decoys)
        manifest = build_decoy_generation_manifest(
            input_records=payload.target_records,
            output_records=decoys,
            mode=payload.decoy_mode,
            prefix=payload.prefix,
            seed=payload.seed,
            source_path=None,
        )
        validation = validate_target_decoy_database(
            tuple(combined_records),
            prefix=payload.prefix,
        )
        calibration = build_empirical_score_calibration_report(
            payload.psm_records,
            score_orientation=score_orientation,
        )
        if not validation.valid:
            blocked.append(payload.benchmark_id)
        entries.append(
            TargetDecoyCalibrationBenchmarkEntry(
                benchmark_id=payload.benchmark_id,
                decoy_mode=payload.decoy_mode,
                reproducibility_hash=manifest.reproducibility_hash,
                database_valid=validation.valid,
                target_count=validation.target_count,
                decoy_count=validation.decoy_count,
                top_fraction_decoy_share=calibration.top_fraction_decoy_share,
                top_fraction_decoy_interval_width=calibration.top_fraction_decoy_interval_width,
                calibration_advisory=calibration.advisory,
                calibration_report=calibration,
            )
        )
    return TargetDecoyCalibrationBenchmarkReport(
        entries=tuple(entries),
        release_blocked=bool(blocked),
        blocked_benchmarks=tuple(blocked),
    )
