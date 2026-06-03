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
    export_ptm_mapped_site_annotation_tsv,
    export_ptm_site_annotation_biology_tsv,
    export_ptm_site_annotation_mapping_summary_tsv,
    export_ptm_unmapped_site_annotation_tsv,
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


def test_ptm_site_annotation_exports_preserve_mapped_unmapped_and_biology_ledgers(
    tmp_path: Path,
) -> None:
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
    biology_summary = build_ptm_site_annotation_biology_summary(mapping_report)

    summary_path = tmp_path / "ptm.annotation.summary.tsv"
    mapped_path = tmp_path / "ptm.annotation.mapped.tsv"
    unmapped_path = tmp_path / "ptm.annotation.unmapped.tsv"
    kinase_path = tmp_path / "ptm.annotation.kinase.tsv"
    phosphatase_path = tmp_path / "ptm.annotation.phosphatase.tsv"

    export_ptm_site_annotation_mapping_summary_tsv(
        mapping_report,
        summary_path,
    )
    export_ptm_mapped_site_annotation_tsv(
        mapping_report,
        mapped_path,
    )
    export_ptm_unmapped_site_annotation_tsv(
        mapping_report,
        unmapped_path,
    )
    export_ptm_site_annotation_biology_tsv(
        biology_summary,
        category="kinase",
        path=kinase_path,
    )
    export_ptm_site_annotation_biology_tsv(
        biology_summary,
        category="phosphatase",
        path=phosphatase_path,
    )

    assert summary_path.read_text().splitlines()[0] == (
        "target_species\tmatched_annotation_count\tmatched_site_count\t"
        "unmapped_annotation_count\tspecies_mismatch_count"
    )
    assert "P11111:S5:Phospho" in mapped_path.read_text()
    assert "Mus musculus" in unmapped_path.read_text()
    assert "AKT1\t1\tP11111:S5:Phospho" in kinase_path.read_text()
    assert "PPP2CA\t1\tP11111:S5:Phospho" in phosphatase_path.read_text()
