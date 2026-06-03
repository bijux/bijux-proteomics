# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation import (
    build_ortholog_mapping_report,
    parse_ortholog_table,
    parse_protein_reference_table,
)


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "interpretation" / name


def test_build_ortholog_mapping_report_maps_selected_species_pair() -> None:
    protein_table = parse_protein_reference_table(_fixture_path("ortholog_input.tsv"))
    ortholog_table = parse_ortholog_table(_fixture_path("ortholog_relationships.tsv"))

    report = build_ortholog_mapping_report(
        protein_table.accepted_entries,
        ortholog_table.accepted_records,
        source_species="human",
        target_species="mouse",
    )

    assert report.summary.input_entry_count == 7
    assert report.summary.mapped_entry_count == 9
    assert report.summary.unmapped_entry_count == 1
    assert report.summary.distinct_source_protein_ref_count == 6
    assert report.summary.distinct_target_protein_ref_count == 6
    assert report.summary.one_to_one_count == 1
    mapped_entry = next(
        entry
        for entry in report.mapped_entries
        if entry.source_protein_ref == "P001" and entry.target_protein_ref == "M001"
    )
    assert mapped_entry.target_gene_symbol == "M1"
    assert mapped_entry.evidence == "ensembl"
    assert mapped_entry.ortholog_metadata == {"source_name": "core"}
    unmapped_entry = report.unmapped_entries[0]
    assert unmapped_entry.source_protein_ref == "P999"
    assert unmapped_entry.reason == (
        "no ortholog relationship for selected species pair human -> mouse"
    )
