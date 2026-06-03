# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from math import isclose
from pathlib import Path

from bijux_proteomics.io.chromatographic_peak_picking import (
    ChromatographicPeakQuality,
    extract_mzml_chromatographic_peaks,
    pick_chromatographic_peaks,
    pick_peak,
    render_chromatographic_peaks_tsv,
    render_picked_chromatographic_peaks_tsv,
)
from bijux_proteomics.io.mzml_reader import stream_mzml_spectra
from bijux_proteomics.io.xic_extraction import (
    XicToleranceUnit,
    extract_mzml_xic_traces,
    extract_xic,
    parse_xic_target_table,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def test_pick_chromatographic_peaks_detects_boundaries_apex_and_overlap_flags() -> None:
    trace_report = extract_mzml_xic_traces(
        _format_fixture("chromatographic_peak_profile.mzml"),
        _format_fixture("chromatographic_peak_targets.tsv"),
        tolerance_ppm=10.0,
    )

    report = pick_chromatographic_peaks(trace_report)

    assert len(report.peaks) == 3

    overlap_peaks = [
        peak for peak in report.peaks if peak.target_id == "target_overlap"
    ]
    single_peak = next(
        peak for peak in report.peaks if peak.target_id == "target_single"
    )

    assert len(overlap_peaks) == 2
    assert overlap_peaks[0].start_time_seconds == 0.0
    assert overlap_peaks[0].end_time_seconds == 30.0
    assert overlap_peaks[0].apex_time_seconds == 20.0
    assert overlap_peaks[0].overlap_flag is True
    assert overlap_peaks[0].shoulder_flag is True
    assert overlap_peaks[1].start_time_seconds == 30.0
    assert overlap_peaks[1].end_time_seconds == 60.0
    assert overlap_peaks[1].apex_time_seconds == 40.0
    assert overlap_peaks[1].overlap_flag is True
    assert overlap_peaks[1].shoulder_flag is False
    assert single_peak.start_time_seconds == 0.0
    assert single_peak.end_time_seconds == 60.0
    assert single_peak.apex_time_seconds == 30.0
    assert single_peak.overlap_flag is False
    assert single_peak.shoulder_flag is False


def test_pick_peak_flags_overlapping_fixture_instead_of_one_clean_peak() -> None:
    spectra = tuple(
        stream_mzml_spectra(_format_fixture("chromatographic_peak_profile.mzml"))
    )
    targets = parse_xic_target_table(
        _format_fixture("chromatographic_peak_targets.tsv")
    ).accepted_entries
    raw_rows = tuple(
        row
        for row in extract_xic(
            spectra,
            targets,
            tolerance=10.0,
            tolerance_unit=XicToleranceUnit.PPM,
        )
        if row.target_id == "target_overlap"
    )

    peaks = pick_peak(raw_rows)
    rendered = render_picked_chromatographic_peaks_tsv(peaks)

    assert len(peaks) == 2
    assert peaks[0].rt_start == 0.0
    assert peaks[0].rt_apex == 20.0
    assert peaks[0].rt_end == 30.0
    assert peaks[0].overlap_flag is True
    assert peaks[0].peak_quality is ChromatographicPeakQuality.SHOULDER
    assert peaks[1].rt_start == 30.0
    assert peaks[1].rt_apex == 40.0
    assert peaks[1].rt_end == 60.0
    assert peaks[1].overlap_flag is True
    assert peaks[1].peak_quality is ChromatographicPeakQuality.OVERLAP
    assert "peak_quality" in rendered


def test_pick_chromatographic_peaks_uses_baseline_corrected_area_instead_of_window_sum() -> (
    None
):
    trace_report = extract_mzml_xic_traces(
        _format_fixture("chromatographic_peak_profile.mzml"),
        _format_fixture("chromatographic_peak_targets.tsv"),
        tolerance_ppm=10.0,
    )

    report = pick_chromatographic_peaks(trace_report)

    first_overlap_peak = next(
        peak for peak in report.peaks if peak.peak_id == "target_overlap_peak_001"
    )
    second_overlap_peak = next(
        peak for peak in report.peaks if peak.peak_id == "target_overlap_peak_002"
    )
    single_peak = next(
        peak for peak in report.peaks if peak.target_id == "target_single"
    )

    assert isclose(first_overlap_peak.baseline_at_apex, 60.0, rel_tol=0.0, abs_tol=1e-9)
    assert isclose(first_overlap_peak.height, 60.0, rel_tol=0.0, abs_tol=1e-9)
    assert isclose(first_overlap_peak.area, 700.0, rel_tol=0.0, abs_tol=1e-9)
    assert isclose(
        second_overlap_peak.baseline_at_apex, 60.0, rel_tol=0.0, abs_tol=1e-9
    )
    assert isclose(second_overlap_peak.height, 80.0, rel_tol=0.0, abs_tol=1e-9)
    assert isclose(second_overlap_peak.area, 850.0, rel_tol=0.0, abs_tol=1e-9)
    assert isclose(single_peak.baseline_at_apex, 0.0, rel_tol=0.0, abs_tol=1e-9)
    assert isclose(single_peak.height, 160.0, rel_tol=0.0, abs_tol=1e-9)
    assert isclose(single_peak.area, 3600.0, rel_tol=0.0, abs_tol=1e-9)
    assert single_peak.area != sum(
        point.intensity
        for point in trace_report.trace_points
        if point.target_id == "target_single"
    )


def test_extract_mzml_chromatographic_peaks_composes_xic_extraction() -> None:
    report = extract_mzml_chromatographic_peaks(
        _format_fixture("chromatographic_peak_profile.mzml"),
        _format_fixture("chromatographic_peak_targets.tsv"),
        tolerance_ppm=10.0,
    )

    assert report.trace_report.eligible_spectra == 7
    assert report.trace_report.total_spectra == 8
    assert len(report.trace_report.trace_points) == 14
    assert [peak.peak_id for peak in report.peaks] == [
        "target_overlap_peak_001",
        "target_overlap_peak_002",
        "target_single_peak_001",
    ]


def test_render_chromatographic_peaks_tsv_emits_overlap_and_shoulder_flags() -> None:
    report = extract_mzml_chromatographic_peaks(
        _format_fixture("chromatographic_peak_profile.mzml"),
        _format_fixture("chromatographic_peak_targets.tsv"),
        tolerance_ppm=10.0,
    )

    rendered = render_chromatographic_peaks_tsv(report)
    rows = rendered.strip().splitlines()

    assert rows[0] == (
        "peak_id\ttarget_id\tstart_time_seconds\tend_time_seconds\tapex_time_seconds\t"
        "apex_intensity\tbaseline_start_intensity\tbaseline_end_intensity\t"
        "baseline_at_apex\theight\tarea\tpoint_count\toverlap_flag\tshoulder_flag"
    )
    assert (
        "target_overlap_peak_001\ttarget_overlap\t0\t30\t20\t120\t0\t90\t60\t60\t700\t4\ttrue\ttrue"
        in rows
    )
    assert (
        "target_single_peak_001\ttarget_single\t0\t60\t30\t160\t0\t0\t0\t160\t3600\t7\tfalse\tfalse"
        in rows
    )
