# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm import build_ptm_report_bundle, parse_ptm_localization_tsv
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document


def _ptm_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


def _protein_sequences() -> dict[str, str]:
    fasta = (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "fasta"
        / "ptm_sites.fasta"
    )
    report = parse_fasta_document(fasta.read_text(), mode=FastaParseMode.STRICT)
    return {
        record.canonical_accession: record.residues
        for record in report.accepted_records
    }


def test_ptm_report_bundle_builds_core_peptide_and_site_surfaces() -> None:
    evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))

    report = build_ptm_report_bundle(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )

    assert report.summary.accepted_evidence_count == 8
    assert report.summary.peptide_entry_count == 8
    assert report.summary.site_row_count == 5
    assert report.summary.ambiguous_site_count == 2
    assert report.summary.modified_peptide_count == 3
    assert any(
        entry.localized_peptide == "S[Phospho]PEPTIDEK"
        for entry in report.peptide_entries
    )
    assert any(
        entry.site_key == "P11111:S5:Phospho"
        for entry in report.site_table
    )
