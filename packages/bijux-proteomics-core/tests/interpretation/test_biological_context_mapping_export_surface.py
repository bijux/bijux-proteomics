# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation.biological_context_mapping import (
    build_biological_context_mapping_report,
    parse_biological_context_table,
    render_biological_context_mapping_summary_tsv,
    render_biological_context_mapping_tsv,
    render_biological_context_term_tsv,
    render_rejected_biological_context_tsv,
    render_unmapped_biological_context_tsv,
)
from bijux_proteomics.interpretation.protein_annotation_mapping import (
    parse_protein_reference_table,
)


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "interpretation" / name


def test_biological_context_renderers_emit_summary_mapping_term_unmapped_and_rejected_ledgers() -> (
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

    summary_tsv = render_biological_context_mapping_summary_tsv(report)
    mapped_tsv = render_biological_context_mapping_tsv(report)
    term_tsv = render_biological_context_term_tsv(report)
    unmapped_tsv = render_unmapped_biological_context_tsv(report)
    rejected_tsv = render_rejected_biological_context_tsv(context_table)

    assert "input_entry_count" in summary_tsv.splitlines()[0]
    assert "drug_target" in summary_tsv
    assert "context_kind\tcontext_id\tcontext_name" in term_tsv.splitlines()[0]
    assert "DrugBank" in mapped_tsv
    assert "DRUGBANK:DB0001" in mapped_tsv
    assert "supporting_protein_refs" in term_tsv.splitlines()[0]
    assert "P04637" in term_tsv
    assert "UNKNOWN123" in unmapped_tsv
    assert "duplicate biological context mapping" in rejected_tsv
