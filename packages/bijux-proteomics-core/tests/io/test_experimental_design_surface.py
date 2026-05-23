# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import (
    ExperimentalDesignSampleRole,
    parse_experimental_design_table,
)


def test_parse_experimental_design_table_accepts_csv_rows_and_metadata(
    tmp_path: Path,
) -> None:
    design_path = tmp_path / "study_design.csv"
    design_path.write_text(
        "\n".join(
            (
                "sample_id,condition,replicate,fraction,spectra_file,batch,panel",
                "s1,treated,1,1,run_a.mzML,b1,cohort-a",
                "s2,control,2,1,run_b.mzML,b1,cohort-a",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = parse_experimental_design_table(design_path)

    assert report.rejected_rows == ()
    assert len(report.accepted_entries) == 2
    assert report.accepted_entries[0].replicate == 1
    assert report.accepted_entries[0].fraction == 1
    assert report.accepted_entries[0].sample_role is ExperimentalDesignSampleRole.SAMPLE
    assert report.accepted_entries[0].metadata["panel"] == "cohort-a"


def test_parse_experimental_design_table_rejects_missing_required_columns(
    tmp_path: Path,
) -> None:
    design_path = tmp_path / "missing_design.tsv"
    design_path.write_text(
        "sample_id\tcondition\treplicate\tfraction\ns1\ttreated\t1\t1\n",
        encoding="utf-8",
    )

    report = parse_experimental_design_table(design_path)

    assert report.accepted_entries == ()
    assert len(report.rejected_rows) == 1
    assert report.rejected_rows[0].row_number == 1
    assert report.rejected_rows[0].issues[0].code == "missing_design_column"
    assert report.rejected_rows[0].issues[0].field == "spectra_file"


def test_parse_experimental_design_table_preserves_row_validation_semantics(
    tmp_path: Path,
) -> None:
    design_path = tmp_path / "invalid_design.tsv"
    design_path.write_text(
        "\n".join(
            (
                "sample_id\tcondition\treplicate\tfraction\tspectra_file\tsample_role",
                "s1\ttreated\tone\t1\trun_a.mzML\tsample",
                "s2\tcontrol\t2\t1\trun_b.mzML\tqc_bridge",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = parse_experimental_design_table(design_path)

    assert report.accepted_entries == ()
    assert len(report.rejected_rows) == 2
    assert report.rejected_rows[0].issues[0].code == "invalid_design_row"
    assert "invalid integer value" in report.rejected_rows[0].issues[0].message
    assert report.rejected_rows[1].issues[0].code == "invalid_design_row"
    assert "non-sample multiplex roles require explicit multiplex_group" in (
        report.rejected_rows[1].issues[0].message
    )


def test_parse_experimental_design_table_accepts_multi_run_sample_rows(
    tmp_path: Path,
) -> None:
    design_path = tmp_path / "duplicate_design.tsv"
    design_path.write_text(
        "\n".join(
            (
                "sample_id\tcondition\treplicate\tfraction\tspectra_file\ttechnical_replicate_id",
                "s1\ttreated\t1\t1\trun_a.mzML\ttech-1",
                "s1\ttreated\t1\t1\trun_b.mzML\ttech-2",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = parse_experimental_design_table(design_path)

    assert report.rejected_rows == ()
    assert len(report.accepted_entries) == 2
    assert report.accepted_entries[0].sample_id == "s1"
    assert report.accepted_entries[0].technical_replicate_id == "tech-1"
    assert report.accepted_entries[1].technical_replicate_id == "tech-2"
