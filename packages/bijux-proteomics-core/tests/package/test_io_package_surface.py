# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics import io
from bijux_proteomics.io.spectra import SpectrumModel, SpectrumPeak


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "formats" / name


def test_io_package_exports_mzml_reader_owner_surface() -> None:
    report = io.parse_mzml(_format_fixture("simple.mzml"))
    review = io.build_mzml_practical_review_report(_format_fixture("practical_review.mzml"))

    assert hasattr(io, "parse_mzml")
    assert hasattr(io, "inspect_mzml_decoding_support")
    assert hasattr(io, "build_mzml_practical_review_report")
    assert report.metadata.instrument_names == ("Q Exactive",)
    assert review.decoding_support.supported is True


def test_io_package_exports_spectrum_quality_owner_surface() -> None:
    report = io.build_spectrum_run_qc_report(
        (
            SpectrumModel(
                spectrum_id="scan=1",
                precursor_mz=500.2,
                precursor_intensity=50000.0,
                precursor_charge=2,
                peaks=tuple(
                    SpectrumPeak(mz=100.0 + offset, intensity=100.0)
                    for offset in range(8)
                ),
            ),
        ),
        source_kind="mgf",
    )
    rendered = io.render_spectrum_run_qc_spectra_tsv(report)

    assert hasattr(io, "build_spectrum_run_qc_report")
    assert hasattr(io, "render_spectrum_run_qc_spectra_tsv")
    assert report.spectrum_metrics[0].quality_tier.value == "high"
    assert "quality_tier" in rendered


def test_io_package_exports_transition_table_owner_surface() -> None:
    report = io.parse_transition_table(_format_fixture("transition_quant.tsv"))
    first_entry = report.accepted_entries[0]
    domain_record = first_entry.to_domain_record()

    assert hasattr(io, "parse_transition_table")
    assert len(report.accepted_entries) == 7
    assert first_entry.precursor_charge == 2
    assert first_entry.retention_time_minutes == 12.5
    assert domain_record.precursor_charge == 2
    assert domain_record.retention_time_minutes == 12.5


def test_io_package_exports_xic_extraction_owner_surface() -> None:
    report = io.extract_mzml_xic_traces(
        _format_fixture("xic_review.mzml"),
        _format_fixture("xic_targets.tsv"),
        tolerance_ppm=10.0,
    )
    rendered = io.render_xic_traces_tsv(report)

    assert hasattr(io, "parse_xic_target_table")
    assert hasattr(io, "extract_mzml_xic_traces")
    assert hasattr(io, "render_xic_traces_tsv")
    assert report.eligible_spectra == 3
    assert len(report.trace_points) == 8
    assert "target_alpha\tscan=7000\t10\t500.000000" in rendered


def test_io_package_exports_chromatographic_peak_picking_owner_surface() -> None:
    report = io.extract_mzml_chromatographic_peaks(
        _format_fixture("chromatographic_peak_profile.mzml"),
        _format_fixture("chromatographic_peak_targets.tsv"),
        tolerance_ppm=10.0,
    )
    rendered = io.render_chromatographic_peaks_tsv(report)

    assert hasattr(io, "pick_chromatographic_peaks")
    assert hasattr(io, "extract_mzml_chromatographic_peaks")
    assert hasattr(io, "render_chromatographic_peaks_tsv")
    assert len(report.peaks) == 3
    assert report.peaks[0].overlap_flag is True
    assert "target_single_peak_001\ttarget_single\t0\t60\t30\t160" in rendered


def test_io_package_exports_retention_time_alignment_owner_surface() -> None:
    report = io.extract_mzml_retention_time_alignment(
        (
            _format_fixture("rt_alignment_reference.mzml"),
            _format_fixture("rt_alignment_shifted.mzml"),
        ),
        _format_fixture("rt_alignment_targets.tsv"),
        tolerance_ppm=10.0,
        aligned_rt_tolerance_seconds=5.0,
    )
    rendered = io.render_retention_time_alignment_residuals_tsv(report)

    assert hasattr(io, "align_chromatographic_peak_retention_times")
    assert hasattr(io, "extract_mzml_retention_time_alignment")
    assert hasattr(io, "render_retention_time_alignment_models_tsv")
    assert hasattr(io, "render_retention_time_alignment_residuals_tsv")
    assert hasattr(io, "render_retention_time_alignment_failed_anchors_tsv")
    assert report.run_models[1].status.value == "aligned"
    assert len(report.flagged_residuals) == 1
    assert "anchor_gamma\tanchor_gamma_peak_001\tanchor_gamma_peak_001\t60\t80\t70" in rendered


def test_io_package_exports_chromatographic_evidence_owner_surface() -> None:
    report = io.extract_mzml_chromatographic_evidence(
        (
            _format_fixture("rt_alignment_reference.mzml"),
            _format_fixture("rt_alignment_shifted.mzml"),
        ),
        _format_fixture("rt_alignment_targets.tsv"),
        tolerance_ppm=10.0,
        aligned_rt_tolerance_seconds=5.0,
    )
    rendered = io.render_chromatographic_peptide_evidence_tsv(report)

    assert hasattr(io, "score_chromatographic_evidence")
    assert hasattr(io, "extract_mzml_chromatographic_evidence")
    assert hasattr(io, "render_chromatographic_target_evidence_tsv")
    assert hasattr(io, "render_chromatographic_peptide_evidence_tsv")
    assert len(report.target_entries) == 4
    assert report.peptide_entries[0].chromatographic_evidence_score == 1.0
    assert "PEPD\tanchor_delta\t2\t1\t1.0000\t1.0000\t1.0000\t0.0000\t0.5000\t0.7250" in rendered
