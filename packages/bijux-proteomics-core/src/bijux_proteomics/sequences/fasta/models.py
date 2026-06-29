# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable FASTA models, identifiers, and residue contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import re

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics_foundation import DocumentSchema, JsonModel, TargetId

_CANONICAL_RESIDUES = frozenset("ACDEFGHIKLMNPQRSTVWY")
_AMBIGUOUS_RESIDUES = frozenset("BJXZ")
_UNSUPPORTED_RESIDUES = frozenset("OU")
_SEQUENCE_RE = re.compile(r"^[A-Z*]+$")
_UNIPROT_ACCESSION_RE = re.compile(
    r"^(?P<accession>(?:[OPQ][0-9][A-Z0-9]{3}[0-9])|(?:[A-NR-Z][0-9][A-Z][A-Z0-9]{2}[0-9]))(?:-(?P<isoform>[1-9][0-9]*))?$"
)
_REFSEQ_ACCESSION_RE = re.compile(
    r"^(?P<accession>(?:NP|XP|YP|WP|AP|ZP)_[0-9]+(?:\.[0-9]+)?)$"
)
_ENSEMBL_ACCESSION_RE = re.compile(
    r"^(?P<accession>ENS[A-Z]*P[0-9]{6,})(?:\.[0-9]+)?$"
)
_GENE_FIELD_RE = re.compile(r"\bGN=(?P<gene>[A-Za-z0-9_.-]+)")
_ORGANISM_FIELD_RE = re.compile(r"\bOS=(?P<organism>.+?)(?=\s(?:OX|GN|PE|SV)=|$)")
_ENSEMBL_GENE_SYMBOL_RE = re.compile(r"\bgene_symbol:(?P<gene>[A-Za-z0-9_.-]+)")
_ENSEMBL_DESCRIPTION_RE = re.compile(r"\bdescription:(?P<description>.+)")
_DECOY_PREFIXES = ("DECOY_", "REV_", "REVERSE_", "SHUFFLED_")


@dataclass(frozen=True)
class FastaSequenceRecord:
    """One parsed FASTA record before normalization."""

    header: str
    identifier: str
    description: str
    residues: str


@dataclass(frozen=True)
class UniProtAccession:
    """Normalized UniProt accession with an optional isoform suffix."""

    accession: str
    isoform: int | None = None


class FastaParseMode(StrEnum):
    """Supported FASTA parser policies."""

    STRICT = "strict"
    PERMISSIVE = "permissive"


class DuplicateAccessionPolicy(StrEnum):
    """Explicit policy for normalized duplicate protein accessions."""

    REJECT = "reject"
    ACCEPT_WITH_WARNING = "accept_with_warning"


class ResiduePolicyState(StrEnum):
    """Support state for an uncommon residue token under one parser policy."""

    ACCEPTED = "accepted"
    ACCEPTED_WITH_WARNING = "accepted_with_warning"
    REFUSED = "refused"


class DecoyGenerationMode(StrEnum):
    """Supported target-decoy generation modes."""

    REVERSE = "reverse"
    SHUFFLE = "shuffle"


class SequenceIssueSeverity(StrEnum):
    """Severity of a sequence validation issue."""

    WARNING = "warning"
    ERROR = "error"


class SequenceValidationIssue(JsonModel):
    """One normalized sequence validation issue."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    severity: SequenceIssueSeverity
    message: str = Field(..., min_length=1)
    positions: tuple[int, ...] = Field(default_factory=tuple)


class ResiduePolicyEntry(JsonModel):
    """One explicit parser decision for an uncommon residue symbol."""

    model_config = ConfigDict(extra="forbid")

    residue: str = Field(..., min_length=1, max_length=1)
    state: ResiduePolicyState
    rationale: str = Field(..., min_length=1)


class SequenceResiduePolicy(JsonModel):
    """Explicit uncommon-residue policy for one FASTA parser mode."""

    model_config = ConfigDict(extra="forbid")

    mode: FastaParseMode
    entries: tuple[ResiduePolicyEntry, ...] = Field(default_factory=tuple)


class SequenceValidationResult(JsonModel):
    """Validation result for one protein sequence string."""

    model_config = ConfigDict(extra="forbid")

    normalized_residues: str = Field(
        ..., description="Whitespace-normalized, uppercased residue string."
    )
    issues: tuple[SequenceValidationIssue, ...] = Field(default_factory=tuple)

    @property
    def is_valid(self) -> bool:
        """Return whether the sequence passes the active parser policy."""

        return all(
            issue.severity is not SequenceIssueSeverity.ERROR for issue in self.issues
        )


class NormalizedProteinRecord(JsonModel):
    """Stable normalized protein record extracted from FASTA input."""

    model_config = ConfigDict(extra="forbid")

    source_header: str = Field(..., min_length=1)
    source_identifier: str = Field(..., min_length=1)
    accession_namespace: str = Field(..., min_length=1)
    canonical_accession: str = Field(..., min_length=1)
    isoform: int | None = None
    display_name: str = Field(..., min_length=1)
    gene: str | None = None
    organism: str | None = None
    description: str = ""
    residues: str = Field(..., min_length=1)
    residue_count: int = Field(..., ge=1)
    sequence_checksum: str = Field(..., min_length=64, max_length=64)
    contaminant: bool = False
    decoy: bool = False
    validation_issues: tuple[SequenceValidationIssue, ...] = Field(
        default_factory=tuple
    )

    @field_validator("residues")
    @classmethod
    def _validate_residues(cls, value: str) -> str:
        sequence = value.strip().upper()
        if not _SEQUENCE_RE.fullmatch(sequence):
            raise ValueError("residues must be uppercase amino-acid symbols")
        return sequence


class RejectedFastaRecord(JsonModel):
    """Rejected FASTA record and its validation issues."""

    model_config = ConfigDict(extra="forbid")

    source_header: str = Field(..., min_length=1)
    source_identifier: str = Field(..., min_length=1)
    issues: tuple[SequenceValidationIssue, ...]


class FastaDatabaseComposition(JsonModel):
    """Parser-level composition summary over accepted FASTA records."""

    model_config = ConfigDict(extra="forbid")

    accepted_record_count: int = Field(..., ge=0)
    target_count: int = Field(..., ge=0)
    decoy_count: int = Field(..., ge=0)
    contaminant_count: int = Field(..., ge=0)
    accession_namespace_counts: dict[str, int] = Field(default_factory=dict)


class FastaParseReport(JsonModel):
    """Result of parsing one FASTA payload under a parser policy."""

    model_config = ConfigDict(extra="forbid")

    parse_mode: FastaParseMode
    duplicate_accession_policy: DuplicateAccessionPolicy
    total_records: int = Field(..., ge=0)
    accepted_records: tuple[NormalizedProteinRecord, ...] = Field(default_factory=tuple)
    rejected_records: tuple[RejectedFastaRecord, ...] = Field(default_factory=tuple)
    duplicate_identifiers: tuple[str, ...] = Field(default_factory=tuple)
    duplicate_accessions: tuple[str, ...] = Field(default_factory=tuple)
    database_composition: FastaDatabaseComposition


class FastaStatsReport(JsonModel):
    """Summary metrics for one normalized FASTA collection."""

    model_config = ConfigDict(extra="forbid")

    total_records: int = Field(..., ge=0)
    unique_accessions: int = Field(..., ge=0)
    total_residues: int = Field(..., ge=0)
    min_length: int | None = None
    median_length: float | None = None
    max_length: int | None = None
    invalid_record_count: int = Field(default=0, ge=0)
    duplicate_identifier_count: int = Field(default=0, ge=0)
    duplicate_accession_count: int = Field(default=0, ge=0)
    duplicate_sequence_count: int = Field(default=0, ge=0)
    decoy_count: int = Field(default=0, ge=0)
    target_count: int = Field(default=0, ge=0)
    contaminant_count: int = Field(default=0, ge=0)
    accession_namespace_counts: dict[str, int] = Field(default_factory=dict)


class FastaDeduplicationReport(JsonModel):
    """Result of FASTA deduplication."""

    model_config = ConfigDict(extra="forbid")

    input_records: int = Field(..., ge=0)
    output_records: int = Field(..., ge=0)
    duplicate_accessions: tuple[str, ...] = Field(default_factory=tuple)
    duplicate_sequences: tuple[str, ...] = Field(default_factory=tuple)


class FastaFilterReport(JsonModel):
    """Result of FASTA filtering."""

    model_config = ConfigDict(extra="forbid")

    input_records: int = Field(..., ge=0)
    output_records: int = Field(..., ge=0)
    excluded_by_length: int = Field(default=0, ge=0)
    excluded_by_accession: int = Field(default=0, ge=0)
    excluded_by_organism: int = Field(default=0, ge=0)
    excluded_as_contaminant: int = Field(default=0, ge=0)


class FastaProvenanceManifest(JsonModel):
    """Stable provenance manifest for FASTA processing steps."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    operation: str = Field(..., min_length=1)
    source_path: str | None = None
    source_sha256: str | None = None
    parse_mode: FastaParseMode
    input_record_count: int = Field(..., ge=0)
    accepted_record_count: int = Field(..., ge=0)
    rejected_record_count: int = Field(..., ge=0)
    output_record_count: int = Field(..., ge=0)
    parameters: dict[str, str | int | bool | None] = Field(default_factory=dict)


class DecoyGenerationManifest(JsonModel):
    """Stable manifest for one deterministic decoy-generation step."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    decoy_mode: DecoyGenerationMode
    prefix: str = Field(..., min_length=1)
    seed: int
    source_path: str | None = None
    source_sha256: str | None = None
    input_record_count: int = Field(..., ge=0)
    output_record_count: int = Field(..., ge=0)
    reproducibility_hash: str = Field(..., min_length=64, max_length=64)
    output_sha256: str = Field(..., min_length=64, max_length=64)


class DecoyGenerationReport(JsonModel):
    """Reviewer-facing summary of one target-decoy generation step."""

    model_config = ConfigDict(extra="forbid")

    decoy_mode: DecoyGenerationMode
    prefix: str = Field(..., min_length=1)
    seed: int
    input_target_count: int = Field(..., ge=0)
    generated_decoy_count: int = Field(..., ge=0)
    unchanged_sequence_count: int = Field(..., ge=0)
    target_sequence_collision_count: int = Field(..., ge=0)
    unchanged_sequence_accessions: tuple[str, ...] = Field(default_factory=tuple)
    target_sequence_collision_accessions: tuple[str, ...] = Field(default_factory=tuple)
    valid: bool


class TargetDecoyValidationReport(JsonModel):
    """Validation report for a target/decoy FASTA collection."""

    model_config = ConfigDict(extra="forbid")

    prefix: str = Field(..., min_length=1)
    target_count: int = Field(..., ge=0)
    decoy_count: int = Field(..., ge=0)
    missing_decoys: tuple[str, ...] = Field(default_factory=tuple)
    duplicate_decoys: tuple[str, ...] = Field(default_factory=tuple)
    orphan_decoys: tuple[str, ...] = Field(default_factory=tuple)
    valid: bool


class ProteinSequence(JsonModel):
    """Canonical protein sequence document."""

    model_config = ConfigDict(extra="forbid")

    target_id: TargetId = Field(..., description="Target identifier.")
    residues: str = Field(
        ..., min_length=1, description="Canonical amino-acid sequence."
    )

    @field_validator("residues")
    @classmethod
    def _validate_residues(cls, value: str) -> str:
        """Normalize and validate canonical amino-acid residue symbols."""

        sequence = value.strip().upper()
        if not _SEQUENCE_RE.fullmatch(sequence) or any(
            residue not in _CANONICAL_RESIDUES for residue in sequence
        ):
            raise ValueError("residues must contain only canonical amino-acid symbols")
        return sequence


def sequence_length(sequence: ProteinSequence) -> int:
    """Return the amino-acid length of a canonical sequence."""

    return len(sequence.residues)


__all__ = [
    "DecoyGenerationManifest",
    "DecoyGenerationMode",
    "DecoyGenerationReport",
    "DuplicateAccessionPolicy",
    "FastaDatabaseComposition",
    "FastaDeduplicationReport",
    "FastaFilterReport",
    "FastaParseMode",
    "FastaParseReport",
    "FastaProvenanceManifest",
    "FastaSequenceRecord",
    "FastaStatsReport",
    "NormalizedProteinRecord",
    "ProteinSequence",
    "RejectedFastaRecord",
    "ResiduePolicyEntry",
    "ResiduePolicyState",
    "SequenceIssueSeverity",
    "SequenceResiduePolicy",
    "SequenceValidationIssue",
    "SequenceValidationResult",
    "TargetDecoyValidationReport",
    "UniProtAccession",
    "sequence_length",
]
