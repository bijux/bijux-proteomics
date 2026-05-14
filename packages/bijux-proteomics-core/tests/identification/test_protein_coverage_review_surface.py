# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification import (
    PsmRecord,
    build_protein_coverage_map,
    build_protein_coverage_review_report,
    filter_psms_by_fdr,
    parse_psm_tsv,
    render_protein_coverage_entries_tsv,
    render_protein_coverage_regions_tsv,
    render_protein_coverage_summary_tsv,
)
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document

from .test_identification_surface import _default_mapping, _fasta_fixture, _psm_fixture


def test_protein_coverage_review_reports_regions_and_shared_peptides() -> None:
    report = parse_psm_tsv(
        _psm_fixture("protein_inference_results.tsv"), mapping=_default_mapping()
    )
    accepted = filter_psms_by_fdr(report.accepted_records, threshold=0.05)
    fasta_report = parse_fasta_document(
        _fasta_fixture("protein_inference.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )
    protein_sequences = {
        record.canonical_accession: record.residues
        for record in fasta_report.accepted_records
    }

    coverage = build_protein_coverage_review_report(
        accepted,
        protein_sequences=protein_sequences,
        threshold=0.05,
    )

    assert coverage.summary.total_proteins == 4
    assert coverage.summary.proteins_with_sequence == 4
    assert coverage.summary.proteins_missing_sequence == 0
    assert coverage.summary.proteins_with_unique_peptides == 2
    assert coverage.summary.proteins_with_shared_peptides == 3
    assert coverage.summary.total_regions == 7
    assert coverage.summary.total_covered_residues == 50

    p11111 = next(entry for entry in coverage.entries if entry.protein_ref == "P11111")
    p22222 = next(entry for entry in coverage.entries if entry.protein_ref == "P22222")

    assert p11111.coverage_fraction == 15 / 21
    assert p11111.covered_ranges == ((2, 9), (13, 19))
    assert p11111.unique_peptides == ("PEPTIDEK",)
    assert p11111.shared_peptides == ("SHAREDK",)
    assert p11111.covered_peptides == ("PEPTIDEK", "SHAREDK")
    assert p11111.unmatched_peptides == ()

    assert p22222.coverage_fraction == 14 / 20
    assert p22222.covered_ranges == ((3, 9), (12, 18))
    assert p22222.unique_peptides == ()
    assert p22222.shared_peptides == ("GLYGLYK", "SHAREDK")

    summary_tsv = render_protein_coverage_summary_tsv(coverage)
    entries_tsv = render_protein_coverage_entries_tsv(coverage)
    regions_tsv = render_protein_coverage_regions_tsv(coverage)

    assert "total_covered_residues\t50" in summary_tsv
    assert "P11111\t21\t15\t0.7142857142857143\t2-9;13-19" in entries_tsv
    assert "P22222\t2\t12\t18\t7" in regions_tsv


def test_protein_coverage_surfaces_match_modified_peptides_by_sequence() -> None:
    records = (
        PsmRecord(
            spectrum_id="scan=mod-1",
            peptide="ACDMK",
            canonical_peptide="ACDM[Oxidation]K",
            charge=2,
            score=42.0,
            q_value=0.01,
            protein_refs=("P55555",),
        ),
    )

    coverage_map = build_protein_coverage_map(
        records,
        protein_sequences={"P55555": "TTACDMKAA"},
    )
    review = build_protein_coverage_review_report(
        records,
        protein_sequences={"P55555": "TTACDMKAA"},
    )

    assert coverage_map[0].covered_ranges == ((3, 7),)
    assert coverage_map[0].covered_peptides == ("ACDMK",)
    assert review.entries[0].covered_ranges == ((3, 7),)
    assert review.entries[0].covered_peptides == ("ACDM[Oxidation]K",)
    assert review.entries[0].unmatched_peptides == ()
