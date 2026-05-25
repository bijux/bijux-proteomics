# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical XIC target-table parsing owners."""

from __future__ import annotations

from pathlib import Path

from pydantic import ConfigDict, Field, ValidationError, field_validator, model_validator

from bijux_proteomics._tabular import (
    DelimitedColumnSpec,
    DelimitedTableIssue,
    parse_delimited_table,
)
from bijux_proteomics_foundation import JsonModel


class XicTargetEntry(JsonModel):
    """One precursor target to extract from mzML spectra."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    precursor_mz: float = Field(..., gt=0.0)
    rt_expected_seconds: float | None = Field(default=None, ge=0.0)
    rt_start_seconds: float | None = Field(default=None, ge=0.0)
    rt_end_seconds: float | None = Field(default=None, ge=0.0)
    expected_charge: int | None = Field(default=None, ge=1)
    display_name: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("target_id", "display_name", mode="before")
    @classmethod
    def _strip_text(cls, value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @model_validator(mode="after")
    def _validate_retention_window(self) -> XicTargetEntry:
        if (
            self.rt_start_seconds is not None
            and self.rt_end_seconds is not None
            and self.rt_start_seconds > self.rt_end_seconds
        ):
            raise ValueError("rt_start_seconds cannot exceed rt_end_seconds")
        return self


class XicTargetRejectedRow(JsonModel):
    """One rejected XIC target row with explicit stable reason."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=1)
    values: dict[str, str] = Field(default_factory=dict)
    reason: str = Field(..., min_length=1)


class XicTargetParseReport(JsonModel):
    """Stable parse report for one XIC target precursor table."""

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(..., min_length=1)
    accepted_entries: tuple[XicTargetEntry, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[XicTargetRejectedRow, ...] = Field(default_factory=tuple)


def parse_xic_target_table(path: Path) -> XicTargetParseReport:
    """Parse one precursor-target table for mzML XIC extraction."""

    table_report = parse_delimited_table(
        path,
        column_specs=(
            DelimitedColumnSpec(name="target_id", source_columns=("id",)),
            DelimitedColumnSpec(name="precursor_mz", source_columns=("mz", "q1")),
            DelimitedColumnSpec(name="rt_expected_seconds", source_columns=("rt_expected",)),
            DelimitedColumnSpec(
                name="rt_start_seconds",
                source_columns=("rt_start", "rt_window_start"),
            ),
            DelimitedColumnSpec(
                name="rt_end_seconds",
                source_columns=("rt_end", "rt_window_end"),
            ),
            DelimitedColumnSpec(
                name="expected_charge",
                source_columns=("charge", "precursor_charge"),
            ),
            DelimitedColumnSpec(name="display_name", source_columns=("name",)),
        ),
    )
    accepted_entries: list[XicTargetEntry] = []
    rejected_rows = [
        XicTargetRejectedRow(
            row_number=row.row_number,
            values=row.raw_values,
            reason=_stable_reason_from_issues(row.issues),
        )
        for row in table_report.rejected_rows
    ]
    fieldnames = set(table_report.header)
    seen_target_ids: set[str] = set()
    for accepted_row in table_report.accepted_rows:
        normalized_row = _render_table_row_values(accepted_row.values, accepted_row.extra_values)
        try:
            entry = _parse_xic_target_row(normalized_row, fieldnames)
            if entry.target_id in seen_target_ids:
                raise ValueError(f"duplicate target_id {entry.target_id!r}")
            seen_target_ids.add(entry.target_id)
            accepted_entries.append(entry)
        except (ValueError, ValidationError) as exc:
            rejected_rows.append(
                XicTargetRejectedRow(
                    row_number=accepted_row.row_number,
                    values=normalized_row,
                    reason=_stable_reason(exc),
                )
            )
    return XicTargetParseReport(
        source_path=str(path),
        accepted_entries=tuple(accepted_entries),
        rejected_rows=tuple(rejected_rows),
    )


def coerce_xic_target_report(
    targets: Path | XicTargetParseReport | tuple[XicTargetEntry, ...],
) -> XicTargetParseReport:
    """Coerce in-memory or file-backed targets into one typed target report."""

    if isinstance(targets, Path):
        return parse_xic_target_table(targets)
    if isinstance(targets, XicTargetParseReport):
        return targets
    return XicTargetParseReport(
        source_path="<in-memory>",
        accepted_entries=targets,
        rejected_rows=(),
    )


def _parse_xic_target_row(
    row: dict[str, str],
    fieldnames: set[str],
) -> XicTargetEntry:
    target_id = row.get("target_id") or row.get("id") or None
    precursor_mz = row.get("precursor_mz") or row.get("mz") or row.get("q1") or None
    if target_id is None:
        raise ValueError("target row requires target_id")
    if precursor_mz is None:
        raise ValueError("target row requires precursor_mz")
    metadata = {
        key: value
        for key, value in row.items()
        if key in fieldnames
        and key
        not in {
            "target_id",
            "id",
            "precursor_mz",
            "mz",
            "q1",
            "rt_expected_seconds",
            "rt_expected",
            "rt_start_seconds",
            "rt_start",
            "rt_window_start",
            "rt_end_seconds",
            "rt_end",
            "rt_window_end",
            "expected_charge",
            "charge",
            "precursor_charge",
            "display_name",
            "name",
        }
        and value
    }
    return XicTargetEntry(
        target_id=target_id,
        precursor_mz=float(precursor_mz),
        rt_expected_seconds=_optional_float(
            row.get("rt_expected_seconds") or row.get("rt_expected")
        ),
        rt_start_seconds=_optional_float(
            row.get("rt_start_seconds") or row.get("rt_start") or row.get("rt_window_start")
        ),
        rt_end_seconds=_optional_float(
            row.get("rt_end_seconds") or row.get("rt_end") or row.get("rt_window_end")
        ),
        expected_charge=_optional_int(
            row.get("expected_charge") or row.get("charge") or row.get("precursor_charge")
        ),
        display_name=row.get("display_name") or row.get("name") or None,
        metadata=metadata,
    )


def _optional_float(value: str | None) -> float | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    return float(stripped)


def _optional_int(value: str | None) -> int | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    return int(stripped)


def _stable_reason(error: ValueError | ValidationError) -> str:
    if isinstance(error, ValidationError):
        issues = error.errors()
        if issues:
            message = issues[0].get("msg")
            if isinstance(message, str):
                return message.removeprefix("Value error, ")
    return str(error)


def _stable_reason_from_issues(issues: tuple[DelimitedTableIssue, ...]) -> str:
    if not issues:
        return "xic target row was rejected"
    if any(issue.code == "empty_table" for issue in issues):
        return "xic target table is empty"
    return issues[0].message


def _render_table_row_values(
    values: dict[str, str | int | float | bool | None],
    extra_values: dict[str, str],
) -> dict[str, str]:
    rendered: dict[str, str] = dict(extra_values)
    for key, value in values.items():
        rendered[key] = "" if value is None else str(value)
    return rendered
