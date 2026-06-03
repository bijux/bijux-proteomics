# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm import (
    build_ptm_site_context_report,
    build_ptm_site_table,
    export_ptm_site_context_summary_tsv,
    export_ptm_site_context_tsv,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
)
from bijux_proteomics.ptm.context_annotation import parse_ptm_site_context_tsv
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


def test_ptm_site_context_exports_preserve_site_context_ledgers(tmp_path: Path) -> None:
    evidence = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = build_ptm_site_table(mappings)
    context = parse_ptm_site_context_tsv(_fixture_path("ptm_site_context.tsv"))
    report = build_ptm_site_context_report(site_table, context.accepted_records)

    summary_path = tmp_path / "ptm.context.summary.tsv"
    context_path = tmp_path / "ptm.context.entries.tsv"
    export_ptm_site_context_summary_tsv(report, summary_path)
    export_ptm_site_context_tsv(report, context_path)

    assert summary_path.read_text().splitlines()[0] == (
        "site_count\tcontext_annotated_site_count\toutside_annotation_site_count\t"
        "domain_annotated_site_count\tdisorder_annotated_site_count\t"
        "transmembrane_annotated_site_count\tactive_site_annotated_site_count\t"
        "motif_annotated_site_count\tconservation_annotated_site_count"
    )
    exported = context_path.read_text()
    assert "outside_provided_annotations" in exported
    assert "Q9DEC1:S5:Phospho" in exported
    assert "activation_segment" in exported
    assert "helix_1" in exported
