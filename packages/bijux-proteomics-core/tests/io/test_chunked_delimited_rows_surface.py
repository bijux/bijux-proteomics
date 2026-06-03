# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.tables import (
    iter_delimited_row_chunks,
    read_delimited_table_header,
)


def test_chunked_delimited_rows_preserve_header_and_source_row_numbers(
    tmp_path: Path,
) -> None:
    table_path = tmp_path / "rows.tsv"
    table_path.write_text(
        "\n".join(
            (
                "sample_id\tpeptide\tintensity",
                "S1\tPEPA\t10",
                "S2\tPEPB\t20",
                "S3\tPEPC\t30",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    header = read_delimited_table_header(table_path)
    assert header is not None
    assert header.fieldnames == ("sample_id", "peptide", "intensity")
    assert header.delimiter == "\t"

    chunks = tuple(iter_delimited_row_chunks(table_path, chunk_size_rows=2))
    assert len(chunks) == 2
    assert chunks[0].row_number_start == 2
    assert chunks[0].rows[0]["sample_id"] == "S1"
    assert chunks[0].rows[1]["sample_id"] == "S2"
    assert chunks[1].row_number_start == 4
    assert chunks[1].rows[0]["sample_id"] == "S3"
