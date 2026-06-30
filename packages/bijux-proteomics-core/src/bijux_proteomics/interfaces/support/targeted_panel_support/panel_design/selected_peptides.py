# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Selected peptide TSV loading for targeted panel design entrypoints."""

from __future__ import annotations

import csv
from pathlib import Path

import click

from bijux_proteomics.identification.peptide_evidence import PeptideEvidenceClass
from bijux_proteomics.sequences import (
    PeptideChemicalLiabilityTier,
    PeptideDetectabilityTier,
    PeptideUniquenessClass,
)
from bijux_proteomics.targeted.panel_design import TargetedPanelSelectedPeptideInput

from ...targeted_selection_io.field_parsing import (
    _parse_cli_bool,
    _split_semicolon_field,
)


def _load_targeted_panel_selected_peptides(
    path: Path,
) -> tuple[TargetedPanelSelectedPeptideInput, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "selected-peptide TSV must include a header row for targeted panel building"
            )
        required_columns = {
            "target_protein_ref",
            "target_protein_group_id",
            "gene_symbol",
            "peptide_sequence",
            "canonical_peptide",
            "rank",
            "observed_in_discovery",
            "observed_psm_count",
            "run_count",
            "detection_frequency",
            "replicate_consistency",
            "primary_evidence_class",
            "uniqueness_class",
            "uniqueness_score",
            "detectability_score",
            "detectability_tier",
            "suitability_score",
            "liability_tier",
            "liability_codes",
            "selection_score",
            "selection_reasons",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "selected-peptide TSV is missing required columns for targeted panel building: "
                + ", ".join(sorted(missing_columns))
            )
        rows: list[TargetedPanelSelectedPeptideInput] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                primary_class_raw = str(row.get("primary_evidence_class", "")).strip()
                rows.append(
                    TargetedPanelSelectedPeptideInput(
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
                        rank=int(str(row.get("rank", "")).strip()),
                        observed_in_discovery=_parse_cli_bool(
                            row.get("observed_in_discovery", ""),
                            field_name="observed_in_discovery",
                        ),
                        observed_psm_count=(
                            None
                            if not str(row.get("observed_psm_count", "")).strip()
                            else int(str(row.get("observed_psm_count", "")).strip())
                        ),
                        run_count=(
                            None
                            if not str(row.get("run_count", "")).strip()
                            else int(str(row.get("run_count", "")).strip())
                        ),
                        detection_frequency=(
                            None
                            if not str(row.get("detection_frequency", "")).strip()
                            else float(str(row.get("detection_frequency", "")).strip())
                        ),
                        replicate_consistency=(
                            None
                            if not str(row.get("replicate_consistency", "")).strip()
                            else float(
                                str(row.get("replicate_consistency", "")).strip()
                            )
                        ),
                        primary_evidence_class=(
                            None
                            if not primary_class_raw
                            else PeptideEvidenceClass(primary_class_raw)
                        ),
                        uniqueness_class=PeptideUniquenessClass(
                            str(row.get("uniqueness_class", "")).strip()
                        ),
                        uniqueness_score=float(
                            str(row.get("uniqueness_score", "")).strip()
                        ),
                        detectability_score=float(
                            str(row.get("detectability_score", "")).strip()
                        ),
                        detectability_tier=PeptideDetectabilityTier(
                            str(row.get("detectability_tier", "")).strip()
                        ),
                        suitability_score=float(
                            str(row.get("suitability_score", "")).strip()
                        ),
                        liability_tier=PeptideChemicalLiabilityTier(
                            str(row.get("liability_tier", "")).strip()
                        ),
                        liability_codes=_split_semicolon_field(
                            row.get("liability_codes", "")
                        ),
                        selection_score=float(
                            str(row.get("selection_score", "")).strip()
                        ),
                        selection_reasons=_split_semicolon_field(
                            row.get("selection_reasons", "")
                        ),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid selected-peptide row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return tuple(rows)


__all__ = ("_load_targeted_panel_selected_peptides",)
