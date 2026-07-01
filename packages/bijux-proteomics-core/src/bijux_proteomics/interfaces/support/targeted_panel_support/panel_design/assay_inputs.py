# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Assay TSV loading for targeted panel design entrypoints."""

from __future__ import annotations

import csv
from pathlib import Path

import click

from bijux_proteomics.targeted.assay_interference import (
    TargetedAssayInterferenceReason,
    TargetedAssayInterferenceRiskTier,
)
from bijux_proteomics.targeted.panel_design import TargetedPanelAssayInput

from ...targeted_selection_io.field_parsing import (
    _parse_cli_bool,
    _split_semicolon_field,
)


def _load_targeted_panel_assay_inputs(
    path: Path,
) -> tuple[TargetedPanelAssayInput, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "assay-interference assay TSV must include a header row for targeted panel building"
            )
        required_columns = {
            "assay_entry_id",
            "target_protein_ref",
            "target_protein_group_id",
            "gene_symbol",
            "peptide_sequence",
            "canonical_peptide",
            "peptide_rank",
            "precursor_charge",
            "precursor_mz",
            "selected_transition_count",
            "exported_transition_count",
            "interference_risk_score",
            "interference_risk_tier",
            "downgrade_reasons",
            "panel_export_allowed",
            "panel_export_caveat",
            "source_library_entry_id",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "assay-interference assay TSV is missing required columns for targeted panel building: "
                + ", ".join(sorted(missing_columns))
            )
        rows: list[TargetedPanelAssayInput] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                downgrade_reasons = tuple(
                    TargetedAssayInterferenceReason(reason)
                    for reason in _split_semicolon_field(
                        row.get("downgrade_reasons", "")
                    )
                )
                rows.append(
                    TargetedPanelAssayInput(
                        assay_entry_id=str(row.get("assay_entry_id", "")).strip(),
                        target_protein_ref=str(
                            row.get("target_protein_ref", "")
                        ).strip(),
                        target_protein_group_id=str(
                            row.get("target_protein_group_id", "")
                        ).strip(),
                        gene_symbol=(
                            None
                            if not str(row.get("gene_symbol", "")).strip()
                            else str(row.get("gene_symbol", "")).strip()
                        ),
                        peptide_sequence=str(row.get("peptide_sequence", "")).strip(),
                        canonical_peptide=str(row.get("canonical_peptide", "")).strip(),
                        peptide_rank=int(str(row.get("peptide_rank", "")).strip()),
                        precursor_charge=int(
                            str(row.get("precursor_charge", "")).strip()
                        ),
                        precursor_mz=float(str(row.get("precursor_mz", "")).strip()),
                        selected_transition_count=int(
                            str(row.get("selected_transition_count", "")).strip()
                        ),
                        exported_transition_count=int(
                            str(row.get("exported_transition_count", "")).strip()
                        ),
                        interference_risk_score=float(
                            str(row.get("interference_risk_score", "")).strip()
                        ),
                        interference_risk_tier=TargetedAssayInterferenceRiskTier(
                            str(row.get("interference_risk_tier", "")).strip()
                        ),
                        downgrade_reasons=downgrade_reasons,
                        panel_export_allowed=_parse_cli_bool(
                            row.get("panel_export_allowed", ""),
                            field_name="panel_export_allowed",
                        ),
                        panel_export_caveat=str(
                            row.get("panel_export_caveat", "")
                        ).strip(),
                        source_library_entry_id=(
                            None
                            if not str(row.get("source_library_entry_id", "")).strip()
                            else str(row.get("source_library_entry_id", "")).strip()
                        ),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid assay-interference assay row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return tuple(rows)


__all__ = ("_load_targeted_panel_assay_inputs",)
