# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Streaming integrity checks for tabular proteomics inputs."""

from __future__ import annotations

import csv
from pathlib import Path
import re

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


_DELIMITER_CANDIDATES: tuple[str, ...] = ("\t", ",", ";", "|")
_NUMERIC_COLUMN_PATTERN = re.compile(
    r"(?:^|_)(?:intensity|abundance|quantity|amount|score|probability|"
    r"q_value|p_value|mz|mass|charge|rt|retention|area|ratio|fold|fc|"
    r"count|position|coverage|ppm|entropy|variance)(?:$|_)",
    re.IGNORECASE,
)
_ID_COLUMN_PATTERN = re.compile(r"(^id$|_id$|^id_)", re.IGNORECASE)


class InputIntegrityIssue(JsonModel):
    """One stable input-integrity issue emitted by the streaming scanner."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(..., min_length=1)
    issue_code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    line_number: int | None = Field(default=None, ge=1)
    column_name: str | None = None
    record_id: str | None = None


class InputIntegrityFileReport(JsonModel):
    """Integrity scan summary for one source file."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(..., min_length=1)
    detected_delimiter: str | None = None
    header_fields: tuple[str, ...] = Field(default_factory=tuple)
    scanned_row_count: int = Field(..., ge=0)
    issues: tuple[InputIntegrityIssue, ...] = Field(default_factory=tuple)


class InputIntegrityScanReport(JsonModel):
    """Streaming integrity scan report over one or more source files."""

    model_config = ConfigDict(extra="forbid")

    files: tuple[InputIntegrityFileReport, ...] = Field(default_factory=tuple)
    total_file_count: int = Field(..., ge=0)
    total_issue_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


def scan_input_integrity(paths: tuple[str | Path, ...]) -> InputIntegrityScanReport:
    """Scan tabular inputs for integrity failures without loading whole files."""

    file_reports = tuple(_scan_one_path(Path(raw_path)) for raw_path in paths)
    return InputIntegrityScanReport(
        files=file_reports,
        total_file_count=len(file_reports),
        total_issue_count=sum(len(report.issues) for report in file_reports),
        note=(
            "input integrity scan streams source files row by row to detect encoding, "
            "delimiter, duplicate id, numeric, malformed row, and required-field failures"
        ),
    )


def render_input_integrity_issues_tsv(report: InputIntegrityScanReport) -> str:
    """Render one flat TSV of all integrity issues."""

    rows = [
        {
            "path": issue.path,
            "issue_code": issue.issue_code,
            "line_number": "" if issue.line_number is None else str(issue.line_number),
            "column_name": issue.column_name or "",
            "record_id": issue.record_id or "",
            "message": issue.message,
        }
        for file_report in report.files
        for issue in file_report.issues
    ]
    return _render_tsv(
        rows,
        fieldnames=(
            "path",
            "issue_code",
            "line_number",
            "column_name",
            "record_id",
            "message",
        ),
    )


def _scan_one_path(path: Path) -> InputIntegrityFileReport:
    issues: list[InputIntegrityIssue] = []
    scanned_row_count = 0
    detected_delimiter: str | None = None
    header_fields: tuple[str, ...] = ()

    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            try:
                header_line = handle.readline()
            except UnicodeDecodeError as error:
                issues.append(
                    InputIntegrityIssue(
                        path=str(path),
                        issue_code="broken_encoding",
                        message=f"utf-8 decoding failed near byte offset {error.start}",
                    )
                )
                return InputIntegrityFileReport(
                    path=str(path),
                    detected_delimiter=None,
                    header_fields=(),
                    scanned_row_count=0,
                    issues=tuple(issues),
                )
            if header_line == "":
                issues.append(
                    InputIntegrityIssue(
                        path=str(path),
                        issue_code="empty_file",
                        message="input file is empty",
                    )
                )
                return InputIntegrityFileReport(
                    path=str(path),
                    detected_delimiter=None,
                    header_fields=(),
                    scanned_row_count=0,
                    issues=tuple(issues),
                )

            detected_delimiter = _detect_delimiter(header_line)
            header_fields = tuple(_parse_row(header_line, detected_delimiter))
            if any(field.strip() == "" for field in header_fields):
                issues.append(
                    InputIntegrityIssue(
                        path=str(path),
                        issue_code="malformed_header",
                        message="header contains one or more empty field names",
                        line_number=1,
                    )
                )
            expected_field_count = len(header_fields)
            duplicate_id_columns = tuple(
                field for field in header_fields if _ID_COLUMN_PATTERN.search(field.strip())
            )
            numeric_columns = tuple(
                field for field in header_fields if _NUMERIC_COLUMN_PATTERN.search(field.strip())
            )
            seen_ids = {field: set() for field in duplicate_id_columns}
            primary_id_column = duplicate_id_columns[0] if duplicate_id_columns else None

            line_number = 1
            while True:
                try:
                    raw_line = handle.readline()
                except UnicodeDecodeError as error:
                    issues.append(
                        InputIntegrityIssue(
                            path=str(path),
                            issue_code="broken_encoding",
                            message=f"utf-8 decoding failed near byte offset {error.start}",
                            line_number=line_number + 1,
                        )
                    )
                    break
                if raw_line == "":
                    break
                line_number += 1
                if raw_line.strip() == "":
                    continue
                scanned_row_count += 1
                row = _parse_row(raw_line, detected_delimiter)
                if len(row) != expected_field_count:
                    issues.extend(
                        _row_shape_issues(
                            path=path,
                            raw_line=raw_line,
                            detected_delimiter=detected_delimiter,
                            expected_field_count=expected_field_count,
                            line_number=line_number,
                        )
                    )
                    continue

                record = {
                    header_fields[index].strip(): value.strip()
                    for index, value in enumerate(row)
                }
                record_id = (
                    record.get(primary_id_column, "").strip() if primary_id_column else None
                ) or None
                for column in duplicate_id_columns:
                    value = record[column]
                    if value == "":
                        issues.append(
                            InputIntegrityIssue(
                                path=str(path),
                                issue_code="empty_required_field",
                                message="id column is empty",
                                line_number=line_number,
                                column_name=column,
                                record_id=record_id,
                            )
                        )
                        continue
                    if value in seen_ids[column]:
                        issues.append(
                            InputIntegrityIssue(
                                path=str(path),
                                issue_code="duplicate_id",
                                message=f"duplicate id value {value!r} repeated in column {column!r}",
                                line_number=line_number,
                                column_name=column,
                                record_id=value,
                            )
                        )
                    else:
                        seen_ids[column].add(value)
                for column in numeric_columns:
                    value = record[column]
                    if value == "":
                        continue
                    if not _is_float(value):
                        issues.append(
                            InputIntegrityIssue(
                                path=str(path),
                                issue_code="invalid_numeric_value",
                                message=f"column {column!r} contains non-numeric value {value!r}",
                                line_number=line_number,
                                column_name=column,
                                record_id=record_id,
                            )
                        )
    except FileNotFoundError:
        issues.append(
            InputIntegrityIssue(
                path=str(path),
                issue_code="missing_file",
                message="input path does not exist",
            )
        )

    return InputIntegrityFileReport(
        path=str(path),
        detected_delimiter=detected_delimiter,
        header_fields=header_fields,
        scanned_row_count=scanned_row_count,
        issues=tuple(issues),
    )


def _row_shape_issues(
    *,
    path: Path,
    raw_line: str,
    detected_delimiter: str,
    expected_field_count: int,
    line_number: int,
) -> list[InputIntegrityIssue]:
    issues: list[InputIntegrityIssue] = []
    alternative_delimiter = _alternative_delimiter(
        raw_line=raw_line,
        detected_delimiter=detected_delimiter,
        expected_field_count=expected_field_count,
    )
    if alternative_delimiter is not None:
        issues.append(
            InputIntegrityIssue(
                path=str(path),
                issue_code="inconsistent_delimiter",
                message=(
                    "row appears to use delimiter "
                    f"{alternative_delimiter!r} instead of declared delimiter {detected_delimiter!r}"
                ),
                line_number=line_number,
            )
        )
    issues.append(
        InputIntegrityIssue(
            path=str(path),
            issue_code="malformed_row",
            message=(
                "row field count does not match header field count "
                f"for delimiter {detected_delimiter!r}"
            ),
            line_number=line_number,
        )
    )
    return issues


def _detect_delimiter(header_line: str) -> str:
    counts = {
        delimiter: header_line.count(delimiter)
        for delimiter in _DELIMITER_CANDIDATES
    }
    delimiter, count = max(counts.items(), key=lambda item: item[1])
    if count == 0:
        return "\t"
    return delimiter


def _alternative_delimiter(
    *,
    raw_line: str,
    detected_delimiter: str,
    expected_field_count: int,
) -> str | None:
    for delimiter in _DELIMITER_CANDIDATES:
        if delimiter == detected_delimiter:
            continue
        if len(_parse_row(raw_line, delimiter)) == expected_field_count:
            return delimiter
    return None


def _parse_row(raw_line: str, delimiter: str) -> list[str]:
    return next(csv.reader([raw_line], delimiter=delimiter))


def _is_float(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True


def _render_tsv(
    rows: list[dict[str, str]],
    *,
    fieldnames: tuple[str, ...],
) -> str:
    header = "\t".join(fieldnames)
    if not rows:
        return header + "\n"
    body = [
        "\t".join(row.get(field, "") for field in fieldnames)
        for row in rows
    ]
    return header + "\n" + "\n".join(body) + "\n"
