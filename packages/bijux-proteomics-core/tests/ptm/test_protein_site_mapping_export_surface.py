# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm import (
    build_ptm_protein_site_mapping_report,
    build_ptm_site_table,
    parse_ptm_localization_tsv,
    render_ptm_protein_site_mapping_tsv,
    render_ptm_site_table_tsv,
    render_ptm_unmapped_peptide_tsv,
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
    mapping_report = build_ptm_protein_site_mapping_report(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    mappings = mapping_report.mappings
    site_table = build_ptm_site_table(mappings)

    mapping_lines = render_ptm_protein_site_mapping_tsv(mappings).splitlines()
    site_lines = render_ptm_site_table_tsv(site_table).splitlines()

    assert evidence.accepted_records[0].provenance.source_engine == "ptm-localization"
    assert mapping_lines[0].startswith(
        "spectrum_id\tsample_id\tprotein_ref\tlocalized_peptide"
    )
    assert any(
        line
        == "scan=ptm-005\tC1\tP11111\tAS[Phospho]TYK\tAS[Phospho]TYK\tPhospho\tS\t2\t17\t0.7\t0.02\t17;18;19\ttrue\ttrue\ttarget"
        for line in mapping_lines
    )
    assert site_lines[0].startswith("site_key\tprotein_ref\tresidue\tposition")
    assert "source_engine" in site_lines[0]
    assert any(
        line.startswith(
            "P11111:S5:Phospho\tP11111\tS\t5\tPhospho\t0.996\t0.003\t4\t1\tC1;C2;T1;T2\t5\tfalse\tfalse\ttarget\tptm-localization\t"
        )
        for line in site_lines
    )
    assert mapping_report.unmapped_peptides == ()


def test_ptm_unmapped_peptide_renderer_preserves_reason_ledgers(tmp_path: Path) -> None:
    evidence_path = tmp_path / "unmapped.tsv"
    evidence_path.write_text(
        "\n".join(
            (
                "sample_id\tspectrum_id\tpeptide\tcharge\tscore\tq_value\tproteins\tlocalization_score\tcandidate_sites\tdecoy_label",
                "C1\tscan=unmapped\tS[Phospho]PEPTIDEK\t2\t110.0\t0.005\tP40404\t0.990\t1\ttarget",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    evidence = parse_ptm_localization_tsv(evidence_path)
    mapping_report = build_ptm_protein_site_mapping_report(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )

    lines = render_ptm_unmapped_peptide_tsv(
        mapping_report.unmapped_peptides
    ).splitlines()

    assert lines[0].startswith(
        "spectrum_id\tsample_id\tlocalized_peptide\tcanonical_peptide\tprotein_refs"
    )
    assert any(
        line.startswith(
            "scan=unmapped\tC1\tS[Phospho]PEPTIDEK\tS[Phospho]PEPTIDEK\tP40404\tPhospho\tS\t1\t1\tmissing_protein_sequence"
        )
        for line in lines
    )
