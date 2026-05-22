# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.spectra import SpectrumModel, SpectrumPeak
from bijux_proteomics.io.spectrum_peak_matching import (
    build_spectrum_peak_match_report,
    export_spectrum_peak_match_tsv,
    export_spectrum_unmatched_peak_tsv,
)


def test_spectrum_peak_matching_exports_matched_and_unmatched_tsvs(
    tmp_path: Path,
) -> None:
    spectrum = SpectrumModel(
        spectrum_id="scan=exports",
        precursor_mz=500.2,
        precursor_charge=2,
        peaks=(
            SpectrumPeak(mz=98.06003691067667, intensity=75.0),
            SpectrumPeak(mz=800.0, intensity=25.0),
        ),
    )
    report = build_spectrum_peak_match_report(
        spectrum,
        peptide="PEPTIDE",
        tolerance_da=0.01,
        include_neutral_losses=False,
    )
    matched_path = tmp_path / "matched.tsv"
    unmatched_path = tmp_path / "unmatched.tsv"

    export_spectrum_peak_match_tsv(report, matched_path)
    export_spectrum_unmatched_peak_tsv(report, unmatched_path)

    matched_lines = matched_path.read_text(encoding="utf-8").splitlines()
    unmatched_lines = unmatched_path.read_text(encoding="utf-8").splitlines()

    assert (
        matched_lines[0]
        == "spectrum_id\tpeptide\ttolerance_mode\tseries\tordinal\tfragment_charge\tspan_start\tspan_end\tfragment_sequence\tfragment_mz\tneutral_loss\tobserved_mz\tobserved_intensity\tmass_error_da\tmass_error_ppm\tlabel"
    )
    matched_fields = matched_lines[1].split("\t")
    assert matched_fields[:9] == [
        "scan=exports",
        "PEPTIDE",
        "da",
        "b",
        "1",
        "1",
        "1",
        "1",
        "P",
    ]
    assert matched_fields[10] == ""
    assert matched_fields[11] == "98.06003691067667"
    assert matched_fields[12] == "75.0"
    assert unmatched_lines[0] == "spectrum_id\tpeptide\ttolerance_mode\tmz\tintensity"
    assert unmatched_lines[1] == "scan=exports\tPEPTIDE\tda\t800.0\t25.0"
