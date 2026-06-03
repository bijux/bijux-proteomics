# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation import (
    PathwayMemberKind,
    parse_pathway_membership_table,
)


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "interpretation" / name


def test_parse_pathway_membership_table_preserves_gene_and_protein_memberships() -> (
    None
):
    report = parse_pathway_membership_table(_fixture_path("pathway_memberships.tsv"))

    assert report.total_rows == 7
    assert report.summary.accepted_record_count == 5
    assert report.summary.rejected_row_count == 2
    assert report.summary.distinct_pathway_count == 4
    assert report.summary.member_kind_counts == {"gene": 3, "protein": 2}
    assert report.summary.source_counts == {"KEGG": 1, "Reactome": 2, "custom": 2}
    mapk = next(
        record
        for record in report.accepted_records
        if record.pathway_id == "R-HSA-5673001"
    )
    assert mapk.member_kind is PathwayMemberKind.GENE
    assert mapk.member_id == "MAPK1"
    stress = next(
        record
        for record in report.accepted_records
        if record.pathway_id == "custom:stress"
        and record.member_kind is PathwayMemberKind.PROTEIN
    )
    assert stress.member_id == "Q99999"
    rejected_reasons = {row.reason for row in report.rejected_rows}
    assert (
        "duplicate pathway membership for custom:stress and gene member TP53"
        in rejected_reasons
    )
    assert (
        "pathway membership row requires protein_ref or gene_symbol" in rejected_reasons
    )
