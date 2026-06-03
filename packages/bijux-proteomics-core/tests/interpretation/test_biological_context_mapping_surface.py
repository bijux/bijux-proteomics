# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation.biological_context_mapping import (
    BiologicalContextKind,
    build_biological_context_mapping_report,
    parse_biological_context_table,
)
from bijux_proteomics.interpretation.protein_annotation_mapping import (
    parse_protein_reference_table,
)


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "interpretation" / name


def test_parse_biological_context_table_preserves_supported_kinds_and_rejects_invalid_rows() -> (
    None
):
    report = parse_biological_context_table(
        _fixture_path("biological_context_annotations.tsv")
    )

    assert report.summary.accepted_record_count == 4
    assert report.summary.rejected_row_count == 3
    assert report.summary.distinct_protein_ref_count == 3
    assert report.summary.distinct_context_count == 4
    assert report.summary.context_kind_counts == {
        "disease_term": 1,
        "drug_target": 1,
        "phenotype_term": 1,
        "subcellular_compartment": 1,
    }
    assert report.accepted_records[0].context_kind is BiologicalContextKind.DRUG_TARGET
    assert report.accepted_records[0].metadata == {"curator": "team-a"}
    assert any(
        "duplicate biological context mapping" in row.reason
        for row in report.rejected_rows
    )
    assert any("requires protein_ref" in row.reason for row in report.rejected_rows)
    assert any(
        "unsupported biological context kind" in row.reason
        for row in report.rejected_rows
    )


def test_build_biological_context_mapping_report_preserves_supporting_proteins_and_unmapped_entries() -> (
    None
):
    protein_table = parse_protein_reference_table(
        _fixture_path("biological_context_input.tsv")
    )
    context_table = parse_biological_context_table(
        _fixture_path("biological_context_annotations.tsv")
    )

    report = build_biological_context_mapping_report(
        protein_table.accepted_entries,
        context_table.accepted_records,
    )

    assert report.summary.input_entry_count == 4
    assert report.summary.mapped_entry_count == 4
    assert report.summary.unmapped_entry_count == 1
    assert report.summary.distinct_mapped_protein_ref_count == 3
    assert report.summary.term_count == 4
    assert report.summary.context_kind_counts == {
        "disease_term": 1,
        "drug_target": 1,
        "phenotype_term": 1,
        "subcellular_compartment": 1,
    }
    assert report.unmapped_entries[0].protein_ref == "UNKNOWN123"
    assert (
        "no user-supplied biological context annotation"
        in report.unmapped_entries[0].reason
    )

    drug_term = next(
        entry
        for entry in report.term_entries
        if entry.context_kind is BiologicalContextKind.DRUG_TARGET
    )
    assert drug_term.source_name == "DrugBank"
    assert drug_term.source_accession == "DRUGBANK:DB0001"
    assert drug_term.supporting_protein_refs == ("P04637",)
    assert drug_term.evidence_values == ("curated",)

    compartment_entry = next(
        entry
        for entry in report.mapped_entries
        if entry.protein_ref == "Q9Y243"
        and entry.context_kind is BiologicalContextKind.SUBCELLULAR_COMPARTMENT
    )
    assert compartment_entry.context_name == "cytoplasm"
    assert compartment_entry.context_metadata == {"curator": "team-b"}
