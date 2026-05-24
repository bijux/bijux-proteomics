# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.chromatographic_peak_picking import (
    pick_peak,
    pick_chromatographic_peaks,
)
from bijux_proteomics.io.xic_extraction import extract_mzml_xic_traces


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def test_chromatographic_peak_report_tracks_raw_overlap_classification() -> None:
    trace_report = extract_mzml_xic_traces(
        _format_fixture("chromatographic_peak_profile.mzml"),
        _format_fixture("chromatographic_peak_targets.tsv"),
        tolerance_ppm=10.0,
    )
    overlap_trace = tuple(
        point for point in trace_report.trace_points if point.target_id == "target_overlap"
    )

    raw_peaks = pick_peak(overlap_trace)
    report = pick_chromatographic_peaks(trace_report)
    report_overlap = [peak for peak in report.peaks if peak.target_id == "target_overlap"]

    assert len(raw_peaks) == len(report_overlap) == 2
    assert [peak.rt_apex for peak in raw_peaks] == [
        peak.apex_time_seconds for peak in report_overlap
    ]
    assert all(peak.overlap_flag for peak in raw_peaks)
    assert all(peak.overlap_flag for peak in report_overlap)
