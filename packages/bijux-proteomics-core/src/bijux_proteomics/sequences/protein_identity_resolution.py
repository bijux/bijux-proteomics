# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned peptide-backed protein identity resolution over protein sequences."""

from __future__ import annotations

import csv
from enum import StrEnum
import hashlib
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.sequences.fasta import (
    NormalizedProteinRecord,
    canonicalize_protein_reference,
    parse_uniprot_accession,
)
from bijux_proteomics_foundation import JsonModel


class ProteinIdentityLevel(StrEnum):
    """Stable identity-resolution levels for peptide-backed protein evidence."""

    GENE_LEVEL = "gene_level"
    FAMILY_LEVEL = "family_level"
    PROTEIN_LEVEL = "protein_level"
    ISOFORM_LEVEL = "isoform_level"
    AMBIGUOUS = "ambiguous"


class ProteinIdentityPeptideSupport(StrEnum):
    """Stable peptide-support classes used to resolve protein identity claims."""

    ISOFORM_SPECIFIC = "isoform_specific"
    PROTEIN_SPECIFIC = "protein_specific"
    ISOFORM_SHARED = "isoform_shared"
    GENE_SHARED = "gene_shared"
    FAMILY_SHARED = "family_shared"
    AMBIGUOUS = "ambiguous"
    UNMAPPED = "unmapped"


class ProteinIdentityReference(JsonModel):
    """One evidence item whose peptide support should resolve onto a protein identity."""

    model_config = ConfigDict(extra="forbid")

    evidence_key: str = Field(..., min_length=1)
    target_protein_ref: str = Field(..., min_length=1)
    candidate_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    peptide_sequences: tuple[str, ...] = Field(default_factory=tuple)


class ProteinIdentityPeptideEvidence(JsonModel):
    """One peptide with explicit identity-support classification and matched proteins."""

    model_config = ConfigDict(extra="forbid")

    peptide_sequence: str = Field(..., min_length=1)
    support_class: ProteinIdentityPeptideSupport
    matched_protein_accessions: tuple[str, ...] = Field(default_factory=tuple)
    matched_canonical_accessions: tuple[str, ...] = Field(default_factory=tuple)
    matched_gene_symbols: tuple[str, ...] = Field(default_factory=tuple)


class ProteinIdentityResolutionEntry(JsonModel):
    """One resolved protein-identity result over peptide evidence."""

    model_config = ConfigDict(extra="forbid")

    evidence_key: str = Field(..., min_length=1)
    target_protein_ref: str = Field(..., min_length=1)
    candidate_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    identity_level: ProteinIdentityLevel
    identity_reason: str = Field(..., min_length=1)
    peptide_evidence: tuple[ProteinIdentityPeptideEvidence, ...] = Field(
        default_factory=tuple
    )
    matched_protein_accessions: tuple[str, ...] = Field(default_factory=tuple)
    matched_canonical_accessions: tuple[str, ...] = Field(default_factory=tuple)
    matched_gene_symbols: tuple[str, ...] = Field(default_factory=tuple)


class ProteinIdentityResolutionSummary(JsonModel):
    """Stable summary over one protein-identity resolution pass."""

    model_config = ConfigDict(extra="forbid")

    evidence_count: int = Field(..., ge=0)
    isoform_level_count: int = Field(..., ge=0)
    protein_level_count: int = Field(..., ge=0)
    gene_level_count: int = Field(..., ge=0)
    family_level_count: int = Field(..., ge=0)
    ambiguous_count: int = Field(..., ge=0)


class ProteinIdentityResolutionReport(JsonModel):
    """Owned protein-identity resolution report over peptide-backed evidence."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[ProteinIdentityResolutionEntry, ...] = Field(default_factory=tuple)
    summary: ProteinIdentityResolutionSummary
    note: str = Field(..., min_length=1)


def build_protein_identity_resolution_report(
    references: tuple[ProteinIdentityReference, ...],
    *,
    protein_records: tuple[NormalizedProteinRecord, ...] = (),
    protein_sequences: dict[str, str] | None = None,
    treat_isoleucine_as_leucine: bool = False,
) -> ProteinIdentityResolutionReport:
    """Resolve peptide evidence onto gene, family, protein, or isoform identity levels."""

    records = _materialize_records(
        protein_records,
        protein_sequences=protein_sequences,
    )
    normalized_records = tuple(
        _RecordLookup(
            stable_accession=_stable_accession(record),
            canonical_accession=record.canonical_accession,
            gene_symbol=record.gene.strip() if record.gene else None,
            lookup_residues=_normalize_lookup_sequence(
                record.residues,
                treat_isoleucine_as_leucine=treat_isoleucine_as_leucine,
            ),
            isoform=record.isoform,
        )
        for record in records
    )

    entries = tuple(
        _resolve_identity_entry(
            reference,
            records=normalized_records,
            treat_isoleucine_as_leucine=treat_isoleucine_as_leucine,
        )
        for reference in references
    )
    return ProteinIdentityResolutionReport(
        entries=entries,
        summary=ProteinIdentityResolutionSummary(
            evidence_count=len(entries),
            isoform_level_count=sum(
                1
                for entry in entries
                if entry.identity_level is ProteinIdentityLevel.ISOFORM_LEVEL
            ),
            protein_level_count=sum(
                1
                for entry in entries
                if entry.identity_level is ProteinIdentityLevel.PROTEIN_LEVEL
            ),
            gene_level_count=sum(
                1
                for entry in entries
                if entry.identity_level is ProteinIdentityLevel.GENE_LEVEL
            ),
            family_level_count=sum(
                1
                for entry in entries
                if entry.identity_level is ProteinIdentityLevel.FAMILY_LEVEL
            ),
            ambiguous_count=sum(
                1
                for entry in entries
                if entry.identity_level is ProteinIdentityLevel.AMBIGUOUS
            ),
        ),
        note=(
            "protein identity resolution classifies peptide-backed evidence as exact isoform, "
            "canonical protein, gene-level, family-level, or ambiguous, and refuses exact "
            "isoform calls when the observed peptides do not isolate one isoform"
        ),
    )


def render_protein_identity_resolution_summary_tsv(
    report: ProteinIdentityResolutionReport,
) -> str:
    """Render compact protein-identity resolution summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    writer.writerow(("evidence_count", report.summary.evidence_count))
    writer.writerow(("isoform_level_count", report.summary.isoform_level_count))
    writer.writerow(("protein_level_count", report.summary.protein_level_count))
    writer.writerow(("gene_level_count", report.summary.gene_level_count))
    writer.writerow(("family_level_count", report.summary.family_level_count))
    writer.writerow(("ambiguous_count", report.summary.ambiguous_count))
    writer.writerow(("note", report.note))
    return buffer.getvalue()


def render_protein_identity_resolution_tsv(
    report: ProteinIdentityResolutionReport,
) -> str:
    """Render per-evidence protein identity resolution rows as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "evidence_key",
            "target_protein_ref",
            "candidate_protein_refs",
            "identity_level",
            "identity_reason",
            "matched_protein_accessions",
            "matched_canonical_accessions",
            "matched_gene_symbols",
            "peptide_evidence",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.evidence_key,
                entry.target_protein_ref,
                ";".join(entry.candidate_protein_refs),
                entry.identity_level.value,
                entry.identity_reason,
                ";".join(entry.matched_protein_accessions),
                ";".join(entry.matched_canonical_accessions),
                ";".join(entry.matched_gene_symbols),
                ";".join(
                    f"{peptide.peptide_sequence}:{peptide.support_class.value}"
                    for peptide in entry.peptide_evidence
                ),
            )
        )
    return buffer.getvalue()


def export_protein_identity_resolution_tsv(
    report: ProteinIdentityResolutionReport,
    path: Path,
) -> Path:
    """Write per-evidence protein identity resolution rows as TSV."""

    write_output_table_tsv(path, render_protein_identity_resolution_tsv(report))
    return path


class _RecordLookup(JsonModel):
    model_config = ConfigDict(extra="forbid")

    stable_accession: str
    canonical_accession: str
    gene_symbol: str | None = None
    lookup_residues: str
    isoform: int | None = None


def _resolve_identity_entry(
    reference: ProteinIdentityReference,
    *,
    records: tuple[_RecordLookup, ...],
    treat_isoleucine_as_leucine: bool,
) -> ProteinIdentityResolutionEntry:
    peptide_evidence = tuple(
        _build_peptide_identity_evidence(
            peptide_sequence,
            records=records,
            treat_isoleucine_as_leucine=treat_isoleucine_as_leucine,
        )
        for peptide_sequence in tuple(dict.fromkeys(reference.peptide_sequences))
    )
    identity_level, identity_reason = _resolve_identity_level(
        reference,
        peptide_evidence=peptide_evidence,
    )
    return ProteinIdentityResolutionEntry(
        evidence_key=reference.evidence_key,
        target_protein_ref=reference.target_protein_ref,
        candidate_protein_refs=(
            reference.candidate_protein_refs or (reference.target_protein_ref,)
        ),
        identity_level=identity_level,
        identity_reason=identity_reason,
        peptide_evidence=peptide_evidence,
        matched_protein_accessions=tuple(
            sorted(
                {
                    accession
                    for peptide in peptide_evidence
                    for accession in peptide.matched_protein_accessions
                }
            )
        ),
        matched_canonical_accessions=tuple(
            sorted(
                {
                    accession
                    for peptide in peptide_evidence
                    for accession in peptide.matched_canonical_accessions
                }
            )
        ),
        matched_gene_symbols=tuple(
            sorted(
                {
                    gene
                    for peptide in peptide_evidence
                    for gene in peptide.matched_gene_symbols
                }
            )
        ),
    )


def _build_peptide_identity_evidence(
    peptide_sequence: str,
    *,
    records: tuple[_RecordLookup, ...],
    treat_isoleucine_as_leucine: bool,
) -> ProteinIdentityPeptideEvidence:
    normalized_peptide = peptide_sequence.strip().upper()
    lookup_sequence = _normalize_lookup_sequence(
        normalized_peptide,
        treat_isoleucine_as_leucine=treat_isoleucine_as_leucine,
    )
    matches = tuple(
        record
        for record in records
        if lookup_sequence and lookup_sequence in record.lookup_residues
    )
    accessions = tuple(sorted({record.stable_accession for record in matches}))
    canonical_accessions = tuple(
        sorted({record.canonical_accession for record in matches})
    )
    genes = tuple(
        sorted(
            {
                record.gene_symbol
                for record in matches
                if record.gene_symbol is not None and record.gene_symbol != ""
            }
        )
    )
    return ProteinIdentityPeptideEvidence(
        peptide_sequence=normalized_peptide,
        support_class=_classify_peptide_support(
            accessions=accessions,
            canonical_accessions=canonical_accessions,
            genes=genes,
            matches=matches,
        ),
        matched_protein_accessions=accessions,
        matched_canonical_accessions=canonical_accessions,
        matched_gene_symbols=genes,
    )


def _classify_peptide_support(
    *,
    accessions: tuple[str, ...],
    canonical_accessions: tuple[str, ...],
    genes: tuple[str, ...],
    matches: tuple[_RecordLookup, ...],
) -> ProteinIdentityPeptideSupport:
    if not matches:
        return ProteinIdentityPeptideSupport.UNMAPPED
    if len(accessions) == 1:
        return (
            ProteinIdentityPeptideSupport.ISOFORM_SPECIFIC
            if matches[0].isoform is not None
            else ProteinIdentityPeptideSupport.PROTEIN_SPECIFIC
        )
    if len(canonical_accessions) == 1:
        return ProteinIdentityPeptideSupport.ISOFORM_SHARED
    if len(genes) == 1:
        return ProteinIdentityPeptideSupport.GENE_SHARED
    if len(canonical_accessions) > 1 and not genes:
        return ProteinIdentityPeptideSupport.FAMILY_SHARED
    return ProteinIdentityPeptideSupport.AMBIGUOUS


def _resolve_identity_level(
    reference: ProteinIdentityReference,
    *,
    peptide_evidence: tuple[ProteinIdentityPeptideEvidence, ...],
) -> tuple[ProteinIdentityLevel, str]:
    target_protein_ref = reference.target_protein_ref.strip().upper()
    target_canonical_accession = _canonical_protein_ref(target_protein_ref)
    mapped_evidence = tuple(
        evidence
        for evidence in peptide_evidence
        if evidence.support_class is not ProteinIdentityPeptideSupport.UNMAPPED
    )
    if not mapped_evidence:
        return (
            ProteinIdentityLevel.AMBIGUOUS,
            "no observed peptide matched the provided protein sequences",
        )

    has_exact_isoform_support = any(
        evidence.support_class is ProteinIdentityPeptideSupport.ISOFORM_SPECIFIC
        and target_protein_ref in evidence.matched_protein_accessions
        for evidence in mapped_evidence
    )
    if has_exact_isoform_support:
        return (
            ProteinIdentityLevel.ISOFORM_LEVEL,
            "at least one observed peptide uniquely matches the exact target isoform",
        )

    all_within_target_canonical = all(
        set(evidence.matched_canonical_accessions) <= {target_canonical_accession}
        for evidence in mapped_evidence
    )
    has_target_protein_support = any(
        evidence.support_class
        in {
            ProteinIdentityPeptideSupport.ISOFORM_SPECIFIC,
            ProteinIdentityPeptideSupport.PROTEIN_SPECIFIC,
        }
        and target_canonical_accession in evidence.matched_canonical_accessions
        for evidence in mapped_evidence
    )
    if has_target_protein_support:
        return (
            ProteinIdentityLevel.PROTEIN_LEVEL,
            "at least one observed peptide uniquely matches the target canonical accession, even though other peptides may remain shared",
        )

    has_target_isoform_shared_support = any(
        evidence.support_class is ProteinIdentityPeptideSupport.ISOFORM_SHARED
        and set(evidence.matched_canonical_accessions) == {target_canonical_accession}
        for evidence in mapped_evidence
    )
    if all_within_target_canonical and has_target_isoform_shared_support:
        return (
            ProteinIdentityLevel.PROTEIN_LEVEL,
            "observed peptides stay within one canonical accession family but do not isolate one exact isoform",
        )

    matched_gene_symbols = {
        gene for evidence in mapped_evidence for gene in evidence.matched_gene_symbols
    }
    if len(matched_gene_symbols) == 1:
        return (
            ProteinIdentityLevel.GENE_LEVEL,
            "observed peptides resolve to one gene but remain shared across multiple canonical accessions",
        )

    matched_canonical_accessions = {
        accession
        for evidence in mapped_evidence
        for accession in evidence.matched_canonical_accessions
    }
    if len(matched_canonical_accessions) > 1 and not matched_gene_symbols:
        return (
            ProteinIdentityLevel.FAMILY_LEVEL,
            "observed peptides stay inside one unresolved accession family without gene-level separation",
        )

    return (
        ProteinIdentityLevel.AMBIGUOUS,
        "observed peptides span multiple competing proteins or genes and do not justify an exact identity call",
    )


def _materialize_records(
    protein_records: tuple[NormalizedProteinRecord, ...],
    *,
    protein_sequences: dict[str, str] | None,
) -> tuple[NormalizedProteinRecord, ...]:
    by_accession = {_stable_accession(record): record for record in protein_records}
    if protein_sequences:
        for protein_ref, residues in protein_sequences.items():
            stable_accession = _stable_protein_ref(protein_ref)
            if stable_accession in by_accession:
                continue
            by_accession[stable_accession] = _build_synthetic_record(
                protein_ref,
                residues,
            )
    return tuple(sorted(by_accession.values(), key=_stable_accession))


def _build_synthetic_record(
    protein_ref: str,
    residues: str,
) -> NormalizedProteinRecord:
    stable_ref = _stable_protein_ref(protein_ref)
    accession_namespace = "custom"
    canonical_accession = stable_ref
    isoform = None
    try:
        accession = parse_uniprot_accession(stable_ref)
    except ValueError:
        try:
            canonical_accession = canonicalize_protein_reference(stable_ref)
        except ValueError:
            canonical_accession = stable_ref
    else:
        accession_namespace = "uniprot"
        canonical_accession = accession.accession
        isoform = accession.isoform
    normalized_residues = residues.strip().upper()
    return NormalizedProteinRecord(
        source_header=stable_ref,
        source_identifier=stable_ref,
        accession_namespace=accession_namespace,
        canonical_accession=canonical_accession,
        isoform=isoform,
        display_name=stable_ref,
        residues=normalized_residues,
        residue_count=len(normalized_residues),
        sequence_checksum=hashlib.sha256(
            normalized_residues.encode("utf-8")
        ).hexdigest(),
    )


def _stable_accession(record: NormalizedProteinRecord) -> str:
    if isinstance(record.isoform, int):
        return f"{record.canonical_accession}-{record.isoform}"
    return record.canonical_accession


def _stable_protein_ref(value: str) -> str:
    return value.strip().upper()


def _canonical_protein_ref(value: str) -> str:
    try:
        return canonicalize_protein_reference(value)
    except ValueError:
        token = _stable_protein_ref(value)
        if "-" in token:
            return token.split("-", 1)[0]
        return token


def _normalize_lookup_sequence(
    sequence: str,
    *,
    treat_isoleucine_as_leucine: bool,
) -> str:
    normalized = sequence.strip().upper()
    if treat_isoleucine_as_leucine:
        return normalized.replace("I", "L")
    return normalized


__all__ = (
    "ProteinIdentityLevel",
    "ProteinIdentityPeptideEvidence",
    "ProteinIdentityPeptideSupport",
    "ProteinIdentityReference",
    "ProteinIdentityResolutionEntry",
    "ProteinIdentityResolutionReport",
    "ProteinIdentityResolutionSummary",
    "build_protein_identity_resolution_report",
    "export_protein_identity_resolution_tsv",
    "render_protein_identity_resolution_summary_tsv",
    "render_protein_identity_resolution_tsv",
)
