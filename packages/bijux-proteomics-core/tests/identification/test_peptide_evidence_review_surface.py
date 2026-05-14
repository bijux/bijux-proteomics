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

    assert review.summary.total_peptides == 6
    assert review.summary.accepted_peptides == 4
    assert review.summary.rejected_peptides == 2
    assert review.summary.strong_count == 2
    assert review.summary.weak_count == 2
    assert review.summary.unique_count == 5
    assert review.summary.shared_count == 1
    assert review.summary.modified_count == 1
    assert review.summary.contaminant_count == 1
    assert review.summary.decoy_count == 1

    by_peptide = {entry.canonical_peptide: entry for entry in review.entries}
    assert by_peptide["STRONGK"].primary_class is PeptideEvidencePrimaryClass.STRONG
    assert by_peptide["SHAREDK"].primary_class is PeptideEvidencePrimaryClass.WEAK
    assert PeptideEvidenceTag.SHARED in by_peptide["SHAREDK"].tags
    assert PeptideEvidenceTag.MODIFIED in by_peptide["ACDM[Oxidation]K"].tags
    assert (
        by_peptide["CONTAMK"].primary_class is PeptideEvidencePrimaryClass.CONTAMINANT
    )
    assert by_peptide["DECOYSEQ"].primary_class is PeptideEvidencePrimaryClass.DECOY
    assert by_peptide["DECOYSEQ"].accepted is False
    assert by_peptide["LOWCONFK"].accepted is False

    summary_tsv = render_peptide_evidence_summary_tsv(review)
    entries_tsv = render_peptide_evidence_entries_tsv(review)

    assert "strong_count\t2" in summary_tsv
    assert "weak_count\t2" in summary_tsv
    assert (
        "ACDM[Oxidation]K\tACDM[Oxidation]K\tstrong\tunique;modified\t0.0\ttrue"
        in entries_tsv
    )
    assert "CONTAMK\tCONTAMK\tcontaminant\tunique;contaminant" in entries_tsv
