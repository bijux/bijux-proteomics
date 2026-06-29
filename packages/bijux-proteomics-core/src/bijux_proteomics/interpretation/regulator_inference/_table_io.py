# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Delimited-table helpers for regulator evidence and signal input parsing."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path


def read_delimited_lines(path: Path) -> list[str]:
    """Return non-empty logical lines from one delimited text input."""

    return [
        line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def infer_delimiter(header_line: str) -> str:
    """Infer whether one header line is tab- or comma-delimited."""

    return "\t" if header_line.count("\t") >= header_line.count(",") else ","


def validate_required_columns(
    fieldnames: Sequence[str],
    required: tuple[str | None, ...],
) -> None:
    """Validate that one delimited table exposes every required column."""

    missing = [
        field for field in required if field is not None and field not in fieldnames
    ]
    if missing:
        raise ValueError(
            "table is missing required columns: " + ", ".join(sorted(missing))
        )


def normalize_row(row: dict[str, str | None]) -> dict[str, str]:
    """Trim whitespace and drop null header keys from one parsed row."""

    return {key: (value or "").strip() for key, value in row.items() if key is not None}


def optional_value(values: dict[str, str], field: str | None) -> str | None:
    """Return one optional trimmed field value from one normalized row."""

    if field is None:
        return None
    value = values.get(field, "").strip()
    return value or None
