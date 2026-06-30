# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Shared TSV export support for cross-study workflow reports."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics._output_tables import write_output_table_tsv


def export_tsv_table(path: Path, content: str) -> None:
    """Write one rendered TSV table to its governed output path."""
    write_output_table_tsv(path, content)


def format_optional_float(value: float | None) -> str:
    """Render optional floating-point values for stable TSV output."""
    return "" if value is None else f"{value:.6g}"


__all__ = ["export_tsv_table", "format_optional_float"]
