# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Targeted selection table loaders."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import TypedDict

import click

from ..imports import (
    CrossRunReproducibilityClass,
    DiscoveryTargetProteinEntry,
    DiscoveryTargetedPeptideSelectionEntry,
    FragmentIonSeries,
    PeptideChemicalLiabilityTier,
    PeptideDetectabilityTier,
    PeptideEvidenceClass,
    PeptideEvidenceEntry,
    PeptideUniquenessClass,
    TargetDecoyContaminantClass,
    TargetDecoyLabel,
    TargetedPeptideCandidateSource,
    TargetedTransitionInterferenceRisk,
    TargetedTransitionSelectionFragment,
    TargetedTransitionSelectionPeptideEntry,
)

from .field_parsing import _parse_cli_bool, _split_semicolon_field


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


def _load_selected_targeted_peptides(
    path: Path,
) -> tuple[DiscoveryTargetedPeptideSelectionEntry, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "selected-peptide TSV must include a header row for targeted transition selection"
            )
        required_columns = {
            "target_protein_ref",
            "target_protein_group_id",
            "rank",
            "candidate_source",
            "peptide_sequence",
            "canonical_peptide",
            "observed_in_discovery",
            "uniqueness_class",
            "uniqueness_score",
            "detectability_score",
            "detectability_tier",
            "suitability_score",
            "liability_tier",
            "selection_score",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "selected-peptide TSV is missing required columns for targeted transition selection: "
                + ", ".join(sorted(missing_columns))
            )
        entries: list[DiscoveryTargetedPeptideSelectionEntry] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                primary_evidence_class_raw = str(
                    row.get("primary_evidence_class", "")
                ).strip()
                entries.append(
                    DiscoveryTargetedPeptideSelectionEntry(
                        target_protein_ref=str(
                            row.get("target_protein_ref", "")
                        ).strip(),
                        target_protein_group_id=str(
                            row.get("target_protein_group_id", "")
                        ).strip(),
                        gene_symbol=(
                            value
                            if (value := str(row.get("gene_symbol", "")).strip())
                            else None
                        ),
                        peptide_sequence=str(row.get("peptide_sequence", "")).strip(),
                        canonical_peptide=str(row.get("canonical_peptide", "")).strip(),
                        candidate_source=TargetedPeptideCandidateSource(
                            str(row.get("candidate_source", "")).strip()
                        ),
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
                            if not primary_evidence_class_raw
                            else PeptideEvidenceClass(primary_evidence_class_raw)
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
    return tuple(entries)


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


__all__ = [
    "_load_peptide_evidence_entries",
    "_load_selected_targeted_peptides",
    "_load_selected_targeted_transitions",
    "_load_targeted_selection_targets",
]
