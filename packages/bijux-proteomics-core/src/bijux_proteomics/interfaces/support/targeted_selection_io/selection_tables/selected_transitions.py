# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Selected-transition TSV loading for targeted assay interference review."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import TypedDict

import click

from bijux_proteomics.chemistry.fragments import FragmentIonSeries
from bijux_proteomics.targeted.transition_selection import (
    TargetedTransitionInterferenceRisk,
    TargetedTransitionSelectionFragment,
    TargetedTransitionSelectionPeptideEntry,
)

from ..field_parsing import _parse_cli_bool, _split_semicolon_field


class _SelectedTransitionAssayPayload(TypedDict):
    target_protein_ref: str
    target_protein_group_id: str
    gene_symbol: str | None
    peptide_sequence: str
    canonical_peptide: str
    peptide_rank: int
    precursor_charge: int
    precursor_mz: float
    source_library_entry_id: str | None
    chemistry_supported_transition_count: int
    selected_transition_count: int
    sufficient_transition_support: bool
    instrument_caveats: tuple[str, ...]
    selected_transitions: list[TargetedTransitionSelectionFragment]


def _load_selected_targeted_transitions(
    path: Path,
) -> tuple[TargetedTransitionSelectionPeptideEntry, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "selected-transition TSV must include a header row for targeted assay interference review"
            )
        required_columns = {
            "assay_entry_id",
            "target_protein_ref",
            "target_protein_group_id",
            "peptide_sequence",
            "canonical_peptide",
            "peptide_rank",
            "precursor_charge",
            "precursor_mz",
            "source_library_entry_id",
            "chemistry_supported_transition_count",
            "selected_transition_count",
            "sufficient_transition_support",
            "transition_rank",
            "fragment_label",
            "ion_type",
            "fragment_ordinal",
            "fragment_charge",
            "fragment_sequence",
            "fragment_mz",
            "expected_relative_intensity",
            "interference_risk",
            "interference_risk_score",
            "interference_risk_reasons",
            "selection_score",
            "selection_reasons",
            "instrument_caveats",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "selected-transition TSV is missing required columns for targeted assay interference review: "
                + ", ".join(sorted(missing_columns))
            )
        entries_by_assay: dict[str, _SelectedTransitionAssayPayload] = {}
        assay_order: list[str] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                assay_entry_id = str(row.get("assay_entry_id", "")).strip()
                if assay_entry_id not in entries_by_assay:
                    assay_order.append(assay_entry_id)
                    entries_by_assay[assay_entry_id] = {
                        "target_protein_ref": str(
                            row.get("target_protein_ref", "")
                        ).strip(),
                        "target_protein_group_id": str(
                            row.get("target_protein_group_id", "")
                        ).strip(),
                        "gene_symbol": (
                            value
                            if (value := str(row.get("gene_symbol", "")).strip())
                            else None
                        ),
                        "peptide_sequence": str(
                            row.get("peptide_sequence", "")
                        ).strip(),
                        "canonical_peptide": str(
                            row.get("canonical_peptide", "")
                        ).strip(),
                        "peptide_rank": int(str(row.get("peptide_rank", "")).strip()),
                        "precursor_charge": int(
                            str(row.get("precursor_charge", "")).strip()
                        ),
                        "precursor_mz": float(str(row.get("precursor_mz", "")).strip()),
                        "source_library_entry_id": (
                            value
                            if (
                                value := str(
                                    row.get("source_library_entry_id", "")
                                ).strip()
                            )
                            else None
                        ),
                        "chemistry_supported_transition_count": int(
                            str(
                                row.get("chemistry_supported_transition_count", "")
                            ).strip()
                        ),
                        "selected_transition_count": int(
                            str(row.get("selected_transition_count", "")).strip()
                        ),
                        "sufficient_transition_support": _parse_cli_bool(
                            row.get("sufficient_transition_support", ""),
                            field_name="sufficient_transition_support",
                        ),
                        "instrument_caveats": _split_semicolon_field(
                            row.get("instrument_caveats", "")
                        ),
                        "selected_transitions": [],
                    }
                selected_transitions = entries_by_assay[assay_entry_id][
                    "selected_transitions"
                ]
                selected_transitions.append(
                    TargetedTransitionSelectionFragment(
                        rank=int(str(row.get("transition_rank", "")).strip()),
                        fragment_label=str(row.get("fragment_label", "")).strip(),
                        ion_type=FragmentIonSeries(
                            str(row.get("ion_type", "")).strip()
                        ),
                        fragment_ordinal=int(
                            str(row.get("fragment_ordinal", "")).strip()
                        ),
                        fragment_charge=int(
                            str(row.get("fragment_charge", "")).strip()
                        ),
                        fragment_sequence=str(row.get("fragment_sequence", "")).strip(),
                        fragment_mz=float(str(row.get("fragment_mz", "")).strip()),
                        expected_relative_intensity=(
                            None
                            if not str(
                                row.get("expected_relative_intensity", "")
                            ).strip()
                            else float(
                                str(row.get("expected_relative_intensity", "")).strip()
                            )
                        ),
                        interference_risk=TargetedTransitionInterferenceRisk(
                            str(row.get("interference_risk", "")).strip()
                        ),
                        interference_risk_score=float(
                            str(row.get("interference_risk_score", "")).strip()
                        ),
                        interference_risk_reasons=_split_semicolon_field(
                            row.get("interference_risk_reasons", "")
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
                    f"invalid selected-transition row {row_number} in {path.name!r}: {exc}"
                ) from exc
    entries: list[TargetedTransitionSelectionPeptideEntry] = []
    for assay_entry_id in assay_order:
        assay_payload = entries_by_assay[assay_entry_id]
        ordered_transitions = tuple(
            sorted(
                assay_payload["selected_transitions"],
                key=lambda fragment: (fragment.rank, fragment.fragment_mz),
            )
        )
        entries.append(
            TargetedTransitionSelectionPeptideEntry(
                assay_entry_id=assay_entry_id,
                target_protein_ref=assay_payload["target_protein_ref"],
                target_protein_group_id=assay_payload["target_protein_group_id"],
                gene_symbol=assay_payload["gene_symbol"],
                peptide_sequence=assay_payload["peptide_sequence"],
                canonical_peptide=assay_payload["canonical_peptide"],
                peptide_rank=assay_payload["peptide_rank"],
                precursor_charge=assay_payload["precursor_charge"],
                precursor_mz=assay_payload["precursor_mz"],
                source_library_entry_id=assay_payload["source_library_entry_id"],
                chemistry_supported_transition_count=assay_payload[
                    "chemistry_supported_transition_count"
                ],
                selected_transition_count=assay_payload["selected_transition_count"],
                sufficient_transition_support=assay_payload[
                    "sufficient_transition_support"
                ],
                instrument_caveats=assay_payload["instrument_caveats"],
                selected_transitions=ordered_transitions,
            )
        )
    return tuple(entries)


__all__ = ("_load_selected_targeted_transitions",)
