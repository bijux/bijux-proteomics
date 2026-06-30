# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Selected-peptide support aggregation for biomarker candidate ranking."""

from __future__ import annotations

import csv
from pathlib import Path

import click


def _load_selected_peptide_support_by_protein(
    path: Path,
) -> dict[str, dict[str, float]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "selected-peptide TSV must include a header row for biomarker candidate ranking"
            )
        required_columns = {
            "target_protein_ref",
            "detectability_score",
            "uniqueness_score",
            "suitability_score",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "selected-peptide TSV is missing required columns for biomarker candidate ranking: "
                + ", ".join(sorted(missing_columns))
            )
        support_by_protein: dict[str, dict[str, float]] = {}
        for row_number, row in enumerate(reader, start=2):
            try:
                protein_ref = str(row.get("target_protein_ref", "")).strip()
                support = support_by_protein.setdefault(
                    protein_ref,
                    {
                        "detectability_score": 0.0,
                        "uniqueness_score": 0.0,
                        "suitability_score": 0.0,
                    },
                )
                support["detectability_score"] = max(
                    support["detectability_score"],
                    float(str(row.get("detectability_score", "")).strip()),
                )
                support["uniqueness_score"] = max(
                    support["uniqueness_score"],
                    float(str(row.get("uniqueness_score", "")).strip()),
                )
                support["suitability_score"] = max(
                    support["suitability_score"],
                    float(str(row.get("suitability_score", "")).strip()),
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid selected-peptide row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return support_by_protein


__all__ = ("_load_selected_peptide_support_by_protein",)
