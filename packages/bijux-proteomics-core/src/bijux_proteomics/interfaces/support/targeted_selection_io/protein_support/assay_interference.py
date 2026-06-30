# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Assay-interference support aggregation for biomarker candidate ranking."""

from __future__ import annotations

import csv
from pathlib import Path

import click

from ..field_parsing import _parse_cli_bool


def _load_assay_interference_support_by_protein(
    path: Path,
) -> dict[str, dict[str, float | bool]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "assay-interference TSV must include a header row for biomarker candidate ranking"
            )
        required_columns = {
            "target_protein_ref",
            "interference_risk_score",
            "panel_export_allowed",
            "exported_transition_count",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "assay-interference TSV is missing required columns for biomarker candidate ranking: "
                + ", ".join(sorted(missing_columns))
            )
        support_by_protein: dict[str, dict[str, float | bool]] = {}
        for row_number, row in enumerate(reader, start=2):
            try:
                protein_ref = str(row.get("target_protein_ref", "")).strip()
                panel_export_allowed = _parse_cli_bool(
                    row.get("panel_export_allowed", ""),
                    field_name="panel_export_allowed",
                )
                risk_score = float(str(row.get("interference_risk_score", "")).strip())
                exported_transition_count = int(
                    str(row.get("exported_transition_count", "")).strip()
                )
                assay_score = max(
                    0.0,
                    (
                        (1.0 - risk_score)
                        * (1.0 if panel_export_allowed else 0.35)
                        * min(1.0, exported_transition_count / 3.0)
                    ),
                )
                current = support_by_protein.get(protein_ref)
                if current is None or assay_score > float(current["assay_score"]):
                    support_by_protein[protein_ref] = {
                        "assay_score": assay_score,
                        "panel_export_allowed": panel_export_allowed,
                        "risk_score": risk_score,
                    }
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid assay-interference row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return support_by_protein


__all__ = ("_load_assay_interference_support_by_protein",)
