# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation import (
    ProteinAnnotationRecord,
    ProteinAnnotationSourceKind,
    ProteinAnnotationStatus,
    ProteinReferenceEntry,
    build_protein_annotation_mapping_report,
    parse_protein_annotation_table,
    parse_protein_reference_table,
)
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "interpretation" / name


def _fasta_fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "fasta" / name


def test_build_protein_annotation_mapping_report_merges_fasta_and_custom_annotations() -> (
    None
):
    protein_table = parse_protein_reference_table(
        _fixture_path("protein_annotation_input.tsv")
    )
    custom_table = parse_protein_annotation_table(
        _fixture_path("protein_annotation_custom.tsv")
    )
    fasta_report = parse_fasta_document(
        _fasta_fixture_path("production_grade_database.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )
    report = build_protein_annotation_mapping_report(
        protein_table.accepted_entries,
        fasta_report.accepted_records,
        custom_annotations=custom_table.accepted_records,
    )

    assert report.summary.input_entry_count == 6
    assert report.summary.mapped_entry_count == 6
    assert report.summary.unmapped_entry_count == 0
    assert len(report.result_entries) == 6
    assert report.summary.fasta_annotation_count == 3
    assert report.summary.custom_annotation_count == 1
    assert report.summary.merged_annotation_count == 2

    tp53_entry = next(
        entry
        for entry in report.mapped_entries
        if entry.protein_ref == "P04637" and entry.source_row_id == "row-1"
    )
    assert tp53_entry.annotation_source is ProteinAnnotationSourceKind.MERGED
    assert tp53_entry.accession_aliases == ("sp|P04637|P53_HUMAN",)
    assert tp53_entry.gene_symbol == "TRP53"
    assert tp53_entry.description == "Tumor suppressor p53 override"
    assert tp53_entry.organism == "Homo sapiens"
    assert tp53_entry.annotation_identifier == "UNIPROT:P04637"

    custom_only_entry = next(
        entry for entry in report.mapped_entries if entry.protein_ref == "Q99999"
    )
    assert custom_only_entry.annotation_source is ProteinAnnotationSourceKind.CUSTOM
    assert custom_only_entry.source_identifier is None
    assert custom_only_entry.gene_symbol == "CUST1"
    assert custom_only_entry.custom_annotation == {"source": "curated"}


def test_build_protein_annotation_mapping_report_preserves_explicit_unmapped_entries() -> (
    None
):
    fasta_report = parse_fasta_document(
        _fasta_fixture_path("valid_records.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )
    report = build_protein_annotation_mapping_report(
        (
            ProteinReferenceEntry(
                row_number=2,
                source_row_id="row-x",
                input_protein_ref="UNKNOWN123",
                protein_ref="UNKNOWN123",
                metadata={"condition": "treated"},
            ),
        ),
        fasta_report.accepted_records,
        custom_annotations=(
            ProteinAnnotationRecord(
                protein_ref="Q99999",
                gene_symbol="CUST1",
            ),
        ),
    )

    assert report.summary.mapped_entry_count == 0
    assert report.summary.unmapped_entry_count == 1
    assert len(report.result_entries) == 1
    assert report.unmapped_entries[0].protein_ref == "UNKNOWN123"
    assert "not present" in report.unmapped_entries[0].reason
    assert (
        report.result_entries[0].annotation_status is ProteinAnnotationStatus.UNMAPPED
    )
    assert report.result_entries[0].unmapped_reason is not None
