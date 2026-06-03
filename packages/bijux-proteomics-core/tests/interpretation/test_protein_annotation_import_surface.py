# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation import parse_protein_annotation_table


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "interpretation" / name


def test_parse_protein_annotation_table_preserves_custom_annotations_and_rejected_rows() -> (
    None
):
    report = parse_protein_annotation_table(
        _fixture_path("protein_annotation_custom.tsv")
    )

    assert report.total_rows == 4
    assert report.summary.accepted_record_count == 2
    assert report.summary.rejected_row_count == 2
    assert report.summary.distinct_protein_ref_count == 2
    assert report.summary.gene_annotated_count == 2
    assert report.summary.organism_annotated_count == 2
    assert report.summary.annotation_identifier_count == 2
    custom_record = next(
        record for record in report.accepted_records if record.protein_ref == "Q99999"
    )
    assert custom_record.gene_symbol == "CUST1"
    assert custom_record.description == "Custom signaling protein"
    assert custom_record.annotation_identifier == "CUSTOM:Q99999"
    assert custom_record.metadata == {"source": "curated"}
    rejected_reasons = {row.reason for row in report.rejected_rows}
    assert "protein annotation row requires protein_ref" in rejected_reasons
    assert "duplicate protein annotation for P04637" in rejected_reasons
