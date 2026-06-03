# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation import parse_ppi_edge_table


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "interpretation" / name


def test_parse_ppi_edge_table_preserves_edges_and_rejections() -> None:
    report = parse_ppi_edge_table(_fixture_path("ppi_edges_invalid.tsv"))

    assert report.total_rows == 4
    assert report.summary.accepted_record_count == 1
    assert report.summary.rejected_row_count == 3
    accepted = report.accepted_records[0]
    assert accepted.protein_ref_a == "P001"
    assert accepted.protein_ref_b == "P002"
    rejected_reasons = {row.reason for row in report.rejected_rows}
    assert "ppi edge row must connect two distinct proteins" in rejected_reasons
    assert "duplicate undirected ppi edge for P001 and P002" in rejected_reasons
    assert (
        "ppi edge interaction_score must be numeric when supplied" in rejected_reasons
    )
