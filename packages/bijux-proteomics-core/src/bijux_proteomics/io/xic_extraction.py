# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Extract precursor XIC traces directly from mzML spectrum peaks."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field, ValidationError, field_validator, model_validator

from bijux_proteomics.io.mzml_reader import stream_mzml_spectra
from bijux_proteomics.tabular import (
    DelimitedColumnSpec,
    DelimitedTableIssue,
    parse_delimited_table,
)
from bijux_proteomics_foundation import JsonModel


class XicToleranceUnit(StrEnum):
    """Supported precursor-window tolerance units."""

    DALTON = "da"
    PPM = "ppm"


class XicTargetEntry(JsonModel):
    """One precursor target to extract from mzML spectra."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    precursor_mz: float = Field(..., gt=0.0)
    rt_start_seconds: float | None = Field(default=None, ge=0.0)
    rt_end_seconds: float | None = Field(default=None, ge=0.0)
    expected_charge: int | None = Field(default=None, ge=1)
    display_name: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("target_id", "display_name", mode="before")
    @classmethod
    def _strip_text(cls, value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @model_validator(mode="after")
    def _validate_retention_window(self) -> XicTargetEntry:
        if (
            self.rt_start_seconds is not None
            and self.rt_end_seconds is not None
            and self.rt_start_seconds > self.rt_end_seconds
        ):
            raise ValueError("rt_start_seconds cannot exceed rt_end_seconds")
        return self


class XicTargetRejectedRow(JsonModel):
    """One rejected XIC target row with explicit stable reason."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=1)
    values: dict[str, str] = Field(default_factory=dict)
    reason: str = Field(..., min_length=1)


class XicTargetParseReport(JsonModel):
    """Stable parse report for one XIC target precursor table."""

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(..., min_length=1)
    accepted_entries: tuple[XicTargetEntry, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[XicTargetRejectedRow, ...] = Field(default_factory=tuple)


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


def parse_xic_target_table(path: Path) -> XicTargetParseReport:
    """Parse one precursor-target table for mzML XIC extraction."""

    table_report = parse_delimited_table(
        path,
        column_specs=(
            DelimitedColumnSpec(name="target_id", source_columns=("id",)),
            DelimitedColumnSpec(name="precursor_mz", source_columns=("mz", "q1")),
            DelimitedColumnSpec(
                name="rt_start_seconds",
                source_columns=("rt_start", "rt_window_start"),
            ),
            DelimitedColumnSpec(
                name="rt_end_seconds",
                source_columns=("rt_end", "rt_window_end"),
            ),
            DelimitedColumnSpec(
                name="expected_charge",
                source_columns=("charge", "precursor_charge"),
            ),
            DelimitedColumnSpec(name="display_name", source_columns=("name",)),
        ),
    )
    accepted_entries: list[XicTargetEntry] = []
    rejected_rows = [
        XicTargetRejectedRow(
            row_number=row.row_number,
            values=row.raw_values,
            reason=_stable_reason_from_issues(row.issues),
        )
        for row in table_report.rejected_rows
    ]
    fieldnames = set(table_report.header)
    seen_target_ids: set[str] = set()
    for accepted_row in table_report.accepted_rows:
        normalized_row = _render_table_row_values(accepted_row.values, accepted_row.extra_values)
        try:
            entry = _parse_xic_target_row(normalized_row, fieldnames)
            if entry.target_id in seen_target_ids:
                raise ValueError(f"duplicate target_id {entry.target_id!r}")
            seen_target_ids.add(entry.target_id)
            accepted_entries.append(entry)
        except (ValueError, ValidationError) as exc:
            rejected_rows.append(
                XicTargetRejectedRow(
                    row_number=accepted_row.row_number,
                    values=normalized_row,
                    reason=_stable_reason(exc),
                )
            )
    return XicTargetParseReport(
        source_path=str(path),
        accepted_entries=tuple(accepted_entries),
        rejected_rows=tuple(rejected_rows),
    )


def extract_mzml_xic_traces(
    mzml_path: Path,
    targets: Path | XicTargetParseReport | tuple[XicTargetEntry, ...],
    *,
    tolerance_da: float | None = None,
    tolerance_ppm: float | None = None,
    ms_level: int = 1,
) -> XicTraceReport:
    """Extract precursor XIC traces from mzML spectra for one target set."""

    if ms_level <= 0:
        raise ValueError("ms_level must be greater than zero")
    target_report = _coerce_target_report(targets)
    tolerance_unit, tolerance_value = _resolve_tolerance(
        tolerance_da=tolerance_da,
        tolerance_ppm=tolerance_ppm,
    )
    trace_points: list[XicTracePoint] = []
    total_spectra = 0
    eligible_spectra = 0
    for spectrum in stream_mzml_spectra(mzml_path):
        total_spectra += 1
        if spectrum.ms_level != ms_level or spectrum.retention_time_seconds is None:
            continue
        eligible_spectra += 1
        time_seconds = spectrum.retention_time_seconds
        for target in target_report.accepted_entries:
            if target.rt_start_seconds is not None and time_seconds < target.rt_start_seconds:
                continue
            if target.rt_end_seconds is not None and time_seconds > target.rt_end_seconds:
                continue
            mz_window_lower, mz_window_upper = _mz_window(
                target.precursor_mz,
                tolerance_unit=tolerance_unit,
                tolerance_value=tolerance_value,
            )
            matched_peaks = tuple(
                peak
                for peak in spectrum.peaks
                if mz_window_lower <= peak.mz <= mz_window_upper
            )
            trace_points.append(
                XicTracePoint(
                    target_id=target.target_id,
                    spectrum_id=spectrum.spectrum_id,
                    time_seconds=time_seconds,
                    precursor_mz=target.precursor_mz,
                    mz_window_lower=mz_window_lower,
                    mz_window_upper=mz_window_upper,
                    intensity=sum(peak.intensity for peak in matched_peaks),
                    matched_peak_count=len(matched_peaks),
                )
            )
    return XicTraceReport(
        source_path=str(mzml_path),
        target_source_path=target_report.source_path,
        tolerance_unit=tolerance_unit,
        tolerance_value=tolerance_value,
        extracted_ms_level=ms_level,
        total_spectra=total_spectra,
        eligible_spectra=eligible_spectra,
        accepted_targets=target_report.accepted_entries,
        rejected_target_rows=target_report.rejected_rows,
        trace_points=tuple(trace_points),
    )


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


def _parse_xic_target_row(
    row: dict[str, str],
    fieldnames: set[str],
) -> XicTargetEntry:
    target_id = row.get("target_id") or row.get("id") or None
    precursor_mz = row.get("precursor_mz") or row.get("mz") or row.get("q1") or None
    if target_id is None:
        raise ValueError("target row requires target_id")
    if precursor_mz is None:
        raise ValueError("target row requires precursor_mz")
    metadata = {
        key: value
        for key, value in row.items()
        if key in fieldnames
        and key
        not in {
            "target_id",
            "id",
            "precursor_mz",
            "mz",
            "q1",
            "rt_start_seconds",
            "rt_start",
            "rt_window_start",
            "rt_end_seconds",
            "rt_end",
            "rt_window_end",
            "expected_charge",
            "charge",
            "precursor_charge",
            "display_name",
            "name",
        }
        and value
    }
    return XicTargetEntry(
        target_id=target_id,
        precursor_mz=float(precursor_mz),
        rt_start_seconds=_optional_float(
            row.get("rt_start_seconds") or row.get("rt_start") or row.get("rt_window_start")
        ),
        rt_end_seconds=_optional_float(
            row.get("rt_end_seconds") or row.get("rt_end") or row.get("rt_window_end")
        ),
        expected_charge=_optional_int(
            row.get("expected_charge") or row.get("charge") or row.get("precursor_charge")
        ),
        display_name=row.get("display_name") or row.get("name") or None,
        metadata=metadata,
    )


def _coerce_target_report(
    targets: Path | XicTargetParseReport | tuple[XicTargetEntry, ...],
) -> XicTargetParseReport:
    if isinstance(targets, Path):
        return parse_xic_target_table(targets)
    if isinstance(targets, XicTargetParseReport):
        return targets
    return XicTargetParseReport(
        source_path="<in-memory>",
        accepted_entries=targets,
        rejected_rows=(),
    )


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


def _optional_float(value: str | None) -> float | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    return float(stripped)


def _optional_int(value: str | None) -> int | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    return int(stripped)


def _stable_reason(error: ValueError | ValidationError) -> str:
    if isinstance(error, ValidationError):
        issues = error.errors()
        if issues:
            message = issues[0].get("msg")
            if isinstance(message, str):
                return message.removeprefix("Value error, ")
    return str(error)


def _stable_reason_from_issues(issues: tuple[DelimitedTableIssue, ...]) -> str:
    if not issues:
        return "xic target row was rejected"
    if any(issue.code == "empty_table" for issue in issues):
        return "xic target table is empty"
    return issues[0].message


def _render_table_row_values(
    values: dict[str, str | int | float | bool | None],
    extra_values: dict[str, str],
) -> dict[str, str]:
    rendered: dict[str, str] = dict(extra_values)
    for key, value in values.items():
        rendered[key] = "" if value is None else str(value)
    return rendered
