# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.xic_extraction import extract_mzml_xic_traces


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def test_mzml_xic_report_tracks_raw_engine_tolerance_sensitivity() -> None:
    narrow = extract_mzml_xic_traces(
        _format_fixture("xic_review.mzml"),
        _format_fixture("xic_targets.tsv"),
        tolerance_ppm=5.0,
    )
    wide = extract_mzml_xic_traces(
        _format_fixture("xic_review.mzml"),
        _format_fixture("xic_targets.tsv"),
        tolerance_ppm=20.0,
    )

    narrow_beta = {
        (row.target_id, row.spectrum_id): row
        for row in narrow.trace_points
        if row.target_id == "target_beta"
    }
    wide_beta = {
        (row.target_id, row.spectrum_id): row
        for row in wide.trace_points
        if row.target_id == "target_beta"
    }

    assert narrow_beta[("target_beta", "scan=7001")].intensity == 0.0
    assert wide_beta[("target_beta", "scan=7001")].intensity == 2500.0
    assert narrow_beta[("target_beta", "scan=7001")].matched_peak_count == 0
    assert wide_beta[("target_beta", "scan=7001")].matched_peak_count == 1
