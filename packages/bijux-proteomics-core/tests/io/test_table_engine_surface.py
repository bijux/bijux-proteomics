# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics._tabular import (
    DelimitedColumnSpec,
    DelimitedColumnValueType,
    infer_delimited_table_delimiter,
    parse_delimited_table,
    render_rows_tsv,
    render_tsv_rows,
)


def test_parse_delimited_table_supports_required_columns_coercion_and_missing_values(
    tmp_path: Path,
) -> None:
    table_path = tmp_path / "quant.csv"
    table_path.write_text(
        "sample_id,replicate,intensity,contaminant\n"
        "s1,1,12.5,false\n"
        "s2,2,NA,true\n",
        encoding="utf-8",
    )

    report = parse_delimited_table(
        table_path,
        column_specs=(
            DelimitedColumnSpec(name="sample_id", required=True),
            DelimitedColumnSpec(
                name="replicate",
                required=True,
                value_type=DelimitedColumnValueType.INTEGER,
            ),
            DelimitedColumnSpec(
                name="intensity",
                value_type=DelimitedColumnValueType.FLOAT,
            ),
            DelimitedColumnSpec(
                name="contaminant",
                value_type=DelimitedColumnValueType.BOOLEAN,
            ),
        ),
    )

    assert report.delimiter == ","
    assert report.rejected_rows == ()
    assert len(report.accepted_rows) == 2
    assert report.accepted_rows[0].values["replicate"] == 1
    assert report.accepted_rows[0].values["intensity"] == 12.5
    assert report.accepted_rows[1].values["intensity"] is None
    assert report.accepted_rows[1].values["contaminant"] is True


def test_parse_delimited_table_reports_header_and_row_failures(tmp_path: Path) -> None:
    missing_header_path = tmp_path / "missing.tsv"
    missing_header_path.write_text("sample_id\tintensity\ns1\t10\n", encoding="utf-8")

    header_report = parse_delimited_table(
        missing_header_path,
        column_specs=(
            DelimitedColumnSpec(name="sample_id", required=True),
            DelimitedColumnSpec(name="replicate", required=True),
        ),
    )

    assert len(header_report.rejected_rows) == 1
    assert header_report.rejected_rows[0].issues[0].code == "missing_required_column"

    invalid_row_path = tmp_path / "invalid.tsv"
    invalid_row_path.write_text(
        "sample_id\treplicate\n"
        "s1\tone\n",
        encoding="utf-8",
    )

    row_report = parse_delimited_table(
        invalid_row_path,
        column_specs=(
            DelimitedColumnSpec(name="sample_id", required=True),
            DelimitedColumnSpec(
                name="replicate",
                required=True,
                value_type=DelimitedColumnValueType.INTEGER,
            ),
        ),
    )

    assert row_report.accepted_rows == ()
    assert len(row_report.rejected_rows) == 1
    assert row_report.rejected_rows[0].row_number == 2
    assert row_report.rejected_rows[0].issues[0].code == "invalid_integer_value"


def test_table_engine_infers_delimiter_and_renders_stable_tsv() -> None:
    assert infer_delimited_table_delimiter("a\tb") == "\t"
    assert infer_delimited_table_delimiter("a,b") == ","

    rendered = render_rows_tsv(
        fieldnames=("sample_id", "replicate", "intensity", "accepted"),
        rows=(
            {
                "sample_id": "s1",
                "replicate": 1,
                "intensity": 12.5,
                "accepted": True,
            },
            {
                "sample_id": "s2",
                "replicate": 2,
                "intensity": None,
                "accepted": False,
            },
        ),
    )

    assert rendered == (
        "sample_id\treplicate\tintensity\taccepted\n"
        "s1\t1\t12.5\ttrue\n"
        "s2\t2\t\tfalse\n"
    )
    assert render_tsv_rows(
        fieldnames=("sample_id", "replicate", "intensity", "accepted"),
        rows=(
            {
                "sample_id": "s1",
                "replicate": 1,
                "intensity": 12.5,
                "accepted": True,
            },
            {
                "sample_id": "s2",
                "replicate": 2,
                "intensity": None,
                "accepted": False,
            },
        ),
    ) == rendered
