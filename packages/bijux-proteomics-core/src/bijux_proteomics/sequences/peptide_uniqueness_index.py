# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Peptide-to-protein uniqueness indexing over governed FASTA digests."""

from __future__ import annotations

from collections.abc import Sequence
from enum import StrEnum
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics._tabular import render_rows_tsv
from bijux_proteomics.sequences.core import NormalizedProteinRecord
from bijux_proteomics.sequences.digestion import (
    DigestedPeptide,
    DigestPolicy,
    PeptideDigestionMode,
    PeptideOriginCoordinate,
    ProteaseRule,
    build_digest_policy,
    digest_protein_records,
    get_protease_rule,
)
from bijux_proteomics_foundation import JsonModel


class PeptideUniquenessClass(StrEnum):
    """Stable peptide uniqueness classes for database-scale interpretation."""

    UNIQUE = "unique"
    SHARED = "shared"
    ISOFORM_SHARED = "isoform_shared"
    FAMILY_SHARED = "family_shared"
    CONTAMINANT = "contaminant"
    DECOY = "decoy"
    MIXED = "mixed"


class PeptideUniquenessIndexEntry(JsonModel):
    """One indexed peptide row with full parent-protein provenance."""

    model_config = ConfigDict(extra="forbid")

    peptide_sequence: str = Field(..., min_length=1)
    lookup_sequence: str = Field(..., min_length=1)
    source_sequences: tuple[str, ...] = Field(default_factory=tuple)
    protein_accessions: tuple[str, ...] = Field(default_factory=tuple)
    protein_families: tuple[str, ...] = Field(default_factory=tuple)
    gene_symbols: tuple[str, ...] = Field(default_factory=tuple)
    source_identifiers: tuple[str, ...] = Field(default_factory=tuple)
    coordinates: tuple[PeptideOriginCoordinate, ...] = Field(default_factory=tuple)
    missed_cleavage_counts: tuple[int, ...] = Field(default_factory=tuple)
    uniqueness_class: PeptideUniquenessClass


class PeptideUniquenessIndexSummary(JsonModel):
    """Stable summary accounting for one peptide uniqueness index."""

    model_config = ConfigDict(extra="forbid")

    input_record_count: int = Field(..., ge=0)
    entry_count: int = Field(..., ge=0)
    il_equivalence_applied: bool = False
    unique_count: int = Field(..., ge=0)
    shared_count: int = Field(..., ge=0)
    isoform_shared_count: int = Field(..., ge=0)
    family_shared_count: int = Field(..., ge=0)
    contaminant_count: int = Field(..., ge=0)
    decoy_count: int = Field(..., ge=0)
    mixed_count: int = Field(..., ge=0)


class PeptideUniquenessIndexReport(JsonModel):
    """Stable peptide uniqueness index over a governed digested database."""

    model_config = ConfigDict(extra="forbid")

    digest_policy: DigestPolicy
    entries: tuple[PeptideUniquenessIndexEntry, ...] = Field(default_factory=tuple)
    summary: PeptideUniquenessIndexSummary


def build_peptide_uniqueness_index(
    records: Sequence[NormalizedProteinRecord],
    *,
    protease: ProteaseRule | str = "trypsin",
    missed_cleavages: int = 0,
    digestion_mode: PeptideDigestionMode = PeptideDigestionMode.FULL,
    treat_isoleucine_as_leucine: bool = False,
) -> PeptideUniquenessIndexReport:
    """Build a peptide uniqueness index over a governed protein database."""
    normalized_records = tuple(records)
    protease_rule = (
        get_protease_rule(protease) if isinstance(protease, str) else protease
    )
    digested = digest_protein_records(
        normalized_records,
        protease=protease_rule,
        missed_cleavages=missed_cleavages,
        mode=digestion_mode,
    )
    record_by_accession = {
        _stable_record_accession(record): record for record in normalized_records
    }
    grouped: dict[str, list[DigestedPeptide]] = {}
    for peptide in digested:
        grouped.setdefault(
            _normalize_lookup_sequence(
                peptide.sequence,
                treat_isoleucine_as_leucine=treat_isoleucine_as_leucine,
            ),
            [],
        ).append(peptide)

    entries: list[PeptideUniquenessIndexEntry] = []
    for lookup_sequence, members in sorted(grouped.items()):
        source_sequences = tuple(sorted({member.sequence for member in members}))
        coordinate_keys = sorted(
            {
                (
                    member.source_accession,
                    member.source_protein_family,
                    member.source_identifier,
                    member.start,
                    member.end,
                    member.source_isoform,
                )
                for member in members
            }
        )
        coordinates = tuple(
            PeptideOriginCoordinate(
                protein_accession=accession,
                protein_family=protein_family,
                source_identifier=source_identifier,
                start=start,
                end=end,
                isoform=isoform,
            )
            for accession, protein_family, source_identifier, start, end, isoform in coordinate_keys
        )
        accessions = tuple(sorted({member.source_accession for member in members}))
        families = tuple(sorted({member.source_protein_family for member in members}))
        identifiers = tuple(sorted({member.source_identifier for member in members}))
        gene_symbols = tuple(
            sorted(
                {
                    record.gene.strip()
                    for accession in accessions
                    for record in (record_by_accession.get(accession),)
                    if record is not None
                    and record.gene is not None
                    and record.gene.strip() != ""
                }
            )
        )
        entries.append(
            PeptideUniquenessIndexEntry(
                peptide_sequence=source_sequences[0],
                lookup_sequence=lookup_sequence,
                source_sequences=source_sequences,
                protein_accessions=accessions,
                protein_families=families,
                gene_symbols=gene_symbols,
                source_identifiers=identifiers,
                coordinates=coordinates,
                missed_cleavage_counts=tuple(
                    sorted({member.missed_cleavages for member in members})
                ),
                uniqueness_class=_classify_peptide_uniqueness_class(
                    members,
                    record_by_accession=record_by_accession,
                    gene_symbols=gene_symbols,
                ),
            )
        )

    return PeptideUniquenessIndexReport(
        digest_policy=build_digest_policy(
            protease=protease_rule,
            digestion_mode=digestion_mode,
            missed_cleavages=missed_cleavages,
            min_length=None,
            max_length=None,
            min_mass=None,
            max_mass=None,
        ),
        entries=tuple(entries),
        summary=PeptideUniquenessIndexSummary(
            input_record_count=len(normalized_records),
            entry_count=len(entries),
            il_equivalence_applied=treat_isoleucine_as_leucine,
            unique_count=sum(
                1
                for entry in entries
                if entry.uniqueness_class is PeptideUniquenessClass.UNIQUE
            ),
            shared_count=sum(
                1
                for entry in entries
                if entry.uniqueness_class is PeptideUniquenessClass.SHARED
            ),
            isoform_shared_count=sum(
                1
                for entry in entries
                if entry.uniqueness_class is PeptideUniquenessClass.ISOFORM_SHARED
            ),
            family_shared_count=sum(
                1
                for entry in entries
                if entry.uniqueness_class is PeptideUniquenessClass.FAMILY_SHARED
            ),
            contaminant_count=sum(
                1
                for entry in entries
                if entry.uniqueness_class is PeptideUniquenessClass.CONTAMINANT
            ),
            decoy_count=sum(
                1
                for entry in entries
                if entry.uniqueness_class is PeptideUniquenessClass.DECOY
            ),
            mixed_count=sum(
                1
                for entry in entries
                if entry.uniqueness_class is PeptideUniquenessClass.MIXED
            ),
        ),
    )


def render_peptide_uniqueness_index_tsv(
    report: PeptideUniquenessIndexReport,
) -> str:
    """Render a stable TSV export for a peptide uniqueness index."""
    return render_rows_tsv(
        fieldnames=(
            "peptide_sequence",
            "lookup_sequence",
            "source_sequences",
            "protein_accessions",
            "protein_families",
            "gene_symbols",
            "source_identifiers",
            "missed_cleavage_counts",
            "uniqueness_class",
        ),
        rows=tuple(
            {
                "peptide_sequence": entry.peptide_sequence,
                "lookup_sequence": entry.lookup_sequence,
                "source_sequences": ";".join(entry.source_sequences),
                "protein_accessions": ";".join(entry.protein_accessions),
                "protein_families": ";".join(entry.protein_families),
                "gene_symbols": ";".join(entry.gene_symbols),
                "source_identifiers": ";".join(entry.source_identifiers),
                "missed_cleavage_counts": ";".join(
                    str(count) for count in entry.missed_cleavage_counts
                ),
                "uniqueness_class": entry.uniqueness_class.value,
            }
            for entry in report.entries
        ),
    )


def export_peptide_uniqueness_index_tsv(
    report: PeptideUniquenessIndexReport, path: Path
) -> Path:
    """Write a stable TSV export for a peptide uniqueness index."""
    write_output_table_tsv(path, render_peptide_uniqueness_index_tsv(report))
    return path


def _stable_record_accession(record: NormalizedProteinRecord) -> str:
    if isinstance(record.isoform, int):
        return f"{record.canonical_accession}-{record.isoform}"
    return record.canonical_accession


def _normalize_lookup_sequence(
    sequence: str, *, treat_isoleucine_as_leucine: bool
) -> str:
    normalized = sequence.strip().upper()
    if treat_isoleucine_as_leucine:
        return normalized.replace("I", "L")
    return normalized


def _classify_peptide_uniqueness_class(
    members: Sequence[DigestedPeptide],
    *,
    record_by_accession: dict[str, NormalizedProteinRecord],
    gene_symbols: tuple[str, ...],
) -> PeptideUniquenessClass:
    record_classes: set[str] = set()
    accessions: set[str] = set()
    protein_families: set[str] = set()
    for member in members:
        accessions.add(member.source_accession)
        protein_families.add(member.source_protein_family)
        record = record_by_accession.get(member.source_accession)
        if record is None:
            record_classes.add("target")
            continue
        flags = {(record.contaminant, record.decoy)}
        if flags == {(False, False)}:
            record_classes.add("target")
        elif flags == {(True, False)}:
            record_classes.add("contaminant")
        elif flags == {(False, True)}:
            record_classes.add("decoy")
        else:
            record_classes.update({"contaminant", "decoy"})

    if record_classes == {"contaminant"}:
        return PeptideUniquenessClass.CONTAMINANT
    if record_classes == {"decoy"}:
        return PeptideUniquenessClass.DECOY
    if len(record_classes) > 1:
        return PeptideUniquenessClass.MIXED
    if len(accessions) == 1:
        return PeptideUniquenessClass.UNIQUE
    if len(protein_families) == 1:
        return PeptideUniquenessClass.ISOFORM_SHARED
    if len(gene_symbols) == 1:
        return PeptideUniquenessClass.FAMILY_SHARED
    return PeptideUniquenessClass.SHARED
