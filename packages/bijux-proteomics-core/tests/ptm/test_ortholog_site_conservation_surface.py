# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm import (
    PtmOrthologConservationStatus,
    build_ptm_ortholog_conservation_report,
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
    parse_ptm_ortholog_site_tsv,
    render_ptm_ortholog_conservation_tsv,
)
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document


def _fixture_path(name: str) -> Path:
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


def test_parse_ptm_ortholog_site_tsv_preserves_missing_targets_and_rejections() -> None:
    report = parse_ptm_ortholog_site_tsv(_fixture_path("ptm_ortholog_sites.tsv"))

    assert report.summary.accepted_record_count == 3
    assert report.summary.rejected_row_count == 2
    assert report.summary.missing_target_count == 1
    assert report.summary.target_site_count == 2
    assert report.accepted_records[0].source_species == "Homo sapiens"
    rejected_messages = {
        issue.message for row in report.rejected_rows for issue in row.issues
    }
    assert "duplicate PTM ortholog-site relationship" in rejected_messages
    assert (
        "target protein, residue, position, and modification must all be present when any target-site field is provided"
        in rejected_messages
    )


def test_build_ptm_ortholog_conservation_report_classifies_status_without_guessing() -> (
    None
):
    evidence = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = build_ptm_site_table(mappings)
    ortholog_report = parse_ptm_ortholog_site_tsv(
        _fixture_path("ptm_ortholog_sites.tsv")
    )

    report = build_ptm_ortholog_conservation_report(
        site_table,
        ortholog_report.accepted_records,
        source_species="Homo sapiens",
        target_species="Mus musculus",
    )

    entries = {entry.site_key: entry for entry in report.entries}
    assert report.summary.observed_site_count == 5
    assert report.summary.conserved_site_count == 1
    assert report.summary.shifted_site_count == 1
    assert report.summary.missing_site_count == 1
    assert report.summary.unmapped_site_count == 2

    assert (
        entries["P11111:S5:Phospho"].status is PtmOrthologConservationStatus.CONSERVED
    )
    assert entries["P11111:S5:Phospho"].ortholog_target_site_keys == (
        "M11111:S5:Phospho",
    )
    assert entries["P11111:S17:Phospho"].status is PtmOrthologConservationStatus.SHIFTED
    assert entries["P11111:S17:Phospho"].ortholog_target_site_keys == (
        "M11111:S19:Phospho",
    )
    assert entries["P22222:Y18:Phospho"].status is PtmOrthologConservationStatus.MISSING
    assert entries["Q9DEC1:S5:Phospho"].status is PtmOrthologConservationStatus.UNMAPPED
    assert "status" in render_ptm_ortholog_conservation_tsv(report).splitlines()[0]
