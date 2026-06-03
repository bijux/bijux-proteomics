# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation import (
    ComplexMemberKind,
    parse_complex_membership_table,
)


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "interpretation" / name


def test_parse_complex_membership_table_preserves_member_kind_and_source() -> None:
    report = parse_complex_membership_table(_fixture_path("complex_memberships.tsv"))

    assert report.summary.accepted_record_count == 4
    assert report.summary.rejected_row_count == 2
    assert report.summary.distinct_complex_count == 3
    assert report.summary.member_kind_counts == {"gene": 2, "protein": 2}
    assert report.summary.source_counts == {"CORUM": 2, "custom": 2}
    assert report.accepted_records[0].member_kind is ComplexMemberKind.PROTEIN
    assert report.accepted_records[1].member_kind is ComplexMemberKind.GENE
    assert any(
        row.reason
        == "duplicate complex membership for custom:stressosome and gene member TP53"
        for row in report.rejected_rows
    )
    assert any(
        row.reason == "complex membership row requires protein_ref or gene_symbol"
        for row in report.rejected_rows
    )
