# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from math import isclose
from pathlib import Path

from bijux_proteomics.io.precursor_isotope_fit import (
    extract_mzml_precursor_isotope_fit,
    render_precursor_isotope_fit_entries_tsv,
    render_precursor_isotope_fit_peaks_tsv,
    render_precursor_isotope_fit_summary_tsv,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def test_extract_mzml_precursor_isotope_fit_distinguishes_shifted_and_wrong_charge_patterns() -> (
    None
):
    report = extract_mzml_precursor_isotope_fit(
        (
            _format_fixture("precursor_isotope_fit_reference.mzml"),
            _format_fixture("precursor_isotope_fit_shifted.mzml"),
            _format_fixture("precursor_isotope_fit_wrong_charge.mzml"),
        ),
        _format_fixture("precursor_isotope_fit_targets.tsv"),
        extraction_tolerance_da=0.05,
        fit_tolerance_da=0.05,
        max_isotope_index=2,
    )

    assert report.run_ids == (
        "precursor_isotope_fit_reference",
        "precursor_isotope_fit_shifted",
        "precursor_isotope_fit_wrong_charge",
    )
    assert report.summary.run_count == 3
    assert report.summary.entry_count == 3
    assert report.summary.flagged_entry_count == 2

    by_run = {entry.run_id: entry for entry in report.entries}
    reference = by_run["precursor_isotope_fit_reference"]
    shifted = by_run["precursor_isotope_fit_shifted"]
    wrong_charge = by_run["precursor_isotope_fit_wrong_charge"]

    assert reference.target_id == "prec_peptide_ms1"
    assert reference.precursor_id == "prec_peptide"
    assert reference.peptide_ref == "PEPTIDE"
    assert reference.apex_spectrum_id == "scan=8303"
    assert reference.missing_isotope_indices == ()
    assert isclose(reference.monoisotopic_mass_error_ppm or 0.0, 0.0, abs_tol=0.05)
    assert reference.charge_consistency_score > 0.99
    assert reference.isotope_pattern_score > 0.95
    assert reference.isotope_fit_score > 0.95
    assert reference.concern_codes == ()

    assert shifted.apex_spectrum_id == "scan=8403"
    assert shifted.missing_isotope_indices == ()
    assert shifted.monoisotopic_mass_error_ppm is not None
    assert shifted.monoisotopic_mass_error_ppm > 45.0
    assert shifted.charge_consistency_score > 0.95
    assert shifted.isotope_pattern_score > 0.95
    assert shifted.isotope_fit_score < 0.8
    assert "shifted_monoisotopic_mz" in shifted.concern_codes

    assert wrong_charge.apex_spectrum_id == "scan=8503"
    assert wrong_charge.missing_isotope_indices == (1,)
    assert isclose(wrong_charge.monoisotopic_mass_error_ppm or 0.0, 0.0, abs_tol=0.05)
    assert wrong_charge.charge_consistency_score == 0.0
    assert wrong_charge.isotope_pattern_score < 0.8
    assert wrong_charge.isotope_fit_score < 0.7
    assert "inconsistent_charge_spacing" in wrong_charge.concern_codes


def test_render_precursor_isotope_fit_ledgers_preserve_summary_entry_and_peak_review() -> (
    None
):
    report = extract_mzml_precursor_isotope_fit(
        (
            _format_fixture("precursor_isotope_fit_reference.mzml"),
            _format_fixture("precursor_isotope_fit_shifted.mzml"),
            _format_fixture("precursor_isotope_fit_wrong_charge.mzml"),
        ),
        _format_fixture("precursor_isotope_fit_targets.tsv"),
        extraction_tolerance_da=0.05,
        fit_tolerance_da=0.05,
        max_isotope_index=2,
    )

    summary_tsv = render_precursor_isotope_fit_summary_tsv(report)
    entries_tsv = render_precursor_isotope_fit_entries_tsv(report)
    peaks_tsv = render_precursor_isotope_fit_peaks_tsv(report)

    assert summary_tsv.splitlines()[0] == (
        "run_count\tentry_count\tflagged_entry_count\tmissing_peak_entry_count\t"
        "weak_charge_entry_count\tweak_pattern_entry_count"
    )
    assert summary_tsv.splitlines()[1] == "3\t3\t2\t0\t1\t0"
    assert (
        "precursor_isotope_fit_shifted\tprec_peptide_ms1\tprec_peptide\tPEPTIDE\t2\t"
        "scan=8403\t30.0000\t400.687258\t400.707246\t0.019988\t49.8831" in entries_tsv
    )
    assert (
        "precursor_isotope_fit_wrong_charge\tprec_peptide_ms1\tprec_peptide\tPEPTIDE\t1\t401.188936\t0.267350"
        in peaks_tsv
    )
    assert "\tfalse" in peaks_tsv
