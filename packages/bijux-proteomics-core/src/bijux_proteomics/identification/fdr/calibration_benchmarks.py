# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Benchmark surfaces for adapter-family calibration scrutiny."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.contracts import (
    PsmRecord,
    normalize_psm_score_orientation,
)
from bijux_proteomics.identification.fdr.confidence import (
    EmpiricalScoreCalibrationReport,
    EntrapmentEvaluationReport,
    build_empirical_score_calibration_report,
    build_entrapment_evaluation_report,
)
from bijux_proteomics.identification.search_adapters import SearchAdapterKind
from bijux_proteomics_foundation.serialization.json_contracts import JsonModel


class AdapterCalibrationBenchmarkInput(JsonModel):
    """One adapter-family input for a calibration benchmark suite."""

    model_config = ConfigDict(extra="forbid")

    adapter_kind: SearchAdapterKind
    records: tuple[PsmRecord, ...] = Field(default_factory=tuple)
    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    entrapment_protein_refs: tuple[str, ...] = Field(default_factory=tuple)


class AdapterCalibrationBenchmarkEntry(JsonModel):
    """Calibration benchmark result for one adapter family."""

    model_config = ConfigDict(extra="forbid")

    adapter_kind: SearchAdapterKind
    total_record_count: int = Field(..., ge=0)
    accepted_record_count: int = Field(..., ge=0)
    q_value_monotonic: bool
    calibration: EmpiricalScoreCalibrationReport
    entrapment: EntrapmentEvaluationReport


class AdapterCalibrationBenchmarkSuiteReport(JsonModel):
    """Adapter-family calibration suite across multiple benchmark inputs."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[AdapterCalibrationBenchmarkEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


def _q_values_are_monotonic(
    records: tuple[PsmRecord, ...],
    *,
    score_orientation: str,
) -> bool:
    normalized = normalize_psm_score_orientation(
        records,
        score_orientation=score_orientation,
    )
    record_by_spectrum = {record.spectrum_id: record for record in records}
    ranked_q_values: list[float] = []
    for entry in normalized:
        q_value = record_by_spectrum[entry.spectrum_id].q_value
        if q_value is not None:
            ranked_q_values.append(q_value)
    return all(
        left <= right
        for left, right in zip(ranked_q_values, ranked_q_values[1:], strict=False)
    )


def build_adapter_calibration_benchmark_suite(
    inputs: tuple[AdapterCalibrationBenchmarkInput, ...],
    *,
    accepted_q_value_threshold: float = 0.01,
    bin_count: int = 8,
    top_fraction: float = 0.1,
) -> AdapterCalibrationBenchmarkSuiteReport:
    """Build empirical calibration proof across multiple adapter families."""
    entries = tuple(
        AdapterCalibrationBenchmarkEntry(
            adapter_kind=item.adapter_kind,
            total_record_count=len(item.records),
            accepted_record_count=sum(
                record.q_value is not None
                and record.q_value <= accepted_q_value_threshold
                for record in item.records
            ),
            q_value_monotonic=_q_values_are_monotonic(
                item.records,
                score_orientation=item.score_orientation,
            ),
            calibration=build_empirical_score_calibration_report(
                item.records,
                score_orientation=item.score_orientation,
                bin_count=bin_count,
                top_fraction=top_fraction,
            ),
            entrapment=build_entrapment_evaluation_report(
                item.records,
                entrapment_protein_refs=item.entrapment_protein_refs,
                accepted_q_value_threshold=accepted_q_value_threshold,
            ),
        )
        for item in inputs
    )
    note = (
        "adapter-family calibration suite keeps score orientation, q-value ordering, decoy pressure, and entrapment evidence explicit across benchmark inputs"
        if entries
        else "adapter-family calibration suite has no inputs to evaluate"
    )
    return AdapterCalibrationBenchmarkSuiteReport(entries=entries, note=note)


__all__ = [
    "AdapterCalibrationBenchmarkEntry",
    "AdapterCalibrationBenchmarkInput",
    "AdapterCalibrationBenchmarkSuiteReport",
    "build_adapter_calibration_benchmark_suite",
]
