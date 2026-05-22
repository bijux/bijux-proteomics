# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import extract_mzml_chromatograms, parse_mzml
from bijux_proteomics.io.run_qc import (
    build_spectrum_run_qc_plot_payload,
    build_spectrum_run_qc_report,
    render_spectrum_run_qc_distribution_tsv,
    render_spectrum_run_qc_flagged_spectra_tsv,
    render_spectrum_run_qc_spectra_tsv,
    render_spectrum_run_qc_summary_tsv,
    render_spectrum_run_qc_time_bins_tsv,
    render_spectrum_run_qc_trace_tsv,
)
from bijux_proteomics.io.spectra import SpectrumModel, SpectrumPeak


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "formats" / name


def _qc_spectra() -> tuple[SpectrumModel, ...]:
    return (
        SpectrumModel(
            spectrum_id="scan=1",
            precursor_mz=500.2,
            precursor_intensity=500.0,
            precursor_charge=2,
            retention_time_seconds=15.0,
            peaks=(
                SpectrumPeak(mz=100.0, intensity=40.0),
                SpectrumPeak(mz=150.0, intensity=30.0),
                SpectrumPeak(mz=200.0, intensity=20.0),
            ),
        ),
        SpectrumModel(
            spectrum_id="scan=2",
            precursor_mz=600.2,
            precursor_intensity=5000.0,
            precursor_charge=3,
            retention_time_seconds=75.0,
            peaks=(SpectrumPeak(mz=250.0, intensity=15.0),),
        ),
        SpectrumModel(
            spectrum_id="scan=3",
            precursor_mz=700.2,
            precursor_intensity=None,
            precursor_charge=None,
            retention_time_seconds=135.0,
            peaks=(),
        ),
    )


def test_spectrum_run_qc_report_tracks_distributions_traces_and_flagged_spectra() -> (
    None
):
    report = build_spectrum_run_qc_report(
        _qc_spectra(),
        source_kind="mgf",
        rejected_count=1,
        time_bin_seconds=60.0,
        noisy_peak_count_threshold=3,
        noisy_total_ion_current_threshold=100.0,
    )
    plot_payload = build_spectrum_run_qc_plot_payload(report)
    summary_tsv = render_spectrum_run_qc_summary_tsv(report)
    time_tsv = render_spectrum_run_qc_time_bins_tsv(report)
    charge_tsv = render_spectrum_run_qc_distribution_tsv(
        report.charge_distribution,
        distribution_name="charge",
    )
    precursor_tsv = render_spectrum_run_qc_distribution_tsv(
        report.precursor_intensity_distribution,
        distribution_name="precursor_intensity",
    )
    tic_tsv = render_spectrum_run_qc_trace_tsv(report.tic_trace, trace_name="tic")
    spectra_tsv = render_spectrum_run_qc_spectra_tsv(report)
    flagged_tsv = render_spectrum_run_qc_flagged_spectra_tsv(report)

    assert report.source_kind == "mgf"
    assert report.chromatogram_source == "spectrum_derived"
    assert report.spectrum_count == 3
    assert report.rejected_count == 1
    assert report.ms2_spectrum_count == 3
    assert report.precursor_intensity_observation_count == 2
    assert report.empty_spectrum_count == 1
    assert report.noisy_spectrum_count == 2
    assert report.single_dominant_peak_count == 1
    assert [row.ms2_spectrum_count for row in report.ms2_count_over_time] == [1, 1, 1]
    assert report.tic_trace[0].value == 90.0
    assert report.bpc_trace[1].value == 15.0
    assert [row.count for row in report.charge_distribution] == [1, 0, 1, 1, 0]
    assert [row.count for row in report.quality_distribution] == [0, 0, 3]
    assert report.precursor_intensity_distribution[0].bucket == "unknown"
    assert report.precursor_intensity_distribution[0].count == 1
    assert report.precursor_intensity_distribution[1].count == 1
    assert report.precursor_intensity_distribution[2].count == 1
    assert len(report.spectrum_metrics) == 3
    assert report.spectrum_metrics[0].quality_tier.value == "low"
    assert report.spectrum_metrics[1].is_single_dominant_peak is True
    assert {row.issue_kind.value for row in report.flagged_spectra} == {
        "empty",
        "noisy",
        "single_dominant_peak",
    }
    assert plot_payload.chromatogram_source == "spectrum_derived"
    assert "chromatogram_source" in summary_tsv
    assert "ms2_spectrum_count" in time_tsv
    assert "charge" in charge_tsv
    assert "precursor_intensity" in precursor_tsv
    assert "tic" in tic_tsv
    assert "quality_tier" in spectra_tsv
    assert "issue_kind" in flagged_tsv


def test_spectrum_run_qc_report_prefers_reported_mzml_chromatograms_when_present() -> (
    None
):
    parse_report = parse_mzml(_format_fixture("practical_review.mzml"))
    chromatograms = extract_mzml_chromatograms(_format_fixture("practical_review.mzml"))

    report = build_spectrum_run_qc_report(
        parse_report.accepted_spectra,
        source_kind="mzml",
        rejected_count=len(parse_report.rejected_spectra),
        chromatograms=chromatograms,
        time_bin_seconds=30.0,
    )

    assert report.chromatogram_source == "reported_mzml_chromatograms"
    assert len(report.tic_trace) == 3
    assert len(report.bpc_trace) == 3
    assert report.precursor_intensity_observation_count == 2
    assert report.precursor_intensity_distribution[3].count == 1
    assert report.precursor_intensity_distribution[4].count == 1
    assert report.ms2_spectrum_count == 1
