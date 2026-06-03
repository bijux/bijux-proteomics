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


def test_ptm_site_annotation_mapping_report_preserves_matches_and_unmapped_reasons() -> (
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

    report = build_ptm_site_annotation_mapping_report(
        site_table,
        annotation_report.accepted_records,
        target_species="Homo sapiens",
    )

    assert report.summary.matched_annotation_count == 3
    assert report.summary.matched_site_count == 3
    assert report.summary.unmapped_annotation_count == 2
    assert report.summary.species_mismatch_count == 1
    matched = next(
        entry
        for entry in report.matched_annotations
        if entry.site_key == "P11111:S17:Phospho"
    )
    assert matched.ambiguous_site is True
    assert matched.shared_peptide_site is True
    assert matched.kinases == ("PRKAA1",)
    assert matched.phosphatases == ("PPM1A",)
    species_unmapped = next(
        entry
        for entry in report.unmapped_annotations
        if entry.protein_ref == "P11111"
        and entry.position == 5
        and entry.annotation_species == "Mus musculus"
    )
    assert "species" in species_unmapped.reason
    missing_site = next(
        entry for entry in report.unmapped_annotations if entry.protein_ref == "P99999"
    )
    assert "no observed PTM site matched" in missing_site.reason
