# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics._output_tables import (
    OutputTableValidationError,
    infer_output_table_schema,
    validate_output_table_text,
    write_output_table_tsv,
)


def test_infer_output_table_schema_tracks_header_types_and_meaning() -> None:
    schema = infer_output_table_schema(
        "protein_ref\tpeptide_count\taccepted\nP11111\t3\ttrue\n",
        table_name="protein_support",
    )

    assert schema.table_name == "protein_support"
    assert schema.table_meaning == "Stable TSV output for protein support."
    assert [column.name for column in schema.columns] == [
        "protein_ref",
        "peptide_count",
        "accepted",
    ]
    assert [column.value_type for column in schema.columns] == [
        "text",
        "integer",
        "boolean",
    ]
    assert all(column.required for column in schema.columns)
    assert "protein_support" in schema.columns[0].meaning


def test_validate_output_table_text_rejects_row_type_drift() -> None:
    schema = infer_output_table_schema(
        "protein_ref\tpeptide_count\nP11111\t3\n",
        table_name="protein_support",
    )

    report = validate_output_table_text(
        "protein_ref\tpeptide_count\nP11111\tnot-an-int\n",
        schema=schema,
    )

    assert report.valid is False
    assert report.issues[0].code == "invalid_column_value"
    assert report.issues[0].column == "peptide_count"


def test_write_output_table_tsv_validates_before_writing(tmp_path: Path) -> None:
    output_path = tmp_path / "protein_support.tsv"

    schema = write_output_table_tsv(
        output_path,
        "protein_ref\tpeptide_count\nP11111\t3\n",
    )

    assert output_path.read_text(encoding="utf-8").startswith("protein_ref\t")
    assert schema.table_name == "protein_support"

    with pytest.raises(OutputTableValidationError):
        write_output_table_tsv(
            output_path,
            "protein_ref\tpeptide_count\nP11111\t3\tunexpected\n",
        )
