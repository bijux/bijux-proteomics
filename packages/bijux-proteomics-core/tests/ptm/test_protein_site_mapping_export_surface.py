# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm import (
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
    render_ptm_protein_site_mapping_tsv,
    render_ptm_site_table_tsv,
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


def test_ptm_protein_site_renderers_preserve_mapping_and_site_ledgers() -> None:
    evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = build_ptm_site_table(mappings)

    mapping_lines = render_ptm_protein_site_mapping_tsv(mappings).splitlines()
    site_lines = render_ptm_site_table_tsv(site_table).splitlines()

    assert mapping_lines[0].startswith(
        "spectrum_id\tsample_id\tprotein_ref\tlocalized_peptide"
    )
    assert any(
        line
        == "scan=ptm-005\tC1\tP11111\tAS[Phospho]TYK\tAS[Phospho]TYK\tPhospho\tS\t2\t17\t0.7\t0.02\t17;18;19\ttrue\ttrue\ttarget"
        for line in mapping_lines
    )
    assert site_lines[0].startswith("site_key\tprotein_ref\tresidue\tposition")
    assert any(
        line == "P11111:S5:Phospho\tP11111\tS\t5\tPhospho\t0.996\t0.003\t4\t1\tC1;C2;T1;T2\t5\tfalse\tfalse\ttarget"
        for line in site_lines
    )
