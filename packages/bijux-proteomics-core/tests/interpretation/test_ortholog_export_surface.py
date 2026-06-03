# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation import (
    build_ortholog_mapping_report,
    parse_ortholog_table,
    parse_protein_reference_table,
    render_mapped_ortholog_tsv,
    render_ortholog_mapping_summary_tsv,
    render_rejected_ortholog_tsv,
    render_unmapped_ortholog_tsv,
)


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "interpretation" / name


def test_ortholog_renderers_emit_summary_mapped_unmapped_and_rejected_ledgers() -> None:
    protein_table = parse_protein_reference_table(_fixture_path("ortholog_input.tsv"))
    ortholog_table = parse_ortholog_table(_fixture_path("ortholog_mappings.tsv"))
    mapping_table = parse_ortholog_table(_fixture_path("ortholog_relationships.tsv"))
    report = build_ortholog_mapping_report(
        protein_table.accepted_entries,
        mapping_table.accepted_records,
        source_species="human",
        target_species="mouse",
    )

    summary_tsv = render_ortholog_mapping_summary_tsv(report)
    mapped_tsv = render_mapped_ortholog_tsv(report)
    unmapped_tsv = render_unmapped_ortholog_tsv(report)
    rejected_tsv = render_rejected_ortholog_tsv(ortholog_table)

    assert summary_tsv.splitlines()[0].startswith(
        "source_species\ttarget_species\tinput_entry_count\tmapped_entry_count"
    )
    assert "P005\thuman\tmouse\tM005" in mapped_tsv
    assert "P999\thuman\tmouse" in unmapped_tsv
    assert (
        "duplicate ortholog relationship for human:P12345 -> mouse:Q9AAA1"
        in rejected_tsv
    )
