# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation import GoAspect, parse_go_annotation_table


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "interpretation" / name


def test_parse_go_annotation_table_preserves_memberships_and_rejected_rows() -> None:
    report = parse_go_annotation_table(_fixture_path("go_annotations.tsv"))

    assert report.total_rows == 8
    assert report.summary.accepted_record_count == 6
    assert report.summary.rejected_row_count == 2
    assert report.summary.distinct_protein_ref_count == 5
    assert report.summary.distinct_go_term_count == 5
    assert report.summary.aspect_counts == {
        "biological_process": 4,
        "cellular_component": 1,
        "molecular_function": 1,
    }
    apoptosis = next(
        record
        for record in report.accepted_records
        if record.protein_ref == "P04637" and record.go_term_id == "GO:0006915"
    )
    assert apoptosis.go_term_name == "apoptotic process"
    assert apoptosis.go_aspect is GoAspect.BIOLOGICAL_PROCESS
    assert apoptosis.evidence_code == "IDA"
    assert apoptosis.metadata == {"source": "curated"}
    rejected_reasons = {row.reason for row in report.rejected_rows}
    assert "duplicate GO membership for P04637 and GO:0006915" in rejected_reasons
    assert "GO annotation row requires protein_ref" in rejected_reasons
