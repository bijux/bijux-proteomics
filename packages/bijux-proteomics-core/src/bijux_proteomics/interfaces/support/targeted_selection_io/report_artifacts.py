# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Artifact path and summary field helpers for report-backed workflows."""

from __future__ import annotations

import csv
from pathlib import Path

import click


def _read_summary_field_map(
    path: Path,
    *,
    description: str,
) -> dict[str, str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(f"{description} must include a header row")
        required_columns = {"field", "value"}
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                f"{description} is missing required columns: "
                + ", ".join(sorted(missing_columns))
            )
        return {
            str(row.get("field", "")).strip(): str(row.get("value", "")).strip()
            for row in reader
        }


def _require_report_artifact(
    report_dir: Path,
    artifact_name: str,
    *,
    description: str,
) -> Path:
    artifact_path = report_dir / artifact_name
    if not artifact_path.exists():
        raise click.ClickException(
            f"{description} is missing required artifact {artifact_name!r}"
        )
    return artifact_path


__all__ = [
    "_read_summary_field_map",
    "_require_report_artifact",
]
