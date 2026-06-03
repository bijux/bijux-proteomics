# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation import parse_protein_reference_table


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "interpretation" / name


def test_parse_protein_reference_table_canonicalizes_supported_reference_families() -> (
    None
):
    report = parse_protein_reference_table(
        _fixture_path("protein_annotation_input.tsv")
    )

    assert report.total_rows == 6
    assert report.summary.accepted_entry_count == 6
    assert report.summary.rejected_row_count == 1
    assert report.summary.distinct_protein_ref_count == 5
    accepted_by_row = {
        (entry.source_row_id, entry.input_protein_ref): entry.protein_ref
        for entry in report.accepted_entries
    }
    assert accepted_by_row[("row-1", "sp|P04637|P53_HUMAN")] == "P04637"
    assert accepted_by_row[("row-2", "ref|NP_000537.3|CALM1_HUMAN")] == "NP_000537.3"
    assert accepted_by_row[("row-3", "ENSP00000354587")] == "ENSP00000354587"
    assert accepted_by_row[("row-6", "lab_bait_001")] == "lab_bait_001"
    assert (
        report.rejected_rows[0].reason
        == "protein row requires at least one protein reference"
    )
