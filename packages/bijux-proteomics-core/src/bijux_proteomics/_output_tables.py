# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Schema-backed validation for TSV output tables before they are written."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import csv
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics._tabular import DelimitedColumnValueType
from bijux_proteomics_foundation import JsonModel


class OutputTableColumnSchema(JsonModel):
    """One stable output-table column definition."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1)
    value_type: str = Field(..., min_length=1)
    required: bool = True
    meaning: str = Field(..., min_length=1)


class OutputTableSchema(JsonModel):
    """One durable schema object for one TSV output table."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "2026-05-26"
    table_name: str = Field(..., min_length=1)
    table_meaning: str = Field(..., min_length=1)
    columns: tuple[OutputTableColumnSchema, ...] = Field(default_factory=tuple)


class OutputTableValidationIssue(JsonModel):
    """One validation issue over a rendered TSV output table."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    row_number: int = Field(..., ge=1)
    column: str | None = None


class OutputTableValidationReport(JsonModel):
    """Validation result for one rendered TSV output table."""

    model_config = ConfigDict(extra="forbid")

    table_name: str = Field(..., min_length=1)
    table_schema: OutputTableSchema
    issues: tuple[OutputTableValidationIssue, ...] = Field(default_factory=tuple)

    @property
    def valid(self) -> bool:
        return not self.issues


class OutputTableValidationError(ValueError):
    """Structured exception raised when one TSV output table fails validation."""

    def __init__(self, report: OutputTableValidationReport) -> None:
        self.report = report
        first_issue = report.issues[0] if report.issues else None
        message = (
            f"{report.table_name} output-table validation failed"
            if first_issue is None
            else (
                f"{report.table_name} output-table validation failed: "
                f"{first_issue.message}"
            )
        )
        super().__init__(message)


def infer_output_table_schema(
    text: str,
    *,
    table_name: str,
    table_meaning: str | None = None,
    column_meanings: Mapping[str, str] | None = None,
) -> OutputTableSchema:
    """Infer one stable TSV output-table schema from rendered text."""

    rows = _read_tsv_rows(text)
    header = _header_from_rows(rows)
    meanings = dict(column_meanings or {})
    return OutputTableSchema(
        table_name=table_name,
        table_meaning=table_meaning or _default_table_meaning(table_name),
        columns=tuple(
            OutputTableColumnSchema(
                name=column_name,
                value_type=_infer_column_value_type(rows, column_index=index),
                required=True,
                meaning=meanings.get(
                    column_name,
                    _default_column_meaning(table_name, column_name),
                ),
            )
            for index, column_name in enumerate(header)
        ),
    )


def validate_output_table_text(
    text: str,
    *,
    schema: OutputTableSchema,
) -> OutputTableValidationReport:
    """Validate one rendered TSV output table against one schema object."""

    rows = _read_tsv_rows(text)
    issues: list[OutputTableValidationIssue] = []
    header = _header_from_rows(rows)
    expected_header = tuple(column.name for column in schema.columns)
    if header != expected_header:
        issues.append(
            OutputTableValidationIssue(
                code="header_mismatch",
                message=(
                    f"output table header does not match schema for {schema.table_name!r}"
                ),
                row_number=1,
            )
        )
        return OutputTableValidationReport(
            table_name=schema.table_name,
            table_schema=schema,
            issues=tuple(issues),
        )
    for row_number, row in enumerate(rows[1:], start=2):
        if len(row) != len(expected_header):
            issues.append(
                OutputTableValidationIssue(
                    code="column_count_mismatch",
                    message=(
                        f"row {row_number} has {len(row)} columns but "
                        f"{len(expected_header)} were expected"
                    ),
                    row_number=row_number,
                )
            )
            continue
        for column, value in zip(schema.columns, row, strict=True):
            if not _value_matches_type(value, column.value_type):
                issues.append(
                    OutputTableValidationIssue(
                        code="invalid_column_value",
                        message=(
                            f"row {row_number} has invalid {column.value_type} value "
                            f"for {column.name!r}"
                        ),
                        row_number=row_number,
                        column=column.name,
                    )
                )
    return OutputTableValidationReport(
        table_name=schema.table_name,
        table_schema=schema,
        issues=tuple(issues),
    )


def write_output_table_tsv(
    path: Path,
    text: str,
    *,
    table_name: str | None = None,
    table_meaning: str | None = None,
    column_meanings: Mapping[str, str] | None = None,
) -> OutputTableSchema:
    """Validate one TSV output table and write it only when it matches its schema."""

    active_table_name = table_name or path.stem
    schema = infer_output_table_schema(
        text,
        table_name=active_table_name,
        table_meaning=table_meaning,
        column_meanings=column_meanings,
    )
    report = validate_output_table_text(text, schema=schema)
    if not report.valid:
        raise OutputTableValidationError(report)
    path.write_text(text, encoding="utf-8")
    return schema


def _read_tsv_rows(text: str) -> tuple[tuple[str, ...], ...]:
    if not text:
        raise ValueError("output table text must not be empty")
    rows = tuple(tuple(row) for row in csv.reader(StringIO(text), delimiter="\t"))
    if not rows or not rows[0]:
        raise ValueError("output table must contain a header row")
    return rows


def _header_from_rows(rows: Sequence[Sequence[str]]) -> tuple[str, ...]:
    header = tuple(column.strip() for column in rows[0])
    if any(not column for column in header):
        raise ValueError("output table header must not contain blank column names")
    if len(header) != len(set(header)):
        raise ValueError("output table header must not contain duplicate column names")
    return header


def _infer_column_value_type(
    rows: Sequence[Sequence[str]],
    *,
    column_index: int,
) -> str:
    observed_values = [
        row[column_index].strip()
        for row in rows[1:]
        if column_index < len(row) and row[column_index].strip()
    ]
    if not observed_values:
        return DelimitedColumnValueType.TEXT
    if all(value.lower() in {"true", "false"} for value in observed_values):
        return DelimitedColumnValueType.BOOLEAN
    if all(_is_int(value) for value in observed_values):
        return DelimitedColumnValueType.INTEGER
    if all(_is_float(value) for value in observed_values):
        return DelimitedColumnValueType.FLOAT
    return DelimitedColumnValueType.TEXT


def _value_matches_type(value: str, value_type: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return True
    if value_type == DelimitedColumnValueType.TEXT:
        return True
    if value_type == DelimitedColumnValueType.BOOLEAN:
        return stripped.lower() in {"true", "false"}
    if value_type == DelimitedColumnValueType.INTEGER:
        return _is_int(stripped)
    if value_type == DelimitedColumnValueType.FLOAT:
        return _is_float(stripped)
    return False


def _default_table_meaning(table_name: str) -> str:
    return f"Stable TSV output for {table_name.replace('_', ' ')}."


def _default_column_meaning(table_name: str, column_name: str) -> str:
    return (
        f"Stable column {column_name!r} in TSV output {table_name!r}."
    )


def _is_int(value: str) -> bool:
    try:
        int(value)
    except ValueError:
        return False
    return True


def _is_float(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True


__all__ = [
    "OutputTableColumnSchema",
    "OutputTableSchema",
    "OutputTableValidationError",
    "OutputTableValidationIssue",
    "OutputTableValidationReport",
    "infer_output_table_schema",
    "validate_output_table_text",
    "write_output_table_tsv",
]
