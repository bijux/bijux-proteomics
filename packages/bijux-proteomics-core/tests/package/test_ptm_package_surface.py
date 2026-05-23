# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import bijux_proteomics.ptm as ptm
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


def test_ptm_package_exports_protein_site_mapping_owner_surface() -> None:
    evidence = ptm.parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    report = ptm.build_ptm_protein_site_mapping_report(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    rendered = ptm.render_ptm_unmapped_peptide_tsv(report.unmapped_peptides)

    assert hasattr(ptm, "build_ptm_protein_site_mapping_report")
    assert hasattr(ptm, "render_ptm_unmapped_peptide_tsv")
    assert len(report.ambiguous_mappings) == 4
    assert rendered.splitlines()[0].startswith(
        "spectrum_id\tsample_id\tlocalized_peptide"
    )
