# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm import (
    build_ptm_site_ambiguity_report,
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
)
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document


def _ptm_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


def _fasta_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "fasta" / name


def _protein_sequences() -> dict[str, str]:
    report = parse_fasta_document(
        _fasta_fixture("ptm_sites.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )
    return {
        record.canonical_accession: record.residues
        for record in report.accepted_records
    }


def test_ptm_site_mapping_marks_shared_peptide_mappings_explicitly() -> None:
    evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    shared = [
        mapping for mapping in mappings if mapping.localized_peptide == "AS[Phospho]TYK"
    ]

    assert shared
    assert all(mapping.shared_peptide is True for mapping in shared)
    assert all(mapping.ambiguous is True for mapping in shared)
    assert {mapping.protein_ref for mapping in shared} == {"P11111", "P22222"}


def test_ptm_site_ambiguity_report_preserves_shared_peptide_reason() -> None:
    evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = build_ptm_site_table(mappings)
    ambiguity = build_ptm_site_ambiguity_report(site_table)

    shared = [entry for entry in ambiguity if entry.shared_peptide]

    assert shared
    assert all(
        entry.reason == "localized peptide is shared across multiple protein references"
        for entry in shared
    )
