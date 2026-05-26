# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Streaming lookup joins for governed TSV and CSV artifact tables."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator, Sequence
import csv
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics._tabular import infer_delimited_table_delimiter


@dataclass(frozen=True)
class DelimitedLookupJoinSpec:
    """One lookup table joined onto a streamed primary row set."""

    join_name: str
    path: Path
    primary_key_columns: tuple[str, ...]
    lookup_key_columns: tuple[str, ...]
    required_lookup_columns: tuple[str, ...] = ()
    delimiter: str | None = None


@dataclass(frozen=True)
class DelimitedLookupJoinRow:
    """One streamed primary row plus grouped lookup matches."""

    row_number: int
    primary_row: dict[str, str]
    joined_rows: dict[str, tuple[dict[str, str], ...]]


def iter_delimited_rows(
    path: Path,
    *,
    required_columns: Sequence[str] = (),
    delimiter: str | None = None,
) -> Iterator[tuple[int, dict[str, str]]]:
    """Yield normalized rows from one delimited table without materializing all rows."""

    with path.open("r", encoding="utf-8", newline="") as handle:
        header_line = handle.readline()
        active_delimiter = delimiter or infer_delimited_table_delimiter(header_line)
        handle.seek(0)
        reader = csv.DictReader(handle, delimiter=active_delimiter)
        header = tuple((field or "").strip() for field in reader.fieldnames or ())
        if not header:
            raise ValueError(f"{path.name!r} must include a header row")
        _validate_required_columns(
            header,
            required_columns=tuple(required_columns),
            description=path.name,
        )
        for row_number, raw_row in enumerate(reader, start=2):
            yield row_number, _normalize_delimited_row(raw_row)


def iter_streaming_lookup_join(
    primary_path: Path,
    *,
    lookup_specs: Sequence[DelimitedLookupJoinSpec],
    required_primary_columns: Sequence[str] = (),
    delimiter: str | None = None,
) -> Iterator[DelimitedLookupJoinRow]:
    """Stream one primary table while joining smaller lookup tables by indexed keys."""

    active_specs = tuple(lookup_specs)
    primary_columns = set(required_primary_columns)
    for spec in active_specs:
        primary_columns.update(spec.primary_key_columns)
    lookup_indexes = {
        spec.join_name: _build_lookup_index(spec) for spec in active_specs
    }
    for row_number, primary_row in iter_delimited_rows(
        primary_path,
        required_columns=tuple(primary_columns),
        delimiter=delimiter,
    ):
        joined_rows: dict[str, tuple[dict[str, str], ...]] = {}
        for spec in active_specs:
            primary_key = _row_key(primary_row, spec.primary_key_columns)
            joined_rows[spec.join_name] = lookup_indexes[spec.join_name].get(
                primary_key,
                (),
            )
        yield DelimitedLookupJoinRow(
            row_number=row_number,
            primary_row=primary_row,
            joined_rows=joined_rows,
        )


def _build_lookup_index(
    spec: DelimitedLookupJoinSpec,
) -> dict[tuple[str, ...], tuple[dict[str, str], ...]]:
    grouped_rows: defaultdict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    required_columns = tuple(
        dict.fromkeys((*spec.lookup_key_columns, *spec.required_lookup_columns))
    )
    for _, row in iter_delimited_rows(
        spec.path,
        required_columns=required_columns,
        delimiter=spec.delimiter,
    ):
        grouped_rows[_row_key(row, spec.lookup_key_columns)].append(row)
    return {
        key: tuple(rows)
        for key, rows in grouped_rows.items()
    }


def _normalize_delimited_row(raw_row: dict[str | None, str | None]) -> dict[str, str]:
    return {
        str(key).strip(): str(value or "").strip()
        for key, value in raw_row.items()
        if key is not None
    }


def _validate_required_columns(
    header: tuple[str, ...],
    *,
    required_columns: tuple[str, ...],
    description: str,
) -> None:
    missing_columns = tuple(
        column for column in required_columns if column not in header
    )
    if missing_columns:
        raise ValueError(
            f"{description!r} is missing required columns: {', '.join(missing_columns)}"
        )


def _row_key(row: dict[str, str], columns: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(row.get(column, "").strip() for column in columns)


__all__ = [
    "DelimitedLookupJoinRow",
    "DelimitedLookupJoinSpec",
    "iter_delimited_rows",
    "iter_streaming_lookup_join",
]
