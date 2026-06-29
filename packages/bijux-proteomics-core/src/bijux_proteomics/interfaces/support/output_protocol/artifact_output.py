# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Artifact output helpers for text, TSV, and JSON payloads."""

from __future__ import annotations

from bijux_proteomics._atomic_files import atomic_write_text
from bijux_proteomics._output_tables import write_output_table_tsv

from ..foundation import Any, Path, click, json


def _emit_json(payload: Any, *, out_path: Path | None = None) -> None:
    if hasattr(payload, "to_stable_json"):
        rendered = payload.to_stable_json()
    else:
        rendered = json.dumps(payload, indent=2, sort_keys=True)
    if out_path is not None:
        atomic_write_text(out_path, rendered + "\n")
    click.echo(rendered)


def _write_text_output(path: Path, text: str) -> None:
    if path.suffix.lower() == ".tsv":
        write_output_table_tsv(path, text)
        return
    atomic_write_text(path, text)


def _read_identifier_lines(path: Path | None) -> tuple[str, ...]:
    if path is None:
        return ()
    return tuple(
        line
        for raw_line in path.read_text(encoding="utf-8").splitlines()
        if (line := raw_line.strip()) and not line.startswith("#")
    )
