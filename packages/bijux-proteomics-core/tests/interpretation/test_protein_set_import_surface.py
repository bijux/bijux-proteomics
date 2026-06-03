# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation import parse_protein_set_table


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "interpretation" / name


def test_parse_protein_set_table_preserves_memberships_and_rejections() -> None:
    report = parse_protein_set_table(_fixture_path("protein_sets_invalid.tsv"))

    assert report.total_rows == 3
    assert report.summary.accepted_record_count == 1
    assert report.summary.rejected_row_count == 2
    assert report.summary.distinct_set_count == 1
    assert report.summary.distinct_member_count == 1
    assert report.summary.source_counts == {"curated": 1}
    record = report.accepted_records[0]
    assert record.set_id == "activation"
    assert record.protein_ref == "P001"
    rejected_reasons = {row.reason for row in report.rejected_rows}
    assert (
        "duplicate protein set membership for activation and protein P001"
        in rejected_reasons
    )
    assert "protein set row requires protein_ref" in rejected_reasons


def test_parse_protein_set_table_preserves_optional_category_and_accession_fields() -> (
    None
):
    report = parse_protein_set_table(_fixture_path("protein_set_enrichment.tsv"))

    assert report.summary.accepted_record_count == 6
    first_record = report.accepted_records[0]
    assert first_record.set_category == "compartment"
    assert first_record.source_accession == "SL-0191"
