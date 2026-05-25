# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Typed precursor XIC trace contracts and extraction algorithms."""

from __future__ import annotations

from collections.abc import Iterable
import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.io.spectra import SpectrumModel
from bijux_proteomics.io.tables.xic_target_table import (
    XicTargetEntry,
    XicTargetRejectedRow,
)
from bijux_proteomics_foundation import JsonModel


class XicToleranceUnit(StrEnum):
    """Supported precursor-window tolerance units."""

    DALTON = "da"
    PPM = "ppm"


class XicTracePoint(JsonModel):
    """One extracted precursor-trace point for one target at one scan time."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    spectrum_id: str = Field(..., min_length=1)
    time_seconds: float = Field(..., ge=0.0)
    precursor_mz: float = Field(..., gt=0.0)
    mz_window_lower: float = Field(..., gt=0.0)
    mz_window_upper: float = Field(..., gt=0.0)
    intensity: float = Field(..., ge=0.0)
    matched_peak_count: int = Field(..., ge=0)


class XicExtractionPoint(JsonModel):
    """One raw XIC extraction row with the engine output contract."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    rt: float = Field(..., ge=0.0)
    mz_lower: float = Field(..., gt=0.0)
    mz_upper: float = Field(..., gt=0.0)
    intensity: float = Field(..., ge=0.0)
    scan_id: str = Field(..., min_length=1)


class XicTraceReport(JsonModel):
    """Stable extracted XIC traces over one mzML file and target table."""

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(..., min_length=1)
    target_source_path: str = Field(..., min_length=1)
    tolerance_unit: XicToleranceUnit
    tolerance_value: float = Field(..., gt=0.0)
    extracted_ms_level: int = Field(..., ge=1)
    total_spectra: int = Field(..., ge=0)
    eligible_spectra: int = Field(..., ge=0)
    accepted_targets: tuple[XicTargetEntry, ...] = Field(default_factory=tuple)
    rejected_target_rows: tuple[XicTargetRejectedRow, ...] = Field(default_factory=tuple)
    trace_points: tuple[XicTracePoint, ...] = Field(default_factory=tuple)
def render_xic_traces_tsv(report: XicTraceReport) -> str:
    """Render one extracted XIC report into deterministic TSV rows."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "target_id",
            "spectrum_id",
            "time_seconds",
            "precursor_mz",
            "mz_window_lower",
            "mz_window_upper",
            "intensity",
            "matched_peak_count",
        )
    )
    for point in sorted(
        report.trace_points,
        key=lambda item: (item.target_id, item.time_seconds, item.spectrum_id),
    ):
        writer.writerow(
            (
                point.target_id,
                point.spectrum_id,
                f"{point.time_seconds:g}",
                f"{point.precursor_mz:.6f}",
                f"{point.mz_window_lower:.6f}",
                f"{point.mz_window_upper:.6f}",
                f"{point.intensity:g}",
                point.matched_peak_count,
            )
        )
    return buffer.getvalue()


def extract_xic(
    mzml_reader: Iterable[SpectrumModel],
    targets: tuple[XicTargetEntry, ...],
    *,
    tolerance: float,
    tolerance_unit: XicToleranceUnit = XicToleranceUnit.PPM,
    rt_window: float | None = None,
    ms_level: int = 1,
) -> tuple[XicExtractionPoint, ...]:
    """Extract raw XIC rows from one mzML spectrum stream and target set."""

    if tolerance <= 0.0:
        raise ValueError("tolerance must be greater than zero")
    if rt_window is not None and rt_window < 0.0:
        raise ValueError("rt_window must be greater than or equal to zero")
    if ms_level <= 0:
        raise ValueError("ms_level must be greater than zero")
    rows: list[XicExtractionPoint] = []
    for spectrum in mzml_reader:
        if spectrum.ms_level != ms_level or spectrum.retention_time_seconds is None:
            continue
        for target in targets:
            rt_start_seconds, rt_end_seconds = _resolve_target_rt_window(
                target,
                rt_window=rt_window,
            )
            if rt_start_seconds is not None and spectrum.retention_time_seconds < rt_start_seconds:
                continue
            if rt_end_seconds is not None and spectrum.retention_time_seconds > rt_end_seconds:
                continue
            mz_lower, mz_upper = _mz_window(
                target.precursor_mz,
                tolerance_unit=tolerance_unit,
                tolerance_value=tolerance,
            )
            rows.append(
                XicExtractionPoint(
                    target_id=target.target_id,
                    rt=spectrum.retention_time_seconds,
                    mz_lower=mz_lower,
                    mz_upper=mz_upper,
                    intensity=sum(
                        peak.intensity
                        for peak in spectrum.peaks
                        if mz_lower <= peak.mz <= mz_upper
                    ),
                    scan_id=spectrum.spectrum_id,
                )
            )
    return tuple(sorted(rows, key=lambda row: (row.target_id, row.rt, row.scan_id)))


def render_xic_extraction_tsv(rows: tuple[XicExtractionPoint, ...]) -> str:
    """Render raw XIC extraction rows with the engine column contract."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("target_id", "rt", "mz_lower", "mz_upper", "intensity", "scan_id"))
    for row in rows:
        writer.writerow(
            (
                row.target_id,
                f"{row.rt:g}",
                f"{row.mz_lower:.6f}",
                f"{row.mz_upper:.6f}",
                f"{row.intensity:g}",
                row.scan_id,
            )
        )
    return buffer.getvalue()


def _resolve_tolerance(
    *,
    tolerance_da: float | None,
    tolerance_ppm: float | None,
) -> tuple[XicToleranceUnit, float]:
    if tolerance_da is not None and tolerance_ppm is not None:
        raise ValueError("provide either tolerance_da or tolerance_ppm, not both")
    if tolerance_da is not None:
        if tolerance_da <= 0.0:
            raise ValueError("tolerance_da must be greater than zero")
        return XicToleranceUnit.DALTON, tolerance_da
    effective_ppm = 10.0 if tolerance_ppm is None else tolerance_ppm
    if effective_ppm <= 0.0:
        raise ValueError("tolerance_ppm must be greater than zero")
    return XicToleranceUnit.PPM, effective_ppm


def _mz_window(
    precursor_mz: float,
    *,
    tolerance_unit: XicToleranceUnit,
    tolerance_value: float,
) -> tuple[float, float]:
    if tolerance_unit is XicToleranceUnit.DALTON:
        half_width = tolerance_value
    else:
        half_width = precursor_mz * tolerance_value / 1_000_000.0
    return precursor_mz - half_width, precursor_mz + half_width


def _resolve_target_rt_window(
    target: XicTargetEntry,
    *,
    rt_window: float | None,
) -> tuple[float | None, float | None]:
    if target.rt_start_seconds is not None or target.rt_end_seconds is not None:
        return target.rt_start_seconds, target.rt_end_seconds
    if target.rt_expected_seconds is None or rt_window is None:
        return None, None
    return (
        max(0.0, target.rt_expected_seconds - rt_window),
        target.rt_expected_seconds + rt_window,
    )


def _matched_peak_count(
    spectrum: SpectrumModel,
    row: XicExtractionPoint,
) -> int:
    return sum(
        1 for peak in spectrum.peaks if row.mz_lower <= peak.mz <= row.mz_upper
    )
