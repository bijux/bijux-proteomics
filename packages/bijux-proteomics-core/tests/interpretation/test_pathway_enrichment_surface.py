# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation import (
    PathwayMemberKind,
    build_pathway_enrichment_report,
    parse_pathway_membership_table,
    parse_protein_annotation_table,
    parse_protein_reference_table,
)
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "interpretation" / name


def _fasta_fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "interpretation" / name


def test_build_pathway_enrichment_report_evaluates_gene_and_protein_pathways() -> None:
    foreground = parse_protein_reference_table(_fixture_path("pathway_foreground.tsv"))
    background = parse_protein_reference_table(_fixture_path("pathway_background.tsv"))
    pathway_memberships = parse_pathway_membership_table(
        _fixture_path("pathway_memberships.tsv")
    )
    fasta_report = parse_fasta_document(
        _fasta_fixture_path("protein_annotation_reference.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )
    custom_annotations = parse_protein_annotation_table(
        _fixture_path("protein_annotation_custom.tsv")
    )

    report = build_pathway_enrichment_report(
        foreground.accepted_entries,
        background.accepted_entries,
        pathway_memberships.accepted_records,
        fasta_records=fasta_report.accepted_records,
        custom_annotations=custom_annotations.accepted_records,
    )

    assert report.summary.foreground_size == 3
    assert report.summary.background_size == 6
    assert report.summary.evaluated_entry_count == 5
    assert report.summary.protein_entry_count == 2
    assert report.summary.gene_entry_count == 3
    assert report.summary.unresolved_background_count == 3

    kegg_entry = next(
        entry
        for entry in report.entries
        if entry.pathway_id == "hsa04115"
        and entry.member_kind is PathwayMemberKind.GENE
    )
    assert kegg_entry.foreground_member_ids == ("TP53",)
    assert kegg_entry.source_name == "KEGG"

    stress_entry = next(
        entry
        for entry in report.entries
        if entry.pathway_id == "custom:stress"
        and entry.member_kind is PathwayMemberKind.PROTEIN
    )
    assert stress_entry.foreground_member_ids == ("Q99999",)
    assert stress_entry.source_name == "custom"
    assert any(
        item.set_role == "background" and item.protein_ref == "Q88888"
        for item in report.unresolved_members
    )
