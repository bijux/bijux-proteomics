# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation import parse_ortholog_table


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "interpretation" / name


def test_parse_ortholog_table_preserves_species_pairs_and_rejected_rows() -> None:
    report = parse_ortholog_table(_fixture_path("ortholog_mappings.tsv"))

    assert report.total_rows == 6
    assert report.summary.accepted_record_count == 3
    assert report.summary.rejected_row_count == 3
    assert report.summary.distinct_source_species_count == 2
    assert report.summary.distinct_target_species_count == 1
    assert report.summary.distinct_source_protein_ref_count == 3
    assert report.summary.distinct_target_protein_ref_count == 3
    accepted_record = next(
        record
        for record in report.accepted_records
        if record.source_protein_ref == "P67890"
    )
    assert accepted_record.source_species == "human"
    assert accepted_record.target_species == "mouse"
    assert accepted_record.target_gene_symbol == "TGT3"
    assert accepted_record.metadata == {"source_name": "high_confidence"}
    rejected_reasons = {row.reason for row in report.rejected_rows}
    assert "ortholog row requires source_protein_ref" in rejected_reasons
    assert "ortholog row requires target_protein_ref" in rejected_reasons
    assert (
        "duplicate ortholog relationship for human:P12345 -> mouse:Q9AAA1"
        in rejected_reasons
    )
