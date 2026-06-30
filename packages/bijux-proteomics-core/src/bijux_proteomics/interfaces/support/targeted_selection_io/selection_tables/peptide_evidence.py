# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Peptide-evidence TSV loading for targeted peptide selection."""

from __future__ import annotations

import csv
from pathlib import Path

import click

from ...imports import (
    CrossRunReproducibilityClass,
    PeptideEvidenceClass,
    PeptideEvidenceEntry,
    TargetDecoyContaminantClass,
    TargetDecoyLabel,
)

from ..field_parsing import _parse_cli_bool, _split_semicolon_field


def _load_peptide_evidence_entries(path: Path) -> tuple[PeptideEvidenceEntry, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "peptide-evidence TSV must include a header row for targeted peptide selection"
            )
        required_columns = {
            "peptide",
            "canonical_peptide",
            "primary_class",
            "peptide_q_value",
            "accepted",
            "psm_count",
            "spectrum_count",
            "run_count",
            "detection_frequency",
            "replicate_consistency",
            "condition_specificity",
            "detected_condition_count",
            "reproducibility_class",
            "best_score",
            "charge_states",
            "run_ids",
            "protein_refs",
            "target_decoy_label",
            "target_decoy_contaminant_class",
            "contaminant_flag",
            "explanation",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "peptide-evidence TSV is missing required columns for targeted peptide selection: "
                + ", ".join(sorted(missing_columns))
            )
        entries: list[PeptideEvidenceEntry] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                entries.append(
                    PeptideEvidenceEntry(
                        peptide=str(row.get("peptide", "")).strip(),
                        canonical_peptide=str(row.get("canonical_peptide", "")).strip(),
                        primary_class=PeptideEvidenceClass(
                            str(row.get("primary_class", "")).strip()
                        ),
                        tags=(),
                        peptide_q_value=float(
                            str(row.get("peptide_q_value", "")).strip()
                        ),
                        accepted=_parse_cli_bool(
                            row.get("accepted", ""), field_name="accepted"
                        ),
                        psm_count=int(str(row.get("psm_count", "")).strip()),
                        spectrum_count=int(str(row.get("spectrum_count", "")).strip()),
                        run_count=int(str(row.get("run_count", "")).strip()),
                        detection_frequency=float(
                            str(row.get("detection_frequency", "")).strip()
                        ),
                        replicate_consistency=float(
                            str(row.get("replicate_consistency", "")).strip()
                        ),
                        condition_specificity=float(
                            str(row.get("condition_specificity", "")).strip()
                        ),
                        detected_condition_count=int(
                            str(row.get("detected_condition_count", "")).strip()
                        ),
                        reproducibility_class=CrossRunReproducibilityClass(
                            str(row.get("reproducibility_class", "")).strip()
                        ),
                        exploratory_override=_parse_cli_bool(
                            row.get("exploratory_override", "false"),
                            field_name="exploratory_override",
                        ),
                        best_score=float(str(row.get("best_score", "")).strip()),
                        charge_states=tuple(
                            int(token)
                            for token in _split_semicolon_field(
                                row.get("charge_states", "")
                            )
                        ),
                        run_ids=_split_semicolon_field(row.get("run_ids", "")),
                        protein_refs=_split_semicolon_field(
                            row.get("protein_refs", "")
                        ),
                        target_decoy_label=TargetDecoyLabel(
                            str(row.get("target_decoy_label", "")).strip()
                        ),
                        target_decoy_contaminant_class=TargetDecoyContaminantClass(
                            str(row.get("target_decoy_contaminant_class", "")).strip()
                        ),
                        contaminant_flag=_parse_cli_bool(
                            row.get("contaminant_flag", "false"),
                            field_name="contaminant_flag",
                        ),
                        explanation=str(row.get("explanation", "")).strip(),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid peptide-evidence row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return tuple(entries)


__all__ = ("_load_peptide_evidence_entries",)
