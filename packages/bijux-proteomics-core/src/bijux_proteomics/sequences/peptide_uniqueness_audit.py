# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Peptide uniqueness audit reports with explicit provenance classes."""

from __future__ import annotations

from collections.abc import Sequence
from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry import parse_modified_peptide
from bijux_proteomics.sequences.fasta import NormalizedProteinRecord
from bijux_proteomics.sequences.digestion import (
    PeptideDigestionMode,
    PeptideProteinIndexEntry,
    PeptideUniqueness,
    ProteaseRule,
)
from bijux_proteomics.sequences.peptide_uniqueness_index import (
    PeptideUniquenessClass,
    PeptideUniquenessIndexEntry,
    build_peptide_uniqueness_index,
)
from bijux_proteomics_foundation import JsonModel


class PeptideUniquenessAuditClass(StrEnum):
    """Audit class over peptide uniqueness interpretation."""

    UNIQUE = "unique"
    SHARED = "shared"
    ISOFORM_SPECIFIC = "isoform_specific"
    PROTEIN_GROUP_SPECIFIC = "protein_group_specific"


class PeptideUniquenessAuditEntry(JsonModel):
    """One peptide uniqueness audit decision."""

    model_config = ConfigDict(extra="forbid")

    sequence: str = Field(..., min_length=1)
    audit_class: PeptideUniquenessAuditClass
    uniqueness: PeptideUniqueness
    protein_accessions: tuple[str, ...] = Field(default_factory=tuple)
    protein_families: tuple[str, ...] = Field(default_factory=tuple)
    protein_groups: tuple[str, ...] = Field(default_factory=tuple)
    explanation: str = Field(..., min_length=1)


class PeptideUniquenessAuditReport(JsonModel):
    """Stable report for unique/shared/isoform/group-specific peptide evidence."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[PeptideUniquenessAuditEntry, ...] = Field(default_factory=tuple)
    unique_count: int = Field(..., ge=0)
    shared_count: int = Field(..., ge=0)
    isoform_specific_count: int = Field(..., ge=0)
    protein_group_specific_count: int = Field(..., ge=0)


class PeptideDatabaseMembership(StrEnum):
    """Database membership class for one indexed peptide query."""

    TARGET = "target"
    DECOY = "decoy"
    CONTAMINANT = "contaminant"
    MIXED = "mixed"
    MISSING = "missing"


class PeptideDatabaseLookupEntry(JsonModel):
    """One peptide lookup entry over a digested protein database."""

    model_config = ConfigDict(extra="forbid")

    input_peptide: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    lookup_sequence: str = Field(..., min_length=1)
    modification_stripped: bool = False
    il_equivalence_applied: bool = False
    protein_accessions: tuple[str, ...] = Field(default_factory=tuple)
    protein_families: tuple[str, ...] = Field(default_factory=tuple)
    protein_groups: tuple[str, ...] = Field(default_factory=tuple)
    protein_group_count: int = Field(..., ge=0)
    uniqueness_class: PeptideUniquenessClass | None = None
    uniqueness: PeptideUniqueness | None = None
    audit_class: PeptideUniquenessAuditClass | None = None
    database_membership: PeptideDatabaseMembership
    missed_cleavage_counts: tuple[int, ...] = Field(default_factory=tuple)
    explanation: str = Field(..., min_length=1)


class PeptideDatabaseLookupReport(JsonModel):
    """Stable peptide lookup report over a digested protein database."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[PeptideDatabaseLookupEntry, ...] = Field(default_factory=tuple)
    input_peptide_count: int = Field(..., ge=0)
    matched_count: int = Field(..., ge=0)
    missing_count: int = Field(..., ge=0)
    unique_count: int = Field(..., ge=0)
    shared_count: int = Field(..., ge=0)
    isoform_specific_count: int = Field(..., ge=0)
    protein_group_specific_count: int = Field(..., ge=0)
    target_count: int = Field(..., ge=0)
    decoy_count: int = Field(..., ge=0)
    contaminant_count: int = Field(..., ge=0)
    mixed_count: int = Field(..., ge=0)


def build_peptide_uniqueness_audit_report(
    entries: Sequence[PeptideProteinIndexEntry],
    *,
    protein_group_by_accession: dict[str, str] | None = None,
) -> PeptideUniquenessAuditReport:
    """Build a peptide uniqueness audit report with explicit class explanations."""
    protein_group_by_accession = protein_group_by_accession or {}
    audited: list[PeptideUniquenessAuditEntry] = []
    for entry in entries:
        groups = tuple(
            sorted(
                {
                    protein_group_by_accession[accession]
                    for accession in entry.protein_accessions
                    if accession in protein_group_by_accession
                }
            )
        )
        if len(groups) == 1 and len(entry.protein_accessions) > 1:
            audit_class = PeptideUniquenessAuditClass.PROTEIN_GROUP_SPECIFIC
            explanation = (
                "peptide maps to multiple proteins that collapse into one protein group"
            )
        elif entry.uniqueness is PeptideUniqueness.SHARED_ISOFORM_FAMILY or (
            len(entry.protein_families) == 1 and len(entry.protein_accessions) > 1
        ):
            audit_class = PeptideUniquenessAuditClass.ISOFORM_SPECIFIC
            explanation = "peptide is shared across isoforms within one protein family"
        elif entry.uniqueness is PeptideUniqueness.UNIQUE:
            audit_class = PeptideUniquenessAuditClass.UNIQUE
            explanation = "peptide maps to a single protein accession"
        else:
            audit_class = PeptideUniquenessAuditClass.SHARED
            explanation = "peptide is shared across protein accessions or families"
        audited.append(
            PeptideUniquenessAuditEntry(
                sequence=entry.sequence,
                audit_class=audit_class,
                uniqueness=entry.uniqueness,
                protein_accessions=entry.protein_accessions,
                protein_families=entry.protein_families,
                protein_groups=groups,
                explanation=explanation,
            )
        )
    return PeptideUniquenessAuditReport(
        entries=tuple(audited),
        unique_count=sum(
            1
            for entry in audited
            if entry.audit_class is PeptideUniquenessAuditClass.UNIQUE
        ),
        shared_count=sum(
            1
            for entry in audited
            if entry.audit_class is PeptideUniquenessAuditClass.SHARED
        ),
        isoform_specific_count=sum(
            1
            for entry in audited
            if entry.audit_class is PeptideUniquenessAuditClass.ISOFORM_SPECIFIC
        ),
        protein_group_specific_count=sum(
            1
            for entry in audited
            if entry.audit_class is PeptideUniquenessAuditClass.PROTEIN_GROUP_SPECIFIC
        ),
    )


def build_peptide_database_lookup_report(
    peptides: Sequence[str],
    records: Sequence[NormalizedProteinRecord],
    *,
    protease: ProteaseRule | str = "trypsin",
    missed_cleavages: int = 0,
    digestion_mode: PeptideDigestionMode = PeptideDigestionMode.FULL,
    treat_isoleucine_as_leucine: bool = False,
    protein_group_by_accession: dict[str, str] | None = None,
) -> PeptideDatabaseLookupReport:
    """Build one peptide-to-protein lookup report over a digested database."""
    protein_group_by_accession = protein_group_by_accession or {}
    index_report = build_peptide_uniqueness_index(
        tuple(records),
        protease=protease,
        missed_cleavages=missed_cleavages,
        digestion_mode=digestion_mode,
        treat_isoleucine_as_leucine=treat_isoleucine_as_leucine,
    )
    index_by_sequence = {entry.lookup_sequence: entry for entry in index_report.entries}

    entries: list[PeptideDatabaseLookupEntry] = []
    for input_peptide in dict.fromkeys(peptides):
        parsed = parse_modified_peptide(str(input_peptide))
        canonical_peptide = parsed.sequence
        lookup_sequence = _normalize_lookup_sequence(
            canonical_peptide,
            treat_isoleucine_as_leucine=treat_isoleucine_as_leucine,
        )
        index_entry = index_by_sequence.get(lookup_sequence)
        modification_stripped = bool(parsed.modifications)
        il_equivalence_applied = (
            treat_isoleucine_as_leucine and canonical_peptide != lookup_sequence
        )
        if index_entry is None:
            entries.append(
                PeptideDatabaseLookupEntry(
                    input_peptide=str(input_peptide),
                    canonical_peptide=canonical_peptide,
                    lookup_sequence=lookup_sequence,
                    modification_stripped=modification_stripped,
                    il_equivalence_applied=il_equivalence_applied,
                    protein_group_count=0,
                    database_membership=PeptideDatabaseMembership.MISSING,
                    explanation=(
                        "peptide is absent from the digested database under the current"
                        " digestion and lookup settings"
                    ),
                )
            )
            continue
        protein_groups = tuple(
            sorted(
                {
                    protein_group_by_accession[accession]
                    for accession in index_entry.protein_accessions
                    if accession in protein_group_by_accession
                }
            )
        )
        audit_class, explanation = _build_audit_interpretation(
            index_entry,
            protein_groups=protein_groups,
        )
        membership = _database_membership_from_uniqueness_class(
            index_entry.uniqueness_class
        )
        entries.append(
            PeptideDatabaseLookupEntry(
                input_peptide=str(input_peptide),
                canonical_peptide=canonical_peptide,
                lookup_sequence=lookup_sequence,
                modification_stripped=modification_stripped,
                il_equivalence_applied=il_equivalence_applied,
                protein_accessions=index_entry.protein_accessions,
                protein_families=index_entry.protein_families,
                protein_groups=protein_groups,
                protein_group_count=len(protein_groups),
                uniqueness_class=index_entry.uniqueness_class,
                uniqueness=_legacy_uniqueness_from_index_entry(index_entry),
                audit_class=audit_class,
                database_membership=membership,
                missed_cleavage_counts=index_entry.missed_cleavage_counts,
                explanation=_build_database_lookup_explanation(
                    explanation,
                    membership=membership,
                    modification_stripped=modification_stripped,
                    il_equivalence_applied=il_equivalence_applied,
                ),
            )
        )
    return PeptideDatabaseLookupReport(
        entries=tuple(entries),
        input_peptide_count=len(tuple(peptides)),
        matched_count=sum(
            1
            for entry in entries
            if entry.database_membership is not PeptideDatabaseMembership.MISSING
        ),
        missing_count=sum(
            1
            for entry in entries
            if entry.database_membership is PeptideDatabaseMembership.MISSING
        ),
        unique_count=sum(
            1
            for entry in entries
            if entry.audit_class is PeptideUniquenessAuditClass.UNIQUE
        ),
        shared_count=sum(
            1
            for entry in entries
            if entry.audit_class is PeptideUniquenessAuditClass.SHARED
        ),
        isoform_specific_count=sum(
            1
            for entry in entries
            if entry.audit_class is PeptideUniquenessAuditClass.ISOFORM_SPECIFIC
        ),
        protein_group_specific_count=sum(
            1
            for entry in entries
            if entry.audit_class is PeptideUniquenessAuditClass.PROTEIN_GROUP_SPECIFIC
        ),
        target_count=sum(
            1
            for entry in entries
            if entry.database_membership is PeptideDatabaseMembership.TARGET
        ),
        decoy_count=sum(
            1
            for entry in entries
            if entry.database_membership is PeptideDatabaseMembership.DECOY
        ),
        contaminant_count=sum(
            1
            for entry in entries
            if entry.database_membership is PeptideDatabaseMembership.CONTAMINANT
        ),
        mixed_count=sum(
            1
            for entry in entries
            if entry.database_membership is PeptideDatabaseMembership.MIXED
        ),
    )


def _normalize_lookup_sequence(
    sequence: str, *, treat_isoleucine_as_leucine: bool
) -> str:
    normalized = sequence.strip().upper()
    if treat_isoleucine_as_leucine:
        return normalized.replace("I", "L")
    return normalized


def _database_membership_from_uniqueness_class(
    uniqueness_class: PeptideUniquenessClass,
) -> PeptideDatabaseMembership:
    if uniqueness_class is PeptideUniquenessClass.CONTAMINANT:
        return PeptideDatabaseMembership.CONTAMINANT
    if uniqueness_class is PeptideUniquenessClass.DECOY:
        return PeptideDatabaseMembership.DECOY
    if uniqueness_class is PeptideUniquenessClass.MIXED:
        return PeptideDatabaseMembership.MIXED
    return PeptideDatabaseMembership.TARGET


def _build_audit_interpretation(
    entry: PeptideUniquenessIndexEntry,
    *,
    protein_groups: tuple[str, ...],
) -> tuple[PeptideUniquenessAuditClass, str]:
    if len(protein_groups) == 1 and len(entry.protein_accessions) > 1:
        return (
            PeptideUniquenessAuditClass.PROTEIN_GROUP_SPECIFIC,
            "peptide maps to multiple proteins that collapse into one protein group",
        )
    if entry.uniqueness_class is PeptideUniquenessClass.UNIQUE:
        return (
            PeptideUniquenessAuditClass.UNIQUE,
            "peptide maps to a single protein accession",
        )
    if entry.uniqueness_class is PeptideUniquenessClass.ISOFORM_SHARED:
        return (
            PeptideUniquenessAuditClass.ISOFORM_SPECIFIC,
            "peptide is shared across isoforms within one protein family",
        )
    if entry.uniqueness_class is PeptideUniquenessClass.FAMILY_SHARED:
        return (
            PeptideUniquenessAuditClass.SHARED,
            "peptide is shared across proteins within one annotated gene family",
        )
    if entry.uniqueness_class is PeptideUniquenessClass.CONTAMINANT:
        return (
            PeptideUniquenessAuditClass.SHARED,
            "peptide maps only to contaminant proteins in the indexed database",
        )
    if entry.uniqueness_class is PeptideUniquenessClass.DECOY:
        return (
            PeptideUniquenessAuditClass.SHARED,
            "peptide maps only to decoy proteins in the indexed database",
        )
    if entry.uniqueness_class is PeptideUniquenessClass.MIXED:
        return (
            PeptideUniquenessAuditClass.SHARED,
            "peptide spans target, decoy, or contaminant protein classes",
        )
    return (
        PeptideUniquenessAuditClass.SHARED,
        "peptide is shared across protein accessions or families",
    )


def _legacy_uniqueness_from_index_entry(
    entry: PeptideUniquenessIndexEntry,
) -> PeptideUniqueness:
    if entry.uniqueness_class is PeptideUniquenessClass.UNIQUE:
        return PeptideUniqueness.UNIQUE
    if entry.uniqueness_class is PeptideUniquenessClass.ISOFORM_SHARED:
        return PeptideUniqueness.SHARED_ISOFORM_FAMILY
    return PeptideUniqueness.SHARED


def _build_database_lookup_explanation(
    base_explanation: str,
    *,
    membership: PeptideDatabaseMembership,
    modification_stripped: bool,
    il_equivalence_applied: bool,
) -> str:
    notes = [base_explanation]
    if membership is PeptideDatabaseMembership.DECOY:
        notes.append("matches arise only from decoy proteins")
    elif membership is PeptideDatabaseMembership.CONTAMINANT:
        notes.append("matches arise only from contaminant proteins")
    elif membership is PeptideDatabaseMembership.MIXED:
        notes.append("matches span target, decoy, or contaminant classes")
    if modification_stripped:
        notes.append(
            "modified query notation was reduced to the underlying residue sequence"
        )
    if il_equivalence_applied:
        notes.append("I/L-equivalent lookup normalization was applied")
    return "; ".join(notes)
