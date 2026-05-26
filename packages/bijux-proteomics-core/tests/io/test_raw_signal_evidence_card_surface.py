# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.raw_signal_evidence_cards import (
    extract_mzml_raw_signal_evidence_cards,
    render_raw_signal_evidence_card_summary_tsv,
    render_raw_signal_evidence_card_tsv,
    render_raw_signal_evidence_cards_html,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def _psm_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "psm" / name


def test_extract_mzml_raw_signal_evidence_cards_preserves_precursor_isotope_fit_review() -> (
    None
):
    report = extract_mzml_raw_signal_evidence_cards(
        (
            _format_fixture("precursor_isotope_fit_reference.mzml"),
            _format_fixture("precursor_isotope_fit_shifted.mzml"),
            _format_fixture("precursor_isotope_fit_wrong_charge.mzml"),
        ),
        _format_fixture("precursor_isotope_fit_targets.tsv"),
        tolerance_da=0.05,
        selected_precursor_ids=("prec_peptide",),
    )

    assert report.summary.card_count == 1
    assert report.summary.isotope_fit_card_count == 1
    card = report.cards[0]

    assert card.precursor_id == "prec_peptide"
    assert len(card.precursor_isotope_fit_entries) == 3
    by_run = {entry.run_id: entry for entry in card.precursor_isotope_fit_entries}
    assert by_run["precursor_isotope_fit_reference"].isotope_fit_score > 0.95
    assert by_run["precursor_isotope_fit_shifted"].concern_codes == (
        "shifted_monoisotopic_mz",
    )
    assert by_run["precursor_isotope_fit_wrong_charge"].concern_codes == (
        "inconsistent_charge_spacing",
        "missing_isotope_peak",
    )
    assert by_run["precursor_isotope_fit_wrong_charge"].missing_isotope_indices == (1,)
    assert {
        warning.code.value for warning in card.warnings
    } == {
        "chromatographic_peak_concern",
        "precursor_isotope_mismatch",
    }


def test_extract_mzml_raw_signal_evidence_cards_use_semantic_card_ids() -> None:
    report = extract_mzml_raw_signal_evidence_cards(
        (
            _format_fixture("raw_signal_card_reference.mzml"),
            _format_fixture("raw_signal_card_shifted.mzml"),
        ),
        _format_fixture("raw_signal_card_targets.tsv"),
        selected_precursor_ids=("prec_peptide",),
    )

    assert report.cards[0].card_id == "raw-signal-card:prec_peptide"


def test_extract_mzml_raw_signal_evidence_cards_preserves_raw_sections_and_warnings() -> None:
    report = extract_mzml_raw_signal_evidence_cards(
        (
            _format_fixture("raw_signal_card_reference.mzml"),
            _format_fixture("raw_signal_card_shifted.mzml"),
        ),
        _format_fixture("raw_signal_card_targets.tsv"),
        fragment_target_table=_format_fixture("raw_signal_card_fragment_targets.tsv"),
        spectrum_mzml_path=_format_fixture("chimeric_spectrum_review.mzml"),
        psm_path=_psm_fixture("chimeric_spectrum_candidates.tsv"),
        tolerance_ppm=10.0,
        aligned_rt_tolerance_seconds=5.0,
        apex_tolerance_seconds=5.0,
        fragment_ms_level=1,
        selected_precursor_ids=("prec_peptide",),
    )

    assert report.summary.card_count == 1
    assert report.summary.warning_card_count == 1
    card = report.cards[0]

    assert card.card_id == "raw-signal-card:prec_peptide"
    assert card.precursor_id == "prec_peptide"
    assert card.peptide_ref == "PEPTIDE"
    assert card.chromatographic_target_ids == ("prec_peptide_ms1",)
    assert len(card.chromatographic_targets) == 1
    assert len(card.chromatographic_peaks) == 2
    assert {entry.run_id for entry in card.chromatographic_peaks} == {
        "raw_signal_card_reference",
        "raw_signal_card_shifted",
    }
    assert len(card.retention_time_models) == 2
    assert len(card.retention_time_residuals) == 1
    assert card.retention_time_residuals[0].run_id == "raw_signal_card_shifted"
    assert card.retention_time_residuals[0].target_id == "prec_peptide_ms1"
    assert card.retention_time_residuals[0].residual_seconds == 20.0
    assert card.retention_time_residuals[0].outside_aligned_tolerance is True
    assert len(card.spectrum_evidence) == 2
    assert sum(1 for entry in card.spectrum_evidence if entry.flagged_chimeric) == 1
    assert card.spectrum_evidence[0].spectrum_id == "scan=9002"
    assert card.spectrum_evidence[0].strongest_competing_peptide == "TIDEPEP"
    assert len(card.fragment_run_entries) == 2
    by_run = {entry.run_id: entry for entry in card.fragment_run_entries}
    assert by_run["raw_signal_card_reference"].coelution_score > 0.99
    assert by_run["raw_signal_card_shifted"].failed_fragment_ids == (
        "peptide_b4",
        "peptide_y8",
    )
    assert by_run["raw_signal_card_shifted"].coelution_score < 0.5
    assert {
        warning.code.value for warning in card.warnings
    } == {
        "chimeric_spectrum",
        "chromatographic_peak_concern",
        "retention_time_alignment_outside_tolerance",
        "weak_fragment_support",
    }


def test_render_raw_signal_evidence_cards_keep_all_review_sections_visible() -> None:
    report = extract_mzml_raw_signal_evidence_cards(
        (
            _format_fixture("raw_signal_card_reference.mzml"),
            _format_fixture("raw_signal_card_shifted.mzml"),
        ),
        _format_fixture("raw_signal_card_targets.tsv"),
        fragment_target_table=_format_fixture("raw_signal_card_fragment_targets.tsv"),
        spectrum_mzml_path=_format_fixture("chimeric_spectrum_review.mzml"),
        psm_path=_psm_fixture("chimeric_spectrum_candidates.tsv"),
        tolerance_ppm=10.0,
        aligned_rt_tolerance_seconds=5.0,
        apex_tolerance_seconds=5.0,
        fragment_ms_level=1,
        selected_precursor_ids=("prec_peptide",),
    )

    summary_tsv = render_raw_signal_evidence_card_summary_tsv(report)
    card_tsv = render_raw_signal_evidence_card_tsv(report)
    html = render_raw_signal_evidence_cards_html(report)

    assert summary_tsv.splitlines()[0] == (
        "card_count\twarning_card_count\tspectrum_evidence_card_count\t"
        "fragment_support_card_count\tretention_time_flagged_card_count\t"
        "isotope_fit_card_count"
    )
    assert summary_tsv.splitlines()[1] == "1\t1\t1\t1\t1\t0"
    assert (
        "raw-signal-card:prec_peptide\tprec_peptide\tPEPTIDE\tPEPTIDE precursor\t400.687246\t"
        "prec_peptide_ms1\t2\t1\t0\t2\t1\t2\t2\t"
        "chimeric_spectrum|chromatographic_peak_concern|retention_time_alignment_outside_tolerance|weak_fragment_support"
        in card_tsv
    )
    assert "<h2>PEPTIDE (prec_peptide)</h2>" in html
    assert "scan=9002" in html
    assert "retention_time_alignment_outside_tolerance" in html
    assert "peptide_b4|peptide_y8" in html
