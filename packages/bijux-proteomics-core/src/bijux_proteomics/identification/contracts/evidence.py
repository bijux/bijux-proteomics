# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
# ruff: noqa: F401

"""Peptide and protein evidence rollup contracts."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
import csv
from enum import StrEnum
import hashlib
import json
import math
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field, field_validator, model_validator

from bijux_proteomics.chemistry import (
    canonicalize_modified_peptide,
    parse_modified_peptide,
)
from bijux_proteomics.domain.records import (
    ImportedEvidenceProvenance,
    ModifiedPeptide as CanonicalModifiedPeptide,
    PSMRecord as CanonicalPsmRecord,
    PeptideRecord as CanonicalPeptideRecord,
    ProteinGroup as CanonicalProteinGroup,
    ProteinRecord as CanonicalProteinRecord,
    RejectedEvidence as CanonicalRejectedEvidence,
    TargetDecoyState,
)
from bijux_proteomics.scientific_tables import (
    ScientificTableRejectedRow,
    ScientificTableValidationIssue,
    build_psm_table_schema,
    validate_scientific_table,
)
from bijux_proteomics.sequences.core import NormalizedProteinRecord
from bijux_proteomics.sequences.peptide_uniqueness_index import (
    build_peptide_uniqueness_index,
)

if TYPE_CHECKING:
    from bijux_proteomics.identification.cross_run_reproducibility import (
        RunDetectionContext,
    )
from bijux_proteomics.tabular import render_tsv_rows
from bijux_proteomics_foundation import DocumentSchema, JsonModel
from bijux_proteomics.identification.contracts.psm import (
    PsmRecord,
    TargetDecoyLabel,
    _combine_labels,
    parse_target_decoy_label,
)

class PeptideEvidenceEntry(JsonModel):
    """Rolled-up peptide-level evidence across PSMs."""

    model_config = ConfigDict(extra="forbid")

    peptide: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    psm_count: int = Field(..., ge=1)
    spectrum_count: int = Field(..., ge=1)
    best_score: float
    best_q_value: float | None = Field(default=None, ge=0.0)
    charge_states: tuple[int, ...] = Field(default_factory=tuple)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_label: TargetDecoyLabel = TargetDecoyLabel.UNKNOWN

    def to_domain_record(self) -> CanonicalPeptideRecord:
        """Convert one peptide evidence rollup into the canonical peptide record."""

        return CanonicalPeptideRecord(
            record_id=self.canonical_peptide,
            peptide_sequence=self.peptide,
            canonical_peptide=self.canonical_peptide,
            protein_refs=self.protein_refs,
            charge_states=self.charge_states,
            score=self.best_score,
            q_value=self.best_q_value,
            target_decoy_state=TargetDecoyState(self.target_decoy_label.value),
            metadata={
                "source_contract": "identification.peptide_evidence",
                "psm_count": str(self.psm_count),
                "spectrum_count": str(self.spectrum_count),
            },
        )


class ProteinEvidenceEntry(JsonModel):
    """Rolled-up protein-level evidence across peptides and PSMs."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    peptide_count: int = Field(..., ge=1)
    unique_peptide_count: int = Field(..., ge=0)
    shared_peptide_count: int = Field(..., ge=0)
    best_score: float
    best_q_value: float | None = Field(default=None, ge=0.0)
    peptides: tuple[str, ...] = Field(default_factory=tuple)
    spectrum_count: int = Field(..., ge=1)
    target_decoy_label: TargetDecoyLabel = TargetDecoyLabel.UNKNOWN

    def to_domain_record(self) -> CanonicalProteinRecord:
        """Convert one protein evidence rollup into the canonical protein record."""

        return CanonicalProteinRecord(
            record_id=self.protein_ref,
            primary_protein_ref=self.protein_ref,
            protein_refs=(self.protein_ref,),
            peptide_sequences=self.peptides,
            score=self.best_score,
            q_value=self.best_q_value,
            target_decoy_state=TargetDecoyState(self.target_decoy_label.value),
            metadata={
                "source_contract": "identification.protein_evidence",
                "peptide_count": str(self.peptide_count),
                "unique_peptide_count": str(self.unique_peptide_count),
                "shared_peptide_count": str(self.shared_peptide_count),
                "spectrum_count": str(self.spectrum_count),
            },
        )



class PsmSummaryReport(JsonModel):
    """Compact search-result summary over normalized PSM records."""

    model_config = ConfigDict(extra="forbid")

    total_psms: int = Field(..., ge=0)
    target_psms: int = Field(..., ge=0)
    decoy_psms: int = Field(..., ge=0)
    mixed_psms: int = Field(..., ge=0)
    unknown_psms: int = Field(..., ge=0)
    counts_by_charge: dict[str, int] = Field(default_factory=dict)
    counts_by_score_bin: dict[str, int] = Field(default_factory=dict)


class PeptideSummaryReport(JsonModel):
    """Compact peptide-level summary derived from PSM records."""

    model_config = ConfigDict(extra="forbid")

    total_peptides: int = Field(..., ge=0)
    modified_peptides: int = Field(..., ge=0)
    unique_peptides: int = Field(..., ge=0)
    shared_peptides: int = Field(..., ge=0)
    decoy_peptides: int = Field(..., ge=0)


class ProteinSummaryEntry(JsonModel):
    """One protein summary row with optional sequence coverage."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    peptide_count: int = Field(..., ge=0)
    unique_peptide_count: int = Field(..., ge=0)
    shared_peptide_count: int = Field(..., ge=0)
    coverage_fraction: float | None = Field(default=None, ge=0.0, le=1.0)


class ProteinSummaryReport(JsonModel):
    """Compact protein-level summary over evidence rollups."""

    model_config = ConfigDict(extra="forbid")

    total_proteins: int = Field(..., ge=0)
    target_proteins: int = Field(..., ge=0)
    decoy_proteins: int = Field(..., ge=0)
    protein_groups: tuple[ProteinSummaryEntry, ...] = Field(default_factory=tuple)



def rollup_peptide_evidence(
    records: tuple[PsmRecord, ...],
) -> tuple[PeptideEvidenceEntry, ...]:
    """Roll up multiple PSMs into peptide-level evidence rows."""
    grouped: dict[str, list[PsmRecord]] = defaultdict(list)
    for record in records:
        grouped[record.canonical_peptide].append(record)

    rollups: list[PeptideEvidenceEntry] = []
    for canonical_peptide in sorted(grouped):
        group = grouped[canonical_peptide]
        best = max(
            group,
            key=lambda record: (
                record.score,
                -(record.q_value if record.q_value is not None else float("inf")),
                record.peptide,
            ),
        )
        protein_refs = tuple(
            sorted(
                {protein_ref for record in group for protein_ref in record.protein_refs}
            )
        )
        charge_states = tuple(sorted({record.charge for record in group}))
        spectra = {record.spectrum_id for record in group}
        q_values = [record.q_value for record in group if record.q_value is not None]
        rollups.append(
            PeptideEvidenceEntry(
                peptide=best.peptide,
                canonical_peptide=canonical_peptide,
                psm_count=len(group),
                spectrum_count=len(spectra),
                best_score=best.score,
                best_q_value=min(q_values) if q_values else None,
                charge_states=charge_states,
                protein_refs=protein_refs,
                target_decoy_label=_combine_labels(
                    tuple(record.target_decoy_label for record in group)
                ),
            )
        )
    return tuple(rollups)


def rollup_protein_evidence(
    records: tuple[PsmRecord, ...],
) -> tuple[ProteinEvidenceEntry, ...]:
    """Roll up PSMs and peptides into protein-level evidence rows."""
    peptide_rollups = rollup_peptide_evidence(records)
    protein_to_peptides: dict[str, list[PeptideEvidenceEntry]] = defaultdict(list)
    protein_to_spectra: dict[str, set[str]] = defaultdict(set)

    record_by_peptide: dict[str, list[PsmRecord]] = defaultdict(list)
    for record in records:
        record_by_peptide[record.canonical_peptide].append(record)

    for peptide_rollup in peptide_rollups:
        for protein_ref in peptide_rollup.protein_refs:
            protein_to_peptides[protein_ref].append(peptide_rollup)
            for record in record_by_peptide[peptide_rollup.canonical_peptide]:
                if protein_ref in record.protein_refs:
                    protein_to_spectra[protein_ref].add(record.spectrum_id)

    rollups: list[ProteinEvidenceEntry] = []
    for protein_ref in sorted(protein_to_peptides):
        peptides = protein_to_peptides[protein_ref]
        peptide_names = tuple(sorted(peptide.canonical_peptide for peptide in peptides))
        unique_peptide_count = sum(
            1 for peptide in peptides if len(peptide.protein_refs) == 1
        )
        shared_peptide_count = sum(
            1 for peptide in peptides if len(peptide.protein_refs) > 1
        )
        q_values = [
            peptide.best_q_value
            for peptide in peptides
            if peptide.best_q_value is not None
        ]
        rollups.append(
            ProteinEvidenceEntry(
                protein_ref=protein_ref,
                peptide_count=len(peptides),
                unique_peptide_count=unique_peptide_count,
                shared_peptide_count=shared_peptide_count,
                best_score=max(peptide.best_score for peptide in peptides),
                best_q_value=min(q_values) if q_values else None,
                peptides=peptide_names,
                spectrum_count=len(protein_to_spectra[protein_ref]),
                target_decoy_label=parse_target_decoy_label(
                    protein_refs=(protein_ref,),
                ),
            )
        )
    return tuple(rollups)



def build_psm_summary_report(
    records: tuple[PsmRecord, ...],
    *,
    score_bin_size: float = 10.0,
) -> PsmSummaryReport:
    """Build a compact summary report over normalized PSM records."""
    counts_by_charge: dict[str, int] = defaultdict(int)
    counts_by_score_bin: dict[str, int] = defaultdict(int)
    target_psms = 0
    decoy_psms = 0
    mixed_psms = 0
    unknown_psms = 0
    for record in records:
        counts_by_charge[str(record.charge)] += 1
        lower = int(record.score // score_bin_size) * int(score_bin_size)
        upper = lower + int(score_bin_size)
        counts_by_score_bin[f"{lower}-{upper}"] += 1
        if record.target_decoy_label is TargetDecoyLabel.TARGET:
            target_psms += 1
        elif record.target_decoy_label is TargetDecoyLabel.DECOY:
            decoy_psms += 1
        elif record.target_decoy_label is TargetDecoyLabel.MIXED:
            mixed_psms += 1
        else:
            unknown_psms += 1
    return PsmSummaryReport(
        total_psms=len(records),
        target_psms=target_psms,
        decoy_psms=decoy_psms,
        mixed_psms=mixed_psms,
        unknown_psms=unknown_psms,
        counts_by_charge=dict(sorted(counts_by_charge.items())),
        counts_by_score_bin=dict(sorted(counts_by_score_bin.items())),
    )


def build_peptide_summary_report(
    records: tuple[PsmRecord, ...],
) -> PeptideSummaryReport:
    """Build a compact peptide-level summary report."""
    peptide_rollups = rollup_peptide_evidence(records)
    return PeptideSummaryReport(
        total_peptides=len(peptide_rollups),
        modified_peptides=sum(
            1 for peptide in peptide_rollups if "[" in peptide.canonical_peptide
        ),
        unique_peptides=sum(
            1 for peptide in peptide_rollups if len(peptide.protein_refs) == 1
        ),
        shared_peptides=sum(
            1 for peptide in peptide_rollups if len(peptide.protein_refs) > 1
        ),
        decoy_peptides=sum(
            1
            for peptide in peptide_rollups
            if peptide.target_decoy_label is TargetDecoyLabel.DECOY
        ),
    )


def build_protein_summary_report(
    records: tuple[PsmRecord, ...],
    *,
    protein_lengths: dict[str, int] | None = None,
) -> ProteinSummaryReport:
    """Build a compact protein-level summary report with optional coverage."""
    rollups = rollup_protein_evidence(records)
    summary_entries: list[ProteinSummaryEntry] = []
    target_proteins = 0
    decoy_proteins = 0
    for rollup in rollups:
        coverage_fraction: float | None = None
        if protein_lengths and protein_lengths.get(rollup.protein_ref):
            covered_residues = {
                residue_index
                for peptide in rollup.peptides
                for residue_index in range(1, len(peptide) + 1)
            }
            coverage_fraction = min(
                len(covered_residues) / protein_lengths[rollup.protein_ref],
                1.0,
            )
        summary_entries.append(
            ProteinSummaryEntry(
                protein_ref=rollup.protein_ref,
                peptide_count=rollup.peptide_count,
                unique_peptide_count=rollup.unique_peptide_count,
                shared_peptide_count=rollup.shared_peptide_count,
                coverage_fraction=coverage_fraction,
            )
        )
        if rollup.target_decoy_label is TargetDecoyLabel.DECOY:
            decoy_proteins += 1
        else:
            target_proteins += 1
    return ProteinSummaryReport(
        total_proteins=len(summary_entries),
        target_proteins=target_proteins,
        decoy_proteins=decoy_proteins,
        protein_groups=tuple(summary_entries),
    )

__all__ = [
    'PeptideEvidenceEntry',
    'ProteinEvidenceEntry',
    'PsmSummaryReport',
    'PeptideSummaryReport',
    'ProteinSummaryEntry',
    'ProteinSummaryReport',
    'rollup_peptide_evidence',
    'rollup_protein_evidence',
    'build_psm_summary_report',
    'build_peptide_summary_report',
    'build_protein_summary_report',
]
