# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.chromatographic_evidence import score_chromatographic_evidence
from bijux_proteomics.io.chromatographic_peak_picking import (
    extract_mzml_chromatographic_peaks,
    score_peak_shape,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def test_chromatographic_evidence_uses_peak_shape_scoring_surface() -> None:
    peak_report = extract_mzml_chromatographic_peaks(
        _format_fixture("chromatographic_peak_profile.mzml"),
        _format_fixture("chromatographic_peak_targets.tsv"),
        tolerance_ppm=10.0,
    )
    overlap_peak = next(
        peak for peak in peak_report.peaks if peak.peak_id == "target_overlap_peak_001"
    )
    overlap_trace = tuple(
        point
        for point in peak_report.trace_report.trace_points
        if point.target_id == overlap_peak.target_id
        and overlap_peak.start_time_seconds
        <= point.time_seconds
        <= overlap_peak.end_time_seconds
    )

    shape = score_peak_shape(overlap_trace)
    evidence = score_chromatographic_evidence((peak_report,))
    by_target = {entry.target_id: entry for entry in evidence.target_entries}

    assert shape.shape_quality_tier.value in {"acceptable", "gaussian_like"}
    assert (
        by_target["target_overlap"].peak_shape_score
        < by_target["target_single"].peak_shape_score
    )
    assert by_target["target_overlap"].peak_shape_score < 0.5
