# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Peptide uniqueness audit reports with explicit provenance classes."""

from __future__ import annotations

from collections.abc import Sequence
from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry import parse_modified_peptide
from bijux_proteomics.sequences.digestion import (
    PeptideDigestionMode,
    PeptideProteinIndexEntry,
    PeptideUniqueness,
    ProteaseRule,
    build_peptide_protein_index,
    digest_protein_records,
    get_protease_rule,
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
    records: Sequence[object],
    *,
    protease: ProteaseRule | str = "trypsin",
    missed_cleavages: int = 0,
    digestion_mode: PeptideDigestionMode = PeptideDigestionMode.FULL,
    treat_isoleucine_as_leucine: bool = False,
    protein_group_by_accession: dict[str, str] | None = None,
) -> PeptideDatabaseLookupReport:
    """Build one peptide-to-protein lookup report over a digested database."""
    protease_rule = get_protease_rule(protease) if isinstance(protease, str) else protease
    protein_group_by_accession = protein_group_by_accession or {}
    digested = digest_protein_records(
        tuple(records),
        protease=protease_rule,
        missed_cleavages=missed_cleavages,
        mode=digestion_mode,
    )
    normalized_peptides = tuple(
        peptide.model_copy(
            update={
                "sequence": _normalize_lookup_sequence(
                    peptide.sequence,
                    treat_isoleucine_as_leucine=treat_isoleucine_as_leucine,
                )
            }
        )
        for peptide in digested
    )
    peptide_index = build_peptide_protein_index(normalized_peptides)
    audit_report = build_peptide_uniqueness_audit_report(
        peptide_index,
        protein_group_by_accession=protein_group_by_accession,
    )
    audit_by_sequence = {entry.sequence: entry for entry in audit_report.entries}
    members_by_sequence: dict[str, list[object]] = {}
    for peptide in normalized_peptides:
        members_by_sequence.setdefault(peptide.sequence, []).append(peptide)
    record_flags_by_accession = {
        _stable_record_accession(record): (
            bool(getattr(record, "contaminant", False)),
            bool(getattr(record, "decoy", False)),
        )
        for record in records
    }

    entries: list[PeptideDatabaseLookupEntry] = []
    for input_peptide in dict.fromkeys(peptides):
        parsed = parse_modified_peptide(str(input_peptide))
        canonical_peptide = parsed.sequence
        lookup_sequence = _normalize_lookup_sequence(
            canonical_peptide,
            treat_isoleucine_as_leucine=treat_isoleucine_as_leucine,
        )
        audit_entry = audit_by_sequence.get(lookup_sequence)
        members = tuple(members_by_sequence.get(lookup_sequence, ()))
        membership = _classify_database_membership(
            members,
            record_flags_by_accession=record_flags_by_accession,
        )
        modification_stripped = bool(parsed.modifications)
        il_equivalence_applied = (
            treat_isoleucine_as_leucine and canonical_peptide != lookup_sequence
        )
        if audit_entry is None:
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
        entries.append(
            PeptideDatabaseLookupEntry(
                input_peptide=str(input_peptide),
                canonical_peptide=canonical_peptide,
                lookup_sequence=lookup_sequence,
                modification_stripped=modification_stripped,
                il_equivalence_applied=il_equivalence_applied,
                protein_accessions=audit_entry.protein_accessions,
                protein_families=audit_entry.protein_families,
                protein_groups=audit_entry.protein_groups,
                protein_group_count=len(audit_entry.protein_groups),
                uniqueness=audit_entry.uniqueness,
                audit_class=audit_entry.audit_class,
                database_membership=membership,
                missed_cleavage_counts=tuple(
                    sorted({member.missed_cleavages for member in members})
                ),
                explanation=_build_database_lookup_explanation(
                    audit_entry.explanation,
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


def _stable_record_accession(record: object) -> str:
    accession = str(getattr(record, "canonical_accession"))
    isoform = getattr(record, "isoform", None)
    if isinstance(isoform, int):
        return f"{accession}-{isoform}"
    return accession


def _normalize_lookup_sequence(
    sequence: str, *, treat_isoleucine_as_leucine: bool
) -> str:
    normalized = sequence.strip().upper()
    if treat_isoleucine_as_leucine:
        return normalized.replace("I", "L")
    return normalized


def _classify_database_membership(
    members: Sequence[object],
    *,
    record_flags_by_accession: dict[str, tuple[bool, bool]],
) -> PeptideDatabaseMembership:
    if not members:
        return PeptideDatabaseMembership.MISSING
    memberships: set[PeptideDatabaseMembership] = set()
    for member in members:
        contaminant, decoy = record_flags_by_accession.get(
            member.source_accession,
            (False, False),
        )
        if contaminant and decoy:
            memberships.update(
                {
                    PeptideDatabaseMembership.CONTAMINANT,
                    PeptideDatabaseMembership.DECOY,
                }
            )
        elif decoy:
            memberships.add(PeptideDatabaseMembership.DECOY)
        elif contaminant:
            memberships.add(PeptideDatabaseMembership.CONTAMINANT)
        else:
            memberships.add(PeptideDatabaseMembership.TARGET)
    if len(memberships) == 1:
        return next(iter(memberships))
    return PeptideDatabaseMembership.MIXED


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
        notes.append("modified query notation was reduced to the underlying residue sequence")
    if il_equivalence_applied:
        notes.append("I/L-equivalent lookup normalization was applied")
    return "; ".join(notes)
