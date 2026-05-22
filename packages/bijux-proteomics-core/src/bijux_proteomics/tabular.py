# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Low-dependency delimited-table parsing and stable TSV rendering."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
import csv
from io import StringIO
import math
from pathlib import Path

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics_foundation import JsonModel


class DelimitedColumnValueType(str):
    """Backwards-stable value kinds for shared delimited-table parsing."""

    TEXT = "text"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"


class DelimitedColumnSpec(JsonModel):
    """One canonical column definition for a delimited scientific table."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1)
    source_columns: tuple[str, ...] = Field(default_factory=tuple)
    required: bool = False
    value_type: str = Field(default=DelimitedColumnValueType.TEXT, min_length=1)
    missing_tokens: tuple[str, ...] = Field(
        default=("", "na", "n/a", "null", "none", "nan")
    )
    true_tokens: tuple[str, ...] = Field(default=("true", "1", "yes", "y"))
    false_tokens: tuple[str, ...] = Field(default=("false", "0", "no", "n"))

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, value: object) -> str:
        text = str(value).strip()
        if not text:
            raise ValueError("column name must not be blank")
        return text

    @field_validator("source_columns", mode="before")
    @classmethod
    def _normalize_source_columns(cls, value: object) -> tuple[str, ...]:
        if value in (None, ""):
            return ()
        if isinstance(value, str):
            candidates = (value,)
        else:
            if not isinstance(value, Iterable):
                raise ValueError("source_columns must be iterable")
            candidates = tuple(str(item) for item in value)
        normalized = tuple(item.strip() for item in candidates if item.strip())
        return tuple(dict.fromkeys(normalized))

    @field_validator("missing_tokens", "true_tokens", "false_tokens", mode="before")
    @classmethod
    def _normalize_tokens(cls, value: object) -> tuple[str, ...]:
        if value in (None, ""):
            return ()
        if isinstance(value, str):
            items = (value,)
        else:
            if not isinstance(value, Iterable):
                raise ValueError("token sets must be iterable")
            items = tuple(str(item) for item in value)
        normalized = tuple(item.strip().lower() for item in items if item.strip())
        return tuple(dict.fromkeys(normalized))

    @field_validator("value_type")
    @classmethod
    def _validate_value_type(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {
            DelimitedColumnValueType.TEXT,
            DelimitedColumnValueType.INTEGER,
            DelimitedColumnValueType.FLOAT,
            DelimitedColumnValueType.BOOLEAN,
        }:
            raise ValueError(f"unsupported value_type {value!r}")
        return normalized

    def all_source_columns(self) -> tuple[str, ...]:
        """Return the canonical column name plus any accepted aliases."""

        return (self.name, *self.source_columns)


class DelimitedTableIssue(JsonModel):
    """One header-level or row-level issue from shared table parsing."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    row_number: int = Field(..., ge=1)
    column: str | None = None


class RejectedDelimitedRow(JsonModel):
    """One rejected row plus explicit issue set."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=1)
    raw_values: dict[str, str] = Field(default_factory=dict)
    issues: tuple[DelimitedTableIssue, ...] = Field(default_factory=tuple)


class AcceptedDelimitedRow(JsonModel):
    """One accepted row with canonical values and preserved unmapped extras."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=1)
    values: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    extra_values: dict[str, str] = Field(default_factory=dict)
    raw_values: dict[str, str] = Field(default_factory=dict)


class DelimitedTableParseReport(JsonModel):
    """Stable parse report for one TSV or CSV table."""

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(..., min_length=1)
    delimiter: str = Field(..., min_length=1, max_length=1)
    header: tuple[str, ...] = Field(default_factory=tuple)
    accepted_rows: tuple[AcceptedDelimitedRow, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[RejectedDelimitedRow, ...] = Field(default_factory=tuple)


def infer_delimited_table_delimiter(header_line: str) -> str:
    """Infer TSV when tabs are present, otherwise fall back to CSV."""

    return "\t" if "\t" in header_line else ","


def parse_delimited_table(
    path: Path,
    *,
    column_specs: Sequence[DelimitedColumnSpec] = (),
    required_columns: Sequence[str] = (),
    delimiter: str | None = None,
) -> DelimitedTableParseReport:
    """Parse one delimited table with optional shared schema and row rejection."""

    raw_text = path.read_text(encoding="utf-8")
    lines = raw_text.splitlines()
    active_delimiter = (
        delimiter or infer_delimited_table_delimiter(lines[0]) if lines else "\t"
    )
    if not lines:
        return DelimitedTableParseReport(
            source_path=str(path),
            delimiter=active_delimiter,
            rejected_rows=(
                RejectedDelimitedRow(
                    row_number=1,
                    issues=(
                        DelimitedTableIssue(
                            code="empty_table",
                            message="table is empty",
                            row_number=1,
                        ),
                    ),
                ),
            ),
        )

    reader = csv.DictReader(lines, delimiter=active_delimiter)
    raw_header = tuple((field or "").strip() for field in reader.fieldnames or ())
    if not raw_header:
        return DelimitedTableParseReport(
            source_path=str(path),
            delimiter=active_delimiter,
            rejected_rows=(
                RejectedDelimitedRow(
                    row_number=1,
                    issues=(
                        DelimitedTableIssue(
                            code="missing_header",
                            message="table is missing a header row",
                            row_number=1,
                        ),
                    ),
                ),
            ),
        )

    rejected_rows: list[RejectedDelimitedRow] = []
    accepted_rows: list[AcceptedDelimitedRow] = []
    header_issues = _header_issues(
        header=raw_header,
        column_specs=tuple(column_specs),
        required_columns=tuple(required_columns),
    )
    if header_issues:
        return DelimitedTableParseReport(
            source_path=str(path),
            delimiter=active_delimiter,
            header=raw_header,
            rejected_rows=(
                RejectedDelimitedRow(
                    row_number=1,
                    issues=header_issues,
                ),
            ),
        )

    resolved_columns = _resolve_columns(raw_header, tuple(column_specs))
    for row_number, raw_row in enumerate(reader, start=2):
        normalized_row = {
            (key or "").strip(): (value or "").strip()
            for key, value in raw_row.items()
            if key is not None
        }
        if not column_specs:
            accepted_rows.append(
                AcceptedDelimitedRow(
                    row_number=row_number,
                    values=dict(normalized_row),
                    extra_values={},
                    raw_values=normalized_row,
                )
            )
            continue

        values: dict[str, str | int | float | bool | None] = {}
        issues: list[DelimitedTableIssue] = []
        used_columns: set[str] = set()
        for spec in column_specs:
            source_column = resolved_columns.get(spec.name)
            if source_column is not None:
                used_columns.add(source_column)
            raw_value = normalized_row.get(source_column, "") if source_column else ""
            try:
                values[spec.name] = _coerce_delimited_value(
                    raw_value,
                    spec=spec,
                    row_number=row_number,
                )
            except ValueError as exc:
                issues.append(
                    DelimitedTableIssue(
                        code=_issue_code_for_spec(spec, raw_value),
                        message=str(exc),
                        row_number=row_number,
                        column=spec.name,
                    )
                )
        if issues:
            rejected_rows.append(
                RejectedDelimitedRow(
                    row_number=row_number,
                    raw_values=normalized_row,
                    issues=tuple(issues),
                )
            )
            continue

        accepted_rows.append(
            AcceptedDelimitedRow(
                row_number=row_number,
                values=values,
                extra_values={
                    key: value
                    for key, value in normalized_row.items()
                    if key not in used_columns and value
                },
                raw_values=normalized_row,
            )
        )

    return DelimitedTableParseReport(
        source_path=str(path),
        delimiter=active_delimiter,
        header=raw_header,
        accepted_rows=tuple(accepted_rows),
        rejected_rows=tuple(rejected_rows),
    )


def render_tsv_rows(
    *,
    fieldnames: Sequence[str],
    rows: Sequence[Mapping[str, object | None]],
) -> str:
    """Render stable TSV output with explicit header order and newline policy."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(list(fieldnames))
    for row in rows:
        writer.writerow([_format_tsv_value(row.get(field)) for field in fieldnames])
    return buffer.getvalue()


def _header_issues(
    *,
    header: tuple[str, ...],
    column_specs: tuple[DelimitedColumnSpec, ...],
    required_columns: tuple[str, ...],
) -> tuple[DelimitedTableIssue, ...]:
    header_set = set(header)
    issues: list[DelimitedTableIssue] = []
    for column in sorted(set(required_columns)):
        if column not in header_set:
            issues.append(
                DelimitedTableIssue(
                    code="missing_required_column",
                    message=f"table is missing required column {column!r}",
                    row_number=1,
                    column=column,
                )
            )
    for spec in column_specs:
        if spec.required and _find_source_column(header, spec) is None:
            issues.append(
                DelimitedTableIssue(
                    code="missing_required_column",
                    message=f"table is missing required column {spec.name!r}",
                    row_number=1,
                    column=spec.name,
                )
            )
    return tuple(issues)


def _resolve_columns(
    header: tuple[str, ...],
    specs: tuple[DelimitedColumnSpec, ...],
) -> dict[str, str | None]:
    return {spec.name: _find_source_column(header, spec) for spec in specs}


def _find_source_column(
    header: tuple[str, ...],
    spec: DelimitedColumnSpec,
) -> str | None:
    for candidate in spec.all_source_columns():
        if candidate in header:
            return candidate
    return None


def _coerce_delimited_value(
    raw_value: str,
    *,
    spec: DelimitedColumnSpec,
    row_number: int,
) -> str | int | float | bool | None:
    normalized_value = raw_value.strip()
    if normalized_value.lower() in spec.missing_tokens:
        if spec.required:
            raise ValueError(f"row is missing required value for {spec.name!r}")
        return None
    if spec.value_type == DelimitedColumnValueType.TEXT:
        return normalized_value
    if spec.value_type == DelimitedColumnValueType.INTEGER:
        try:
            return int(normalized_value)
        except ValueError as exc:
            raise ValueError(f"row has invalid integer value for {spec.name!r}") from exc
    if spec.value_type == DelimitedColumnValueType.FLOAT:
        try:
            return float(normalized_value)
        except ValueError as exc:
            raise ValueError(f"row has invalid float value for {spec.name!r}") from exc
    if spec.value_type == DelimitedColumnValueType.BOOLEAN:
        lowered = normalized_value.lower()
        if lowered in spec.true_tokens:
            return True
        if lowered in spec.false_tokens:
            return False
        raise ValueError(f"row has invalid boolean value for {spec.name!r}")
    raise ValueError(
        f"unsupported column value type {spec.value_type!r} at row {row_number}"
    )


def _issue_code_for_spec(spec: DelimitedColumnSpec, raw_value: str) -> str:
    if raw_value.strip().lower() in spec.missing_tokens:
        return "missing_required_value"
    if spec.value_type == DelimitedColumnValueType.INTEGER:
        return "invalid_integer_value"
    if spec.value_type == DelimitedColumnValueType.FLOAT:
        return "invalid_float_value"
    if spec.value_type == DelimitedColumnValueType.BOOLEAN:
        return "invalid_boolean_value"
    return "invalid_value"


def _format_tsv_value(value: object | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        if not math.isfinite(value):
            return str(value)
        return f"{value:g}"
    return str(value)
