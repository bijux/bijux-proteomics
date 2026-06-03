# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification import (
    PeptideEvidencePrimaryClass,
    PeptideEvidenceTag,
    build_peptide_evidence_review_report,
    parse_psm_tsv,
    render_peptide_evidence_entries_tsv,
    render_peptide_evidence_summary_tsv,
)

from .test_identification_surface import _default_mapping, _psm_fixture


def test_peptide_evidence_review_reports_primary_classes_and_tags() -> None:
    report = parse_psm_tsv(
        _psm_fixture("peptide_evidence_classes.tsv"), mapping=_default_mapping()
    )

    review = build_peptide_evidence_review_report(
        report.accepted_records,
        threshold=0.05,
        strong_q_value=0.01,
    )

    assert review.summary.total_peptides == 8
    assert review.summary.accepted_peptides == 5
    assert review.summary.rejected_peptides == 3
    assert review.summary.strong_count == 1
    assert review.summary.moderate_count == 1
    assert review.summary.weak_count == 2
    assert review.summary.shared_count == 1
    assert review.summary.ambiguous_count == 1
    assert review.summary.unique_count == 5
    assert review.summary.modified_count == 1
    assert review.summary.reproducible_count == 2
    assert review.summary.contaminant_count == 1
    assert review.summary.decoy_count == 1

    by_peptide = {entry.canonical_peptide: entry for entry in review.entries}
    assert by_peptide["STRONGK"].primary_class is PeptideEvidencePrimaryClass.STRONG
    assert by_peptide["SHAREDFINEK"].primary_class is PeptideEvidencePrimaryClass.SHARED
    assert by_peptide["SHAREDK"].primary_class is PeptideEvidencePrimaryClass.WEAK
    assert PeptideEvidenceTag.SHARED in by_peptide["SHAREDK"].tags
    assert (
        by_peptide["ACDM[Oxidation]K"].primary_class
        is PeptideEvidencePrimaryClass.MODERATE
    )
    assert PeptideEvidenceTag.MODIFIED in by_peptide["ACDM[Oxidation]K"].tags
    assert by_peptide["AMBIGK"].primary_class is PeptideEvidencePrimaryClass.AMBIGUOUS
    assert (
        by_peptide["CONTAMK"].primary_class is PeptideEvidencePrimaryClass.CONTAMINANT
    )
    assert by_peptide["DECOYSEQ"].primary_class is PeptideEvidencePrimaryClass.DECOY
    assert by_peptide["DECOYSEQ"].accepted is False
    assert by_peptide["LOWCONFK"].accepted is False

    summary_tsv = render_peptide_evidence_summary_tsv(review)
    entries_tsv = render_peptide_evidence_entries_tsv(review)

    assert "strong_count\t1" in summary_tsv
    assert "moderate_count\t1" in summary_tsv
    assert "weak_count\t2" in summary_tsv
    assert "shared_count\t1" in summary_tsv
    assert "ambiguous_count\t1" in summary_tsv
    assert (
        "ACDM[Oxidation]K\tACDM[Oxidation]K\tmoderate\tunique;modified" in entries_tsv
    )
    assert "CONTAMK\tCONTAMK\tcontaminant\tunique;contaminant" in entries_tsv


def test_peptide_evidence_review_keeps_duplicate_psm_support_on_one_peptide_row() -> (
    None
):
    report = parse_psm_tsv(
        _psm_fixture("duplicate_spectrum_results.tsv"), mapping=_default_mapping()
    )

    review = build_peptide_evidence_review_report(
        report.accepted_records,
        threshold=0.05,
    )

    assert review.summary.total_peptides == 2
    peptide_entry = next(
        entry for entry in review.entries if entry.canonical_peptide == "PEPTIDER"
    )
    assert peptide_entry.psm_count == 2
    assert peptide_entry.spectrum_count == 2
    assert PeptideEvidenceTag.REPRODUCIBLE in peptide_entry.tags
