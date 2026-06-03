# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation import (
    ProteinAnnotationRecord,
    ProteinReferenceEntry,
    build_protein_annotation_mapping_report,
    parse_protein_annotation_table,
    parse_protein_reference_table,
    render_mapped_protein_annotation_tsv,
    render_protein_annotation_summary_tsv,
    render_protein_annotation_tsv,
    render_rejected_protein_annotation_tsv,
    render_rejected_protein_reference_tsv,
    render_unmapped_protein_annotation_tsv,
)
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "interpretation" / name


def _fasta_fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "fasta" / name


def test_protein_annotation_renderers_emit_summary_result_mapped_unmapped_and_rejected_ledgers() -> (
    None
):
    protein_table = parse_protein_reference_table(
        _fixture_path("protein_annotation_input.tsv")
    )
    custom_table = parse_protein_annotation_table(
        _fixture_path("protein_annotation_custom.tsv")
    )
    fasta_report = parse_fasta_document(
        _fasta_fixture_path("valid_records.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )
    mapping_report = build_protein_annotation_mapping_report(
        protein_table.accepted_entries
        + (
            ProteinReferenceEntry(
                row_number=99,
                source_row_id="row-missing",
                input_protein_ref="UNKNOWN123",
                protein_ref="UNKNOWN123",
            ),
        ),
        fasta_report.accepted_records,
        custom_annotations=custom_table.accepted_records
        + (
            ProteinAnnotationRecord(
                protein_ref="Q99999",
                gene_symbol="CUST1",
            ),
        ),
    )

    summary_tsv = render_protein_annotation_summary_tsv(mapping_report)
    result_tsv = render_protein_annotation_tsv(mapping_report)
    mapped_tsv = render_mapped_protein_annotation_tsv(mapping_report)
    unmapped_tsv = render_unmapped_protein_annotation_tsv(mapping_report)
    rejected_input_tsv = render_rejected_protein_reference_tsv(protein_table)
    rejected_annotation_tsv = render_rejected_protein_annotation_tsv(custom_table)

    assert summary_tsv.splitlines()[0].startswith(
        "input_entry_count\tmapped_entry_count"
    )
    assert "annotation_status" in result_tsv.splitlines()[0]
    assert "row-missing\tUNKNOWN123\tUNKNOWN123" in result_tsv
    assert "unmapped" in result_tsv
    assert "TRP53" in mapped_tsv
    assert "accession_aliases" in mapped_tsv.splitlines()[0]
    assert "row-missing\tUNKNOWN123\tUNKNOWN123" in unmapped_tsv
    assert "protein row requires at least one protein reference" in rejected_input_tsv
    assert "duplicate protein annotation for P04637" in rejected_annotation_tsv
