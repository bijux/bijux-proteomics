# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.chemistry import calculate_fragment_ions
from bijux_proteomics.io.spectra import SpectrumModel, SpectrumPeak
from bijux_proteomics.io.spectrum_peak_matching import (
    SpectrumPeakMatchToleranceMode,
    build_spectrum_peak_match_report,
)


def test_spectrum_peak_matching_reports_ppm_and_dalton_modes() -> None:
    fragment = calculate_fragment_ions(
        "PEPTIDE",
        include_neutral_losses=False,
    )[0]
    observed_mz = fragment.mz_monoisotopic * (1.0 + (10.0 / 1_000_000.0))
    spectrum = SpectrumModel(
        spectrum_id="scan=tolerance-modes",
        precursor_mz=500.2,
        precursor_charge=2,
        peaks=(
            SpectrumPeak(mz=observed_mz, intensity=80.0),
            SpectrumPeak(mz=700.0, intensity=20.0),
        ),
    )

    ppm_report = build_spectrum_peak_match_report(
        spectrum,
        peptide="PEPTIDE",
        tolerance_da=None,
        tolerance_ppm=20.0,
        include_neutral_losses=False,
    )
    dalton_report = build_spectrum_peak_match_report(
        spectrum,
        peptide="PEPTIDE",
        tolerance_da=0.0005,
        tolerance_ppm=None,
        include_neutral_losses=False,
    )

    assert ppm_report.tolerance_mode is SpectrumPeakMatchToleranceMode.PPM
    assert ppm_report.matched_peak_count == 1
    assert ppm_report.unmatched_peak_count == 1
    assert ppm_report.explained_intensity_fraction == 0.8
    assert dalton_report.tolerance_mode is SpectrumPeakMatchToleranceMode.DA
    assert dalton_report.matched_peak_count == 0
    assert dalton_report.unmatched_peak_count == 2
    assert dalton_report.explained_intensity_fraction == 0.0


def test_spectrum_peak_matching_preserves_unmatched_peak_rows() -> None:
    spectrum = SpectrumModel(
        spectrum_id="scan=unmatched-ledger",
        precursor_mz=500.2,
        precursor_charge=2,
        peaks=(
            SpectrumPeak(mz=100.0, intensity=40.0),
            SpectrumPeak(mz=250.0, intensity=60.0),
        ),
    )

    report = build_spectrum_peak_match_report(
        spectrum,
        peptide="PEPTIDE",
        tolerance_da=0.0001,
        include_neutral_losses=False,
    )

    assert report.matched_peak_count == 0
    assert report.unmatched_peak_count == 2
    assert tuple((peak.mz, peak.intensity) for peak in report.unmatched_peaks) == (
        (100.0, 40.0),
        (250.0, 60.0),
    )


def test_spectrum_peak_matching_ignores_tolerance_compatible_noise_peaks() -> None:
    fragment = calculate_fragment_ions(
        "PEPTIDE",
        include_neutral_losses=False,
    )[0]
    spectrum = SpectrumModel(
        spectrum_id="scan=noise-filter",
        precursor_mz=500.2,
        precursor_charge=2,
        peaks=(
            SpectrumPeak(mz=fragment.mz_monoisotopic, intensity=5.0),
            SpectrumPeak(mz=200.0, intensity=10.0),
            SpectrumPeak(mz=350.0, intensity=70.0),
            SpectrumPeak(mz=500.0, intensity=140.0),
        ),
    )

    report = build_spectrum_peak_match_report(
        spectrum,
        peptide="PEPTIDE",
        tolerance_da=0.01,
        include_neutral_losses=False,
    )

    assert report.matched_peak_count == 0
    assert report.unmatched_peak_count == 4
    assert report.explained_intensity_fraction == 0.0
    assert tuple((peak.mz, peak.intensity) for peak in report.unmatched_peaks) == (
        (fragment.mz_monoisotopic, 5.0),
        (200.0, 10.0),
        (350.0, 70.0),
        (500.0, 140.0),
    )
