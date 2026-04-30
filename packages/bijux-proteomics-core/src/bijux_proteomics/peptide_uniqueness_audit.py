# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Peptide uniqueness audit reports with explicit provenance classes."""

from __future__ import annotations

from collections.abc import Sequence
from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.digestion import PeptideProteinIndexEntry, PeptideUniqueness
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
        elif (
            entry.uniqueness is PeptideUniqueness.SHARED_ISOFORM_FAMILY
            or (len(entry.protein_families) == 1 and len(entry.protein_accessions) > 1)
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
