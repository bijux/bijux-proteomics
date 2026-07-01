# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Target protein TSV loading for targeted peptide selection."""

from __future__ import annotations

import csv
from pathlib import Path

import click

from bijux_proteomics.targeted.discovery_peptide_selection import (
    DiscoveryTargetProteinEntry,
)

from ..field_parsing import _split_semicolon_field


def _load_targeted_selection_targets(
    path: Path,
) -> tuple[DiscoveryTargetProteinEntry, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "protein-card TSV must include a header row for targeted peptide selection"
            )
        required_columns = {"protein_group_id", "representative_protein_ref"}
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "protein-card TSV is missing required columns for targeted peptide selection: "
                + ", ".join(sorted(missing_columns))
            )
        targets: list[DiscoveryTargetProteinEntry] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                representative_protein_ref = str(
                    row.get("representative_protein_ref", "")
                ).strip()
                protein_group_id = str(row.get("protein_group_id", "")).strip()
                if not representative_protein_ref or not protein_group_id:
                    raise ValueError(
                        "protein_group_id and representative_protein_ref are required"
                    )
                targets.append(
                    DiscoveryTargetProteinEntry(
                        protein_group_id=protein_group_id,
                        representative_protein_ref=representative_protein_ref,
                        protein_refs=_split_semicolon_field(
                            row.get("protein_refs", "")
                        ),
                        gene_symbol=(
                            gene_symbol
                            if (gene_symbol := str(row.get("gene_symbol", "")).strip())
                            else None
                        ),
                        discovery_peptides=_split_semicolon_field(
                            row.get("peptides", "")
                        ),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid protein-card row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return tuple(targets)


__all__ = ("_load_targeted_selection_targets",)
