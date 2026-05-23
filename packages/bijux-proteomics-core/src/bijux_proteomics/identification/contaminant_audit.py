# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Compatibility audits over the owned contaminant evidence separation surface."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.confidence import (
    ProteinInferenceStrategyKind,
    compare_protein_inference_strategies,
)
from bijux_proteomics.identification.contaminant_evidence import (
    ContaminantSeparatedPsmEntry as ContaminantPsmEntry,
    build_contaminant_evidence_report,
)
from bijux_proteomics.identification.contracts import PsmRecord
from bijux_proteomics_foundation import JsonModel


class ContaminantStrategyShift(JsonModel):
    """How one protein-inference strategy changes after contaminant filtering."""

    model_config = ConfigDict(extra="forbid")

    strategy_kind: ProteinInferenceStrategyKind
    strategy_label: str = Field(..., min_length=1)
    raw_selected_proteins: tuple[str, ...] = Field(default_factory=tuple)
    filtered_selected_proteins: tuple[str, ...] = Field(default_factory=tuple)
    removed_contaminant_proteins: tuple[str, ...] = Field(default_factory=tuple)
    target_selection_changed: bool


class ContaminantAwareProteinInferenceAudit(JsonModel):
    """Audit whether contaminant evidence changes final protein-inference posture."""

    model_config = ConfigDict(extra="forbid")

    contaminant_psm_count: int = Field(..., ge=0)
    contaminant_protein_count: int = Field(..., ge=0)
    unresolved_contaminant_promotion: bool
    strategy_shifts: tuple[ContaminantStrategyShift, ...] = Field(default_factory=tuple)


class ContaminantPeptideMatchReport(JsonModel):
    """Separate contaminant-match report over normalized PSM evidence."""

    model_config = ConfigDict(extra="forbid")

    contaminant_psm_count: int = Field(..., ge=0)
    pure_contaminant_psm_count: int = Field(..., ge=0)
    mixed_reference_psm_count: int = Field(..., ge=0)
    contaminant_peptide_count: int = Field(..., ge=0)
    contaminant_protein_counts: dict[str, int] = Field(default_factory=dict)
    entries: tuple[ContaminantPsmEntry, ...] = Field(default_factory=tuple)


def _is_contaminant(protein_ref: str, prefixes: tuple[str, ...]) -> bool:
    return any(protein_ref.startswith(prefix) for prefix in prefixes)


def _filter_contaminant_protein_refs(
    records: tuple[PsmRecord, ...],
    *,
    contaminant_prefixes: tuple[str, ...],
) -> tuple[PsmRecord, ...]:
    filtered_records: list[PsmRecord] = []
    for record in records:
        retained_refs = tuple(
            ref
            for ref in record.protein_refs
            if not _is_contaminant(ref, contaminant_prefixes)
        )
        if not retained_refs:
            continue
        filtered_records.append(
            record.model_copy(update={"protein_refs": retained_refs})
        )
    return tuple(filtered_records)


def build_contaminant_aware_protein_inference_audit(
    records: tuple[PsmRecord, ...],
    *,
    contaminant_prefixes: tuple[str, ...] = ("CON__",),
    picked_threshold: float = 0.05,
) -> ContaminantAwareProteinInferenceAudit:
    """Audit whether contaminants still travel into protein selections."""

    raw = compare_protein_inference_strategies(
        records,
        picked_threshold=picked_threshold,
    )
    filtered_records = _filter_contaminant_protein_refs(
        records,
        contaminant_prefixes=contaminant_prefixes,
    )
    filtered = compare_protein_inference_strategies(
        filtered_records,
        picked_threshold=picked_threshold,
    )
    filtered_by_kind = {entry.strategy_kind: entry for entry in filtered.selections}
    strategy_shifts: list[ContaminantStrategyShift] = []
    unresolved = False
    for selection in raw.selections:
        contaminant_proteins = tuple(
            sorted(
                protein
                for protein in selection.selected_proteins
                if _is_contaminant(protein, contaminant_prefixes)
            )
        )
        unresolved = unresolved or bool(contaminant_proteins)
        filtered_selection = filtered_by_kind.get(selection.strategy_kind)
        filtered_selected = (
            filtered_selection.selected_proteins
            if filtered_selection is not None
            else ()
        )
        strategy_shifts.append(
            ContaminantStrategyShift(
                strategy_kind=selection.strategy_kind,
                strategy_label=selection.strategy_label,
                raw_selected_proteins=selection.selected_proteins,
                filtered_selected_proteins=filtered_selected,
                removed_contaminant_proteins=contaminant_proteins,
                target_selection_changed=tuple(
                    protein
                    for protein in selection.selected_proteins
                    if not _is_contaminant(protein, contaminant_prefixes)
                )
                != tuple(
                    protein
                    for protein in filtered_selected
                    if not _is_contaminant(protein, contaminant_prefixes)
                ),
            )
        )
    contaminant_psm_count = sum(
        any(_is_contaminant(ref, contaminant_prefixes) for ref in record.protein_refs)
        for record in records
    )
    contaminant_protein_set = {
        ref
        for record in records
        for ref in record.protein_refs
        if _is_contaminant(ref, contaminant_prefixes)
    }
    return ContaminantAwareProteinInferenceAudit(
        contaminant_psm_count=contaminant_psm_count,
        contaminant_protein_count=len(contaminant_protein_set),
        unresolved_contaminant_promotion=unresolved,
        strategy_shifts=tuple(strategy_shifts),
    )


def build_contaminant_peptide_match_report(
    records: tuple[PsmRecord, ...],
    *,
    contaminant_prefixes: tuple[str, ...] = ("CON__",),
) -> ContaminantPeptideMatchReport:
    """Separate contaminant-carrying PSM evidence from target-only matches."""
    report = build_contaminant_evidence_report(
        records,
        contaminant_prefixes=contaminant_prefixes,
    )
    return ContaminantPeptideMatchReport(
        contaminant_psm_count=report.summary.contaminant_psm_count,
        pure_contaminant_psm_count=report.summary.pure_contaminant_psm_count,
        mixed_reference_psm_count=report.summary.mixed_reference_psm_count,
        contaminant_peptide_count=report.summary.contaminant_peptide_count,
        contaminant_protein_counts={
            entry.protein_ref: entry.psm_count for entry in report.protein_entries
        },
        entries=report.psm_entries,
    )
