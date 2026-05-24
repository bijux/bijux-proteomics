# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.chromatographic_evidence import (
    extract_mzml_chromatographic_evidence,
    render_chromatographic_peptide_evidence_tsv,
    render_chromatographic_target_evidence_tsv,
    score_chromatographic_evidence,
)
from bijux_proteomics.io.chromatographic_peak_picking import (
    extract_mzml_chromatographic_peaks,
)
from bijux_proteomics.io.retention_time_alignment import (
    extract_mzml_retention_time_alignment,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def test_score_chromatographic_evidence_penalizes_overlap_peak_shape() -> None:
    peak_report = extract_mzml_chromatographic_peaks(
        _format_fixture("chromatographic_peak_profile.mzml"),
        _format_fixture("chromatographic_peak_targets.tsv"),
        tolerance_ppm=10.0,
    )

    report = score_chromatographic_evidence((peak_report,))

    by_target = {entry.target_id: entry for entry in report.target_entries}
    assert by_target["target_single"].chromatographic_evidence_score == 1.0
    assert by_target["target_overlap"].peak_shape_score < 0.5
    assert by_target["target_overlap"].chromatographic_evidence_score < 0.85
    assert by_target["target_overlap"].concern_codes == (
        "low_signal_to_noise",
        "multiple_peaks",
        "overlap_detected",
    )


def test_score_chromatographic_evidence_penalizes_rt_drift_and_missingness() -> None:
    alignment_report = extract_mzml_retention_time_alignment(
        (
            _format_fixture("rt_alignment_reference.mzml"),
            _format_fixture("rt_alignment_shifted.mzml"),
        ),
        _format_fixture("rt_alignment_targets.tsv"),
        tolerance_ppm=10.0,
        aligned_rt_tolerance_seconds=5.0,
    )

    report = score_chromatographic_evidence(
        alignment_report.peak_reports,
        alignment_report=alignment_report,
    )

    by_target = {entry.target_id: entry for entry in report.target_entries}
    by_peptide = {entry.peptide_ref: entry for entry in report.peptide_entries}

    assert by_target["anchor_alpha"].chromatographic_evidence_score == 1.0
    assert by_target["anchor_gamma"].rt_agreement_score == 0.0
    assert by_target["anchor_gamma"].chromatographic_evidence_score < 0.8
    assert "rt_outside_tolerance" in by_target["anchor_gamma"].concern_codes
    assert by_target["anchor_delta"].missingness_score == 0.5
    assert by_target["anchor_delta"].missing_run_ids == ("rt_alignment_shifted",)
    assert by_target["anchor_delta"].chromatographic_evidence_score < 0.75
    assert "missing_peak" in by_target["anchor_delta"].concern_codes
    assert by_peptide["PEPC"].chromatographic_evidence_score == by_target["anchor_gamma"].chromatographic_evidence_score
    assert by_peptide["PEPD"].chromatographic_evidence_score == by_target["anchor_delta"].chromatographic_evidence_score


def test_extract_mzml_chromatographic_evidence_composes_alignment_and_renders_tsv() -> None:
    report = extract_mzml_chromatographic_evidence(
        (
            _format_fixture("rt_alignment_reference.mzml"),
            _format_fixture("rt_alignment_shifted.mzml"),
        ),
        _format_fixture("rt_alignment_targets.tsv"),
        tolerance_ppm=10.0,
        aligned_rt_tolerance_seconds=5.0,
    )

    target_tsv = render_chromatographic_target_evidence_tsv(report)
    peptide_tsv = render_chromatographic_peptide_evidence_tsv(report)

    assert report.run_ids == ("rt_alignment_reference", "rt_alignment_shifted")
    assert len(report.target_entries) == 4
    assert len(report.peptide_entries) == 4
    assert target_tsv.splitlines()[0] == (
        "target_id\tpeptide_ref\tprecursor_mz\ttotal_run_count\tdetected_run_count\t"
        "missing_run_count\tpeak_shape_score\tapex_intensity_score\t"
        "signal_to_noise_score\trt_agreement_score\tmissingness_score\t"
        "chromatographic_evidence_score\tflagged_run_ids\tmissing_run_ids\tconcern_codes"
    )
    assert (
        "anchor_gamma\tPEPC\t700.000000\t2\t2\t0\t0.9166\t1.0000\t1.0000\t0.0000\t1.0000\t0.7792"
        in target_tsv
    )
    assert peptide_tsv.splitlines()[0] == (
        "peptide_ref\ttarget_ids\ttotal_run_count\tdetected_run_count\tpeak_shape_score\t"
        "apex_intensity_score\tsignal_to_noise_score\trt_agreement_score\t"
        "missingness_score\tchromatographic_evidence_score\tconcern_codes"
    )
    assert "PEPD\tanchor_delta\t2\t1\t1.0000\t1.0000\t1.0000\t0.0000\t0.5000\t0.7250" in peptide_tsv
