# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Chunked delimited-row iteration for large governed workflow inputs."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from typing import Iterator


@dataclass(frozen=True)
class DelimitedTableHeader:
    """Resolved header metadata for one governed delimited table."""

    fieldnames: tuple[str, ...]
    delimiter: str


@dataclass(frozen=True)
class DelimitedRowChunk:
    """One stable chunk of delimited rows with source-row numbering."""

    fieldnames: tuple[str, ...]
    row_number_start: int
    rows: tuple[dict[str, str], ...]


def read_delimited_table_header(path: Path) -> DelimitedTableHeader | None:
    """Read one delimited-table header without materializing data rows."""

    with path.open("r", encoding="utf-8", newline="") as handle:
        first_line = handle.readline()
    if not first_line:
        return None
    delimiter = "\t" if "\t" in first_line else ","
    reader = csv.DictReader([first_line], delimiter=delimiter)
    if reader.fieldnames is None:
        return None
    return DelimitedTableHeader(
        fieldnames=tuple(str(fieldname) for fieldname in reader.fieldnames),
        delimiter=delimiter,
    )


def iter_delimited_row_chunks(
    path: Path,
    *,
    chunk_size_rows: int,
) -> Iterator[DelimitedRowChunk]:
    """Yield stable row chunks from one delimited table."""

    if chunk_size_rows < 1:
        raise ValueError("chunk_size_rows must be at least 1")

    with path.open("r", encoding="utf-8", newline="") as handle:
        first_line = handle.readline()
        if not first_line:
            return
        delimiter = "\t" if "\t" in first_line else ","
        reader = csv.DictReader(chain([first_line], handle), delimiter=delimiter)
        if reader.fieldnames is None:
            raise ValueError("delimited table must include a header row")
        fieldnames = tuple(str(fieldname) for fieldname in reader.fieldnames)
        chunk_rows: list[dict[str, str]] = []
        chunk_start_row = 2
        next_row_number = 2
        for row in reader:
            normalized_row = {
                str(key): str(value or "")
                for key, value in row.items()
                if key is not None
            }
            chunk_rows.append(normalized_row)
            if len(chunk_rows) == chunk_size_rows:
                yield DelimitedRowChunk(
                    fieldnames=fieldnames,
                    row_number_start=chunk_start_row,
                    rows=tuple(chunk_rows),
                )
                next_row_number += len(chunk_rows)
                chunk_rows = []
                chunk_start_row = next_row_number
        if chunk_rows:
            yield DelimitedRowChunk(
                fieldnames=fieldnames,
                row_number_start=chunk_start_row,
                rows=tuple(chunk_rows),
            )


__all__ = [
    "DelimitedRowChunk",
    "DelimitedTableHeader",
    "iter_delimited_row_chunks",
    "read_delimited_table_header",
]
