# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.study import parse_study_design_table


def test_parse_study_design_table_accepts_valid_rows_and_rejects_invalid(
    tmp_path: Path,
) -> None:
    table = tmp_path / "design.tsv"
    table.write_text(
        "study_id\tcohort_id\tcondition_id\tsample_id\treplicate_id\tfraction_id\tinstrument_id\trun_id\tbatch_id\n"
        "S-001\tC-1\tcontrol\tsample-01\tR1\tF1\tinst-a\trun-001\tB1\n"
        "S-001\tC-1\ttreated\tsample-02\tR1\tF1\tinst-a\t\tB1\n",
        encoding="utf-8",
    )

    report = parse_study_design_table(table)

    assert report.total_rows == 2
    assert len(report.accepted_records) == 1
    assert len(report.rejected_rows) == 1
    assert report.rejected_rows[0].issues[0].code == "missing_run_id"
