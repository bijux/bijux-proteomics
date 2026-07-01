# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Reusable persisted peptide and protein indexes over governed FASTA inputs."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.sequences.digestion import (
    DigestedPeptide,
    DigestPolicy,
    PeptideDigestionMode,
    ProteaseRule,
    build_digest_policy,
    digest_protein_records,
    get_protease_rule,
)
from bijux_proteomics.sequences.fasta import (
    FastaParseMode,
    NormalizedProteinRecord,
    parse_fasta_document,
)
from bijux_proteomics_foundation import DocumentSchema, JsonModel, hash_text


class ProteinIndexProteinEntry(JsonModel):
    """One indexed protein with sequence and peptide support."""

    model_config = ConfigDict(extra="forbid")

    accession: str = Field(..., min_length=1)
    accession_namespace: str = Field(..., min_length=1)
    source_identifier: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    isoform: int | None = Field(default=None, ge=1)
    gene: str | None = None
    organism: str | None = None
    description: str = ""
    residues: str = Field(..., min_length=1)
    sequence_checksum: str = Field(..., min_length=64, max_length=64)
    peptide_sequences: tuple[str, ...] = Field(default_factory=tuple)
    decoy: bool = False
    contaminant: bool = False


class ProteinIndexPeptideEntry(JsonModel):
    """One indexed peptide with parent-protein membership."""

    model_config = ConfigDict(extra="forbid")

    peptide_sequence: str = Field(..., min_length=1)
    protein_accessions: tuple[str, ...] = Field(default_factory=tuple)
    source_identifiers: tuple[str, ...] = Field(default_factory=tuple)
    missed_cleavage_counts: tuple[int, ...] = Field(default_factory=tuple)
    contains_decoy_parent: bool = False
    contains_contaminant_parent: bool = False


class ProteinIndexSummary(JsonModel):
    """Stable summary over one reusable protein index file."""

    model_config = ConfigDict(extra="forbid")

    source_record_count: int = Field(..., ge=0)
    indexed_protein_count: int = Field(..., ge=0)
    indexed_peptide_count: int = Field(..., ge=0)
    decoy_protein_count: int = Field(..., ge=0)
    contaminant_protein_count: int = Field(..., ge=0)
    decoy_peptide_count: int = Field(..., ge=0)
    contaminant_peptide_count: int = Field(..., ge=0)


class ProteinIndexDocument(JsonModel):
    """Persisted peptide and protein lookup file built from one FASTA digest."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    digest_policy: DigestPolicy
    source_path: str | None = None
    source_sha256: str = Field(..., min_length=64, max_length=64)
    proteins_by_accession: dict[str, ProteinIndexProteinEntry] = Field(
        default_factory=dict
    )
    peptides_by_sequence: dict[str, ProteinIndexPeptideEntry] = Field(
        default_factory=dict
    )
    summary: ProteinIndexSummary


def build_protein_index(
    fasta: str | Path,
    enzyme: ProteaseRule | str,
    missed_cleavages: int,
    out_path: Path,
    *,
    digestion_mode: PeptideDigestionMode = PeptideDigestionMode.FULL,
    parse_mode: FastaParseMode = FastaParseMode.STRICT,
) -> ProteinIndexDocument:
    """Build and persist a reusable protein index from governed FASTA content."""

    fasta_text, source_path = _resolve_fasta_input(fasta)
    parse_report = parse_fasta_document(fasta_text, mode=parse_mode)
    if parse_report.rejected_records:
        rejected = ", ".join(
            record.source_identifier for record in parse_report.rejected_records
        )
        raise ValueError(
            "protein index requires fully accepted FASTA content; rejected records: "
            f"{rejected}"
        )
    protease_rule = get_protease_rule(enzyme) if isinstance(enzyme, str) else enzyme
    records = parse_report.accepted_records
    digested = digest_protein_records(
        records,
        protease=protease_rule,
        missed_cleavages=missed_cleavages,
        mode=digestion_mode,
    )
    protein_index = _assemble_protein_index(
        records=records,
        digested=digested,
        digest_policy=build_digest_policy(
            protease=protease_rule,
            digestion_mode=digestion_mode,
            missed_cleavages=missed_cleavages,
            min_length=None,
            max_length=None,
            min_mass=None,
            max_mass=None,
        ),
        source_path=source_path,
        source_sha256=hash_text(fasta_text),
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(protein_index.to_stable_json() + "\n", encoding="utf-8")
    return protein_index


def load_protein_index(path: Path) -> ProteinIndexDocument:
    """Load a reusable protein index file from stable JSON."""

    return ProteinIndexDocument.model_validate_json(path.read_text(encoding="utf-8"))


def lookup_accession(
    index: ProteinIndexDocument, accession: str
) -> ProteinIndexProteinEntry | None:
    """Return the indexed protein entry for one accession."""

    return index.proteins_by_accession.get(accession.strip().upper())


def lookup_protein_sequence(index: ProteinIndexDocument, accession: str) -> str | None:
    """Return the indexed protein sequence for one accession."""

    entry = lookup_accession(index, accession)
    if entry is None:
        return None
    return entry.residues


def lookup_protein_peptides(
    index: ProteinIndexDocument, accession: str
) -> tuple[str, ...]:
    """Return the indexed peptide sequences for one protein accession."""

    entry = lookup_accession(index, accession)
    if entry is None:
        return ()
    return entry.peptide_sequences


def lookup_peptide_entry(
    index: ProteinIndexDocument, peptide_sequence: str
) -> ProteinIndexPeptideEntry | None:
    """Return the indexed peptide entry for one stripped peptide sequence."""

    return index.peptides_by_sequence.get(peptide_sequence.strip().upper())


def lookup_peptide_proteins(
    index: ProteinIndexDocument, peptide_sequence: str
) -> tuple[str, ...]:
    """Return the protein accessions matched by one indexed peptide sequence."""

    entry = lookup_peptide_entry(index, peptide_sequence)
    if entry is None:
        return ()
    return entry.protein_accessions


def _assemble_protein_index(
    *,
    records: Sequence[NormalizedProteinRecord],
    digested: Sequence[DigestedPeptide],
    digest_policy: DigestPolicy,
    source_path: str | None,
    source_sha256: str,
) -> ProteinIndexDocument:
    record_by_accession = {
        _stable_record_accession(record): record for record in records
    }
    protein_to_peptides: dict[str, set[str]] = {
        accession: set() for accession in record_by_accession
    }
    peptide_members: dict[str, list[DigestedPeptide]] = {}
    for peptide in digested:
        protein_to_peptides.setdefault(peptide.source_accession, set()).add(
            peptide.sequence
        )
        peptide_members.setdefault(peptide.sequence, []).append(peptide)

    proteins_by_accession = {
        accession: ProteinIndexProteinEntry(
            accession=accession,
            accession_namespace=record.accession_namespace,
            source_identifier=record.source_identifier,
            display_name=record.display_name,
            isoform=record.isoform,
            gene=record.gene,
            organism=record.organism,
            description=record.description,
            residues=record.residues,
            sequence_checksum=record.sequence_checksum,
            peptide_sequences=tuple(sorted(protein_to_peptides.get(accession, ()))),
            decoy=record.decoy,
            contaminant=record.contaminant,
        )
        for accession, record in sorted(record_by_accession.items())
    }
    peptides_by_sequence = {
        sequence: _build_peptide_entry(sequence, members, record_by_accession)
        for sequence, members in sorted(peptide_members.items())
    }

    schema = DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind="protein_peptide_index",
        package_name="bijux-proteomics-core",
        status="generated",
    )
    document = ProteinIndexDocument(
        document_schema=schema,
        digest_policy=digest_policy,
        source_path=source_path,
        source_sha256=source_sha256,
        proteins_by_accession=proteins_by_accession,
        peptides_by_sequence=peptides_by_sequence,
        summary=ProteinIndexSummary(
            source_record_count=len(records),
            indexed_protein_count=len(proteins_by_accession),
            indexed_peptide_count=len(peptides_by_sequence),
            decoy_protein_count=sum(
                1 for entry in proteins_by_accession.values() if entry.decoy
            ),
            contaminant_protein_count=sum(
                1 for entry in proteins_by_accession.values() if entry.contaminant
            ),
            decoy_peptide_count=sum(
                1
                for entry in peptides_by_sequence.values()
                if entry.contains_decoy_parent
            ),
            contaminant_peptide_count=sum(
                1
                for entry in peptides_by_sequence.values()
                if entry.contains_contaminant_parent
            ),
        ),
    )
    payload = document.to_dict()
    return document.model_copy(
        update={"document_schema": document.document_schema.with_content_hash(payload)}
    )


def _build_peptide_entry(
    sequence: str,
    members: Sequence[DigestedPeptide],
    record_by_accession: dict[str, NormalizedProteinRecord],
) -> ProteinIndexPeptideEntry:
    accessions = tuple(sorted({member.source_accession for member in members}))
    identifiers = tuple(sorted({member.source_identifier for member in members}))
    parent_records = [
        record_by_accession[accession]
        for accession in accessions
        if accession in record_by_accession
    ]
    return ProteinIndexPeptideEntry(
        peptide_sequence=sequence,
        protein_accessions=accessions,
        source_identifiers=identifiers,
        missed_cleavage_counts=tuple(
            sorted({member.missed_cleavages for member in members})
        ),
        contains_decoy_parent=any(record.decoy for record in parent_records),
        contains_contaminant_parent=any(
            record.contaminant for record in parent_records
        ),
    )


def _resolve_fasta_input(fasta: str | Path) -> tuple[str, str | None]:
    if isinstance(fasta, Path):
        return fasta.read_text(encoding="utf-8"), str(fasta)
    candidate = Path(fasta)
    if "\n" not in fasta and candidate.exists():
        return candidate.read_text(encoding="utf-8"), str(candidate)
    return fasta, None


def _stable_record_accession(record: NormalizedProteinRecord) -> str:
    if isinstance(record.isoform, int):
        return f"{record.canonical_accession}-{record.isoform}"
    return record.canonical_accession


__all__ = [
    "ProteinIndexDocument",
    "ProteinIndexPeptideEntry",
    "ProteinIndexProteinEntry",
    "ProteinIndexSummary",
    "build_protein_index",
    "load_protein_index",
    "lookup_accession",
    "lookup_peptide_entry",
    "lookup_peptide_proteins",
    "lookup_protein_peptides",
    "lookup_protein_sequence",
]
