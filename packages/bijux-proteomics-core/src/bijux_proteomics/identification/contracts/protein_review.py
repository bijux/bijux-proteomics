# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
# ruff: noqa: F401

"""Protein review, trace, coverage, and picked-FDR contracts."""

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
from bijux_proteomics._scientific_tables import (
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
from bijux_proteomics._tabular import render_rows_tsv
from bijux_proteomics_foundation import DocumentSchema, JsonModel
from bijux_proteomics.identification.contracts.evidence import rollup_peptide_evidence
from bijux_proteomics.identification.contracts.grouping import build_protein_groups
from bijux_proteomics.identification.contracts.protein_inference import (
    ParsimonyVariant,
    infer_proteins_by_parsimony,
)
from bijux_proteomics.identification.contracts.psm import (
    PsmRecord,
    TargetDecoyLabel,
    TargetDecoyLabelPolicy,
)

class CombinedEvidenceQuantSupport(JsonModel):
    """Quant support for one protein/sample slice inside a combined evidence view."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    abundance: float | None = Field(default=None, ge=0.0)


class CombinedEvidenceEntry(JsonModel):
    """Joined PSM, peptide, protein, PTM, and quant evidence for review."""

    model_config = ConfigDict(extra="forbid")

    canonical_peptide: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    spectrum_ids: tuple[str, ...] = Field(default_factory=tuple)
    psm_count: int = Field(..., ge=0)
    best_psm_q_value: float | None = Field(default=None, ge=0.0)
    peptide_charge_states: tuple[int, ...] = Field(default_factory=tuple)
    protein_group_id: str | None = None
    protein_group_members: tuple[str, ...] = Field(default_factory=tuple)
    parsimony_variants: tuple[ParsimonyVariant, ...] = Field(default_factory=tuple)
    ptm_site_keys: tuple[str, ...] = Field(default_factory=tuple)
    quant_support: tuple[CombinedEvidenceQuantSupport, ...] = Field(
        default_factory=tuple
    )


class CombinedEvidenceReport(JsonModel):
    """Stable combined evidence view across identification-adjacent surfaces."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[CombinedEvidenceEntry, ...] = Field(default_factory=tuple)


class PeptideProteinTraceEntry(JsonModel):
    """Stable peptide-to-protein trace row for downstream review and export."""

    model_config = ConfigDict(extra="forbid")

    canonical_peptide: str = Field(..., min_length=1)
    peptide: str = Field(..., min_length=1)
    spectrum_ids: tuple[str, ...] = Field(default_factory=tuple)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    protein_group_ids: tuple[str, ...] = Field(default_factory=tuple)
    charge_states: tuple[int, ...] = Field(default_factory=tuple)
    best_score: float
    best_q_value: float | None = Field(default=None, ge=0.0)


class PeptideProteinTraceReport(JsonModel):
    """Stable peptide-to-protein trace collection."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[PeptideProteinTraceEntry, ...] = Field(default_factory=tuple)


class ProteinCoverageEntry(JsonModel):
    """Sequence-aware protein coverage summary from identified peptides."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    residue_count: int = Field(..., ge=1)
    covered_residue_count: int = Field(..., ge=0)
    coverage_fraction: float = Field(..., ge=0.0, le=1.0)
    covered_ranges: tuple[tuple[int, int], ...] = Field(default_factory=tuple)
    covered_peptides: tuple[str, ...] = Field(default_factory=tuple)


class DatabasePeptideUniqueness(StrEnum):
    """Uniqueness classification across a provided protein database."""

    UNIQUE = "unique"
    SHARED = "shared"
    ISOFORM_SHARED = "isoform_shared"
    FAMILY_SHARED = "family_shared"
    CONTAMINANT = "contaminant"
    DECOY = "decoy"
    MIXED = "mixed"
    MISSING = "missing"


class DatabasePeptideUniquenessEntry(JsonModel):
    """One peptide uniqueness entry over a provided database."""

    model_config = ConfigDict(extra="forbid")

    canonical_peptide: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    protein_families: tuple[str, ...] = Field(default_factory=tuple)
    gene_symbols: tuple[str, ...] = Field(default_factory=tuple)
    uniqueness: DatabasePeptideUniqueness


class PickedProteinFdrEntry(JsonModel):
    """One picked target-decoy protein entry with FDR state."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    partner_ref: str | None = None
    score: float
    q_value: float = Field(..., ge=0.0)
    fdr: float = Field(..., ge=0.0)
    rank: int = Field(..., ge=1)
    accepted: bool
    target_decoy_label: TargetDecoyLabel
    supporting_peptides: tuple[str, ...] = Field(default_factory=tuple)


def build_combined_evidence_report(
    records: tuple[PsmRecord, ...],
    *,
    ptm_site_keys_by_peptide: dict[str, tuple[str, ...]] | None = None,
    quant_support_by_protein: dict[str, dict[str, float | None]] | None = None,
    parsimony_variants: tuple[ParsimonyVariant, ...] = (
        ParsimonyVariant.GREEDY_COVERAGE,
        ParsimonyVariant.UNIQUE_EVIDENCE_PRIORITY,
        ParsimonyVariant.BEST_SCORE_PRIORITY,
    ),
) -> CombinedEvidenceReport:
    """Join identification evidence with optional PTM and quant support."""
    peptide_rollups = rollup_peptide_evidence(records)
    protein_groups = build_protein_groups(records)
    groups_by_protein = {
        protein_ref: group
        for group in protein_groups
        for protein_ref in group.protein_refs
    }
    selected_variants_by_protein: dict[str, set[ParsimonyVariant]] = defaultdict(set)
    for variant in parsimony_variants:
        for entry in infer_proteins_by_parsimony(records, variant=variant):
            selected_variants_by_protein[entry.protein_ref].add(variant)

    entries: list[CombinedEvidenceEntry] = []
    for rollup in peptide_rollups:
        ptm_site_keys = tuple(
            sorted((ptm_site_keys_by_peptide or {}).get(rollup.canonical_peptide, ()))
        )
        quant_lookup = quant_support_by_protein or {}
        for protein_ref in rollup.protein_refs:
            group = groups_by_protein.get(protein_ref)
            entries.append(
                CombinedEvidenceEntry(
                    canonical_peptide=rollup.canonical_peptide,
                    protein_ref=protein_ref,
                    spectrum_ids=tuple(
                        sorted(
                            record.spectrum_id
                            for record in records
                            if record.canonical_peptide == rollup.canonical_peptide
                        )
                    ),
                    psm_count=rollup.psm_count,
                    best_psm_q_value=rollup.best_q_value,
                    peptide_charge_states=rollup.charge_states,
                    protein_group_id=group.group_id if group is not None else None,
                    protein_group_members=group.protein_refs
                    if group is not None
                    else (),
                    parsimony_variants=tuple(
                        sorted(
                            selected_variants_by_protein.get(protein_ref, set()),
                            key=lambda item: item.value,
                        )
                    ),
                    ptm_site_keys=ptm_site_keys,
                    quant_support=tuple(
                        CombinedEvidenceQuantSupport(
                            sample_id=sample_id,
                            abundance=abundance,
                        )
                        for sample_id, abundance in sorted(
                            quant_lookup.get(protein_ref, {}).items()
                        )
                    ),
                )
            )
    return CombinedEvidenceReport(
        entries=tuple(
            sorted(
                entries,
                key=lambda entry: (entry.canonical_peptide, entry.protein_ref),
            )
        )
    )


def build_peptide_protein_trace_report(
    records: tuple[PsmRecord, ...],
) -> PeptideProteinTraceReport:
    """Build stable peptide-to-protein traces that survive export."""
    peptide_rollups = rollup_peptide_evidence(records)
    protein_groups = build_protein_groups(records)
    group_ids_by_protein: dict[str, set[str]] = defaultdict(set)
    for group in protein_groups:
        for protein_ref in group.protein_refs:
            group_ids_by_protein[protein_ref].add(group.group_id)

    entries: list[PeptideProteinTraceEntry] = []
    for rollup in peptide_rollups:
        spectrum_ids = tuple(
            sorted(
                record.spectrum_id
                for record in records
                if record.canonical_peptide == rollup.canonical_peptide
            )
        )
        group_ids = tuple(
            sorted(
                {
                    group_id
                    for protein_ref in rollup.protein_refs
                    for group_id in group_ids_by_protein.get(protein_ref, set())
                }
            )
        )
        entries.append(
            PeptideProteinTraceEntry(
                canonical_peptide=rollup.canonical_peptide,
                peptide=rollup.peptide,
                spectrum_ids=spectrum_ids,
                protein_refs=rollup.protein_refs,
                protein_group_ids=group_ids,
                charge_states=rollup.charge_states,
                best_score=rollup.best_score,
                best_q_value=rollup.best_q_value,
            )
        )
    return PeptideProteinTraceReport(
        entries=tuple(
            sorted(entries, key=lambda entry: (entry.canonical_peptide, entry.peptide))
        )
    )


def export_peptide_protein_trace_jsonl(
    report: PeptideProteinTraceReport,
    path: Path,
) -> None:
    """Write a stable JSONL export for peptide-to-protein traces."""
    with path.open("w", encoding="utf-8") as handle:
        for entry in report.entries:
            handle.write(
                json.dumps(entry.to_dict(), sort_keys=True, separators=(",", ":"))
            )
            handle.write("\n")


def export_peptide_protein_trace_tsv(
    report: PeptideProteinTraceReport,
    path: Path,
) -> None:
    """Write a stable TSV export for peptide-to-protein traces."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(
            [
                "canonical_peptide",
                "peptide",
                "spectrum_ids",
                "protein_refs",
                "protein_group_ids",
                "charge_states",
                "best_score",
                "best_q_value",
            ]
        )
        for entry in report.entries:
            writer.writerow(
                [
                    entry.canonical_peptide,
                    entry.peptide,
                    ";".join(entry.spectrum_ids),
                    ";".join(entry.protein_refs),
                    ";".join(entry.protein_group_ids),
                    ";".join(str(charge) for charge in entry.charge_states),
                    entry.best_score,
                    "" if entry.best_q_value is None else entry.best_q_value,
                ]
            )



def build_protein_coverage_map(
    records: tuple[PsmRecord, ...],
    *,
    protein_sequences: dict[str, str],
) -> tuple[ProteinCoverageEntry, ...]:
    """Build a sequence-aware coverage map for proteins present in evidence."""
    from bijux_proteomics.identification.protein_coverage import (
        ProteinCoverageCoordinateStatus,
        build_protein_coverage_report,
    )

    report = build_protein_coverage_report(
        records,
        protein_sequences=protein_sequences,
    )
    peptide_sequences_by_protein: dict[str, set[str]] = defaultdict(set)
    for coordinate in report.peptide_coordinates:
        if coordinate.coordinate_status is ProteinCoverageCoordinateStatus.MATCHED:
            peptide_sequences_by_protein[coordinate.protein_ref].add(
                coordinate.peptide_sequence
            )

    return tuple(
        ProteinCoverageEntry(
            protein_ref=entry.protein_ref,
            residue_count=entry.residue_count,
            covered_residue_count=entry.covered_residue_count,
            coverage_fraction=entry.coverage_fraction,
            covered_ranges=entry.covered_ranges,
            covered_peptides=tuple(
                sorted(peptide_sequences_by_protein.get(entry.protein_ref, ()))
            ),
        )
        for entry in report.entries
    )


def build_peptide_uniqueness_across_database(
    peptides: tuple[str, ...],
    *,
    protein_sequences: dict[str, str] | None = None,
    protein_records: tuple[NormalizedProteinRecord, ...] | None = None,
    treat_isoleucine_as_leucine: bool = False,
) -> tuple[DatabasePeptideUniquenessEntry, ...]:
    """Classify peptide uniqueness by direct lookup across a provided database."""
    if protein_records is not None:
        index_report = build_peptide_uniqueness_index(
            protein_records,
            treat_isoleucine_as_leucine=treat_isoleucine_as_leucine,
        )
        index_by_sequence = {
            entry.lookup_sequence: entry for entry in index_report.entries
        }
        entries: list[DatabasePeptideUniquenessEntry] = []
        for peptide in sorted(dict.fromkeys(peptides)):
            lookup_sequence = peptide.replace("I", "L") if treat_isoleucine_as_leucine else peptide
            index_entry = index_by_sequence.get(lookup_sequence)
            if index_entry is None:
                entries.append(
                    DatabasePeptideUniquenessEntry(
                        canonical_peptide=peptide,
                        uniqueness=DatabasePeptideUniqueness.MISSING,
                    )
                )
                continue
            entries.append(
                DatabasePeptideUniquenessEntry(
                    canonical_peptide=peptide,
                    protein_refs=index_entry.protein_accessions,
                    protein_families=index_entry.protein_families,
                    gene_symbols=index_entry.gene_symbols,
                    uniqueness=DatabasePeptideUniqueness(
                        index_entry.uniqueness_class.value
                    ),
                )
            )
        return tuple(entries)
    if protein_sequences is None:
        raise ValueError(
            "provide either protein_sequences or protein_records for peptide uniqueness lookup"
        )
    entries: list[DatabasePeptideUniquenessEntry] = []
    for peptide in sorted(dict.fromkeys(peptides)):
        lookup_sequence = peptide.replace("I", "L") if treat_isoleucine_as_leucine else peptide
        matching_proteins = tuple(
            sorted(
                protein_ref
                for protein_ref, sequence in protein_sequences.items()
                if lookup_sequence in (
                    sequence.replace("I", "L")
                    if treat_isoleucine_as_leucine
                    else sequence
                )
            )
        )
        entries.append(
            DatabasePeptideUniquenessEntry(
                canonical_peptide=peptide,
                protein_refs=matching_proteins,
                uniqueness=(
                    DatabasePeptideUniqueness.UNIQUE
                    if len(matching_proteins) == 1
                    else DatabasePeptideUniqueness.SHARED
                    if len(matching_proteins) > 1
                    else DatabasePeptideUniqueness.MISSING
                ),
            )
        )
    return tuple(entries)


def calculate_picked_protein_fdr(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float | None = None,
    score_orientation: str = "higher_better",
    decoy_policy: TargetDecoyLabelPolicy | None = None,
) -> tuple[PickedProteinFdrEntry, ...]:
    """Calculate picked protein FDR by pairing targets and decoys with the same base accession."""
    from bijux_proteomics.identification.picked_protein_fdr import (
        build_picked_protein_fdr_report_from_psm_records,
    )

    report = build_picked_protein_fdr_report_from_psm_records(
        records,
        threshold=threshold,
        score_orientation=score_orientation,
        decoy_policy=decoy_policy,
    )
    return tuple(
        PickedProteinFdrEntry(
            protein_ref=entry.winner_ref,
            partner_ref=(
                entry.decoy_ref
                if entry.winner_target_decoy_label is TargetDecoyLabel.TARGET
                else entry.target_ref
            ),
            score=entry.winner_score,
            q_value=entry.q_value,
            fdr=entry.raw_fdr,
            rank=entry.rank,
            accepted=entry.accepted,
            target_decoy_label=entry.winner_target_decoy_label,
            supporting_peptides=entry.winner_supporting_peptides,
        )
        for entry in report.entries
    )

__all__ = [
    'CombinedEvidenceQuantSupport',
    'CombinedEvidenceEntry',
    'CombinedEvidenceReport',
    'PeptideProteinTraceEntry',
    'PeptideProteinTraceReport',
    'ProteinCoverageEntry',
    'DatabasePeptideUniqueness',
    'DatabasePeptideUniquenessEntry',
    'PickedProteinFdrEntry',
    'build_combined_evidence_report',
    'build_peptide_protein_trace_report',
    'export_peptide_protein_trace_jsonl',
    'export_peptide_protein_trace_tsv',
    'build_protein_coverage_map',
    'build_peptide_uniqueness_across_database',
    'calculate_picked_protein_fdr',
]
