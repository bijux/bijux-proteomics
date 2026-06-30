# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Protein-level support loaders for targeted selection workflows."""

from __future__ import annotations

import csv
from pathlib import Path

import click

from ..field_parsing import _parse_cli_bool


def _load_protein_group_map(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("protein group map must include a header row")
        required = {"accession", "protein_group"}
        missing = required.difference(reader.fieldnames)
        if missing:
            missing_columns = ", ".join(sorted(missing))
            raise ValueError(
                "protein group map must include the columns "
                f"'accession' and 'protein_group'; missing: {missing_columns}"
            )
        mapping: dict[str, str] = {}
        for row in reader:
            accession = str(row.get("accession", "")).strip()
            protein_group = str(row.get("protein_group", "")).strip()
            if not accession or not protein_group:
                raise ValueError(
                    "protein group map rows must provide both accession and protein_group"
                )
            mapping[accession] = protein_group
    return mapping


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


__all__ = [
    "_load_assay_interference_support_by_protein",
    "_load_protein_group_map",
    "_load_selected_peptide_support_by_protein",
]
