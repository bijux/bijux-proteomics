# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.chromatographic_peak_picking import (
    extract_mzml_chromatographic_peaks,
)
from bijux_proteomics.io.chromatography.chromatographic_peak_picking import (
    ChromatographicPeakPickingReport,
)
from bijux_proteomics.io.dia_fragment_coelution import (
    DiaFragmentTracePoint,
    extract_mzml_dia_fragment_trace_coelution,
    score_fragment_coelution,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def test_extract_mzml_dia_fragment_trace_coelution_preserves_raw_trace_summary() -> (
    None
):
    peak_report = extract_mzml_chromatographic_peaks(
        _format_fixture("dia_fragment_coelution.mzml"),
        _format_fixture("dia_fragment_targets.tsv"),
        tolerance_ppm=10.0,
        ms_level=2,
    )
    report = extract_mzml_dia_fragment_trace_coelution(
        (_format_fixture("dia_fragment_coelution.mzml"),),
        _format_fixture("dia_fragment_targets.tsv"),
        tolerance_ppm=10.0,
    )
    raw_scores = score_fragment_coelution(_raw_points_from_peak_report(peak_report))
    by_precursor = {entry.precursor_id: entry for entry in report.run_entries}
    raw_by_precursor = {entry.precursor_id: entry for entry in raw_scores}

    assert (
        by_precursor["prec_alpha"].coelution_score
        == raw_by_precursor["prec_alpha"].coelution_score
    )
    assert (
        by_precursor["prec_beta"].apex_spread_seconds
        == raw_by_precursor["prec_beta"].apex_rt_spread
    )
    assert (
        by_precursor["prec_beta"].mean_correlation
        == raw_by_precursor["prec_beta"].mean_trace_correlation
    )
    assert (
        by_precursor["prec_beta"].failed_fragment_ids
        == raw_by_precursor["prec_beta"].failed_fragments
    )
    assert (
        by_precursor["prec_beta"].coelution_score
        == raw_by_precursor["prec_beta"].coelution_score
    )


def _raw_points_from_peak_report(
    peak_report: ChromatographicPeakPickingReport,
) -> tuple[DiaFragmentTracePoint, ...]:
    target_metadata = {
        target.target_id: (
            str(target.metadata["precursor_id"]),
            str(
                target.metadata.get("fragment_id")
                or target.metadata.get("transition_id")
                or target.target_id
            ),
        )
        for target in peak_report.trace_report.accepted_targets
    }
    return tuple(
        DiaFragmentTracePoint(
            precursor_id=target_metadata[point.target_id][0],
            fragment_id=target_metadata[point.target_id][1],
            rt=point.time_seconds,
            intensity=point.intensity,
        )
        for point in peak_report.trace_report.trace_points
        if point.target_id in target_metadata
    )
