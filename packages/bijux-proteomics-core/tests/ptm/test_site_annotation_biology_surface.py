# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm import (
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
)
from bijux_proteomics.ptm.site_annotation_import import (
    build_ptm_site_annotation_biology_summary,
    build_ptm_site_annotation_mapping_report,
    parse_ptm_site_annotation_tsv,
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


def test_ptm_site_annotation_biology_summary_preserves_function_regulator_and_pathway_terms() -> (
    None
):
    evidence = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = build_ptm_site_table(mappings)
    annotation_report = parse_ptm_site_annotation_tsv(
        _fixture_path("ptm_site_annotations.tsv")
    )
    mapping_report = build_ptm_site_annotation_mapping_report(
        site_table,
        annotation_report.accepted_records,
        target_species="Homo sapiens",
    )

    summary = build_ptm_site_annotation_biology_summary(mapping_report)

    assert any(
        entry.term == "activation-linked phosphosite"
        and entry.site_keys == ("P11111:S5:Phospho",)
        for entry in summary.function_entries
    )
    assert any(
        entry.term == "AKT1" and entry.site_keys == ("P11111:S5:Phospho",)
        for entry in summary.kinase_entries
    )
    assert any(
        entry.term == "PPP2CA" and entry.site_keys == ("P11111:S5:Phospho",)
        for entry in summary.phosphatase_entries
    )
    assert any(
        entry.term == "MAPK signaling" and entry.site_keys == ("P22222:Y18:Phospho",)
        for entry in summary.pathway_entries
    )
