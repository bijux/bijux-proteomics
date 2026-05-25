# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""mzML-backed XIC extraction wrappers over typed XIC algorithms."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.chromatography.xic import (
    XicTargetEntry,
    XicTracePoint,
    XicTraceReport,
    _matched_peak_count,
    _resolve_tolerance,
    extract_xic,
)
from bijux_proteomics.io.raw.mzml_reader import stream_mzml_spectra
from bijux_proteomics.io.spectra import SpectrumModel
from bijux_proteomics.io.tables.xic_target_table import (
    XicTargetParseReport,
    coerce_xic_target_report,
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
    target_report = coerce_xic_target_report(targets)
    tolerance_unit, tolerance_value = _resolve_tolerance(
        tolerance_da=tolerance_da,
        tolerance_ppm=tolerance_ppm,
    )
    total_spectra = 0
    eligible_spectra = 0
    eligible_spectra_buffer: list[SpectrumModel] = []
    for spectrum in stream_mzml_spectra(mzml_path):
        total_spectra += 1
        if spectrum.ms_level != ms_level or spectrum.retention_time_seconds is None:
            continue
        eligible_spectra += 1
        eligible_spectra_buffer.append(spectrum)
    extraction_rows = extract_xic(
        eligible_spectra_buffer,
        target_report.accepted_entries,
        tolerance=tolerance_value,
        tolerance_unit=tolerance_unit,
        ms_level=ms_level,
    )
    spectra_by_id = {
        spectrum.spectrum_id: spectrum for spectrum in eligible_spectra_buffer
    }
    targets_by_id = {
        target.target_id: target for target in target_report.accepted_entries
    }
    trace_points = tuple(
        XicTracePoint(
            target_id=row.target_id,
            spectrum_id=row.scan_id,
            time_seconds=row.rt,
            precursor_mz=targets_by_id[row.target_id].precursor_mz,
            mz_window_lower=row.mz_lower,
            mz_window_upper=row.mz_upper,
            intensity=row.intensity,
            matched_peak_count=_matched_peak_count(
                spectra_by_id[row.scan_id],
                row,
            ),
        )
        for row in extraction_rows
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
        trace_points=trace_points,
    )
