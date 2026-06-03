# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification import SearchResultColumnMapping, parse_psm_tsv
from bijux_proteomics.io.chimeric_spectrum import score_chimeric_spectra_from_psms
from bijux_proteomics.io.mzml_reader import parse_mzml


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "formats" / name


def _psm_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "psm" / name


def _default_mapping() -> SearchResultColumnMapping:
    return SearchResultColumnMapping(
        spectrum_id="spectrum_id",
        peptide="peptide",
        charge="charge",
        score="score",
        q_value="q_value",
        protein_refs="proteins",
    )


def test_score_chimeric_spectra_from_psms_separates_mixed_and_clean_spectra() -> None:
    spectra = parse_mzml(
        _format_fixture("chimeric_spectrum_review.mzml")
    ).accepted_spectra
    psm_records = parse_psm_tsv(
        _psm_fixture("chimeric_spectrum_candidates.tsv"),
        mapping=_default_mapping(),
    ).accepted_records

    report = score_chimeric_spectra_from_psms(spectra, psm_records)

    assert spectra[0].isolation_window_target_mz == 400.687246
    assert spectra[0].isolation_window_lower_offset == 1.0
    assert spectra[0].isolation_window_upper_offset == 1.0
    assert report.summary.spectrum_count == 2
    assert report.summary.scored_spectrum_count == 2
    assert report.summary.flagged_chimeric_count == 0
    assert report.summary.competing_evidence_entry_count == 2

    mixed = next(entry for entry in report.spectra if entry.spectrum_id == "scan=9002")
    clean = next(entry for entry in report.spectra if entry.spectrum_id == "scan=9001")

    assert mixed.primary_peptide == "PEPTIDE"
    assert mixed.strongest_competing_peptide == "TIDEPEP"
    assert mixed.flagged_chimeric is False
    assert mixed.chimeric_score == 0.15
    assert clean.flagged_chimeric is False
    assert clean.strongest_competing_peptide == "TIDEPEP"
    assert clean.chimeric_score == 0.15

    mixed_competitor = next(
        entry
        for entry in report.competing_evidence
        if entry.spectrum_id == "scan=9002" and entry.competing_peptide == "TIDEPEP"
    )
    assert mixed_competitor.within_isolation_window is True
    assert mixed_competitor.unique_peak_count == 0
    assert mixed_competitor.shared_peak_count == 0
    assert mixed_competitor.unique_explained_intensity_fraction == 0.0
    assert mixed_competitor.competition_score == 0.15


def test_score_chimeric_spectra_from_psms_requires_candidates() -> None:
    spectra = parse_mzml(
        _format_fixture("chimeric_spectrum_review.mzml")
    ).accepted_spectra

    try:
        score_chimeric_spectra_from_psms(spectra, ())
    except ValueError as exc:
        assert "candidate annotation" in str(exc)
    else:
        raise AssertionError(
            "expected chimeric scoring to reject an empty candidate set"
        )
