# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Protein sequence, FASTA, and target/decoy operations."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json
from pathlib import Path
import random
import re
from statistics import median

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
_ENSEMBL_ACCESSION_RE = re.compile(r"^(?P<accession>ENS[A-Z]*P[0-9]{6,})(?:\.[0-9]+)?$")
_GENE_FIELD_RE = re.compile(r"\bGN=(?P<gene>[A-Za-z0-9_.-]+)")
_ORGANISM_FIELD_RE = re.compile(r"\bOS=(?P<organism>.+?)(?=\s(?:OX|GN|PE|SV)=|$)")
_ENSEMBL_GENE_SYMBOL_RE = re.compile(r"\bgene_symbol:(?P<gene>[A-Za-z0-9_.-]+)")
_ENSEMBL_DESCRIPTION_RE = re.compile(r"\bdescription:(?P<description>.+)")
_DECOY_PREFIXES = ("DECOY_", "REV_", "REVERSE_", "SHUFFLED_")


@dataclass(frozen=True)
class FastaSequenceRecord:
    """One parsed FASTA record before it is promoted into a normalized model."""

    header: str
    identifier: str
    description: str
    residues: str


@dataclass(frozen=True)
class UniProtAccession:
    """Normalized UniProt accession with optional isoform suffix."""

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
    """Supported target/decoy generation modes."""

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


_SEQUENCE_POLICY_BY_MODE: dict[FastaParseMode, SequenceResiduePolicy] = {
    FastaParseMode.STRICT: SequenceResiduePolicy(
        mode=FastaParseMode.STRICT,
        entries=(
            ResiduePolicyEntry(
                residue="B",
                state=ResiduePolicyState.REFUSED,
                rationale="B conflates aspartate and asparagine and is refused in strict mode.",
            ),
            ResiduePolicyEntry(
                residue="J",
                state=ResiduePolicyState.REFUSED,
                rationale="J conflates leucine and isoleucine and is refused in strict mode.",
            ),
            ResiduePolicyEntry(
                residue="X",
                state=ResiduePolicyState.REFUSED,
                rationale="X does not preserve residue identity and is refused in strict mode.",
            ),
            ResiduePolicyEntry(
                residue="Z",
                state=ResiduePolicyState.REFUSED,
                rationale="Z conflates glutamate and glutamine and is refused in strict mode.",
            ),
            ResiduePolicyEntry(
                residue="U",
                state=ResiduePolicyState.REFUSED,
                rationale="U is currently unsupported by downstream chemistry surfaces.",
            ),
            ResiduePolicyEntry(
                residue="O",
                state=ResiduePolicyState.REFUSED,
                rationale="O is currently unsupported by downstream chemistry surfaces.",
            ),
        ),
    ),
    FastaParseMode.PERMISSIVE: SequenceResiduePolicy(
        mode=FastaParseMode.PERMISSIVE,
        entries=(
            ResiduePolicyEntry(
                residue="B",
                state=ResiduePolicyState.ACCEPTED_WITH_WARNING,
                rationale="B is preserved with warning because it is residue-ambiguous.",
            ),
            ResiduePolicyEntry(
                residue="J",
                state=ResiduePolicyState.ACCEPTED_WITH_WARNING,
                rationale="J is preserved with warning because it is residue-ambiguous.",
            ),
            ResiduePolicyEntry(
                residue="X",
                state=ResiduePolicyState.ACCEPTED_WITH_WARNING,
                rationale="X is preserved with warning because it is residue-ambiguous.",
            ),
            ResiduePolicyEntry(
                residue="Z",
                state=ResiduePolicyState.ACCEPTED_WITH_WARNING,
                rationale="Z is preserved with warning because it is residue-ambiguous.",
            ),
            ResiduePolicyEntry(
                residue="U",
                state=ResiduePolicyState.REFUSED,
                rationale="U remains refused until chemistry and mass surfaces support it explicitly.",
            ),
            ResiduePolicyEntry(
                residue="O",
                state=ResiduePolicyState.REFUSED,
                rationale="O remains refused until chemistry and mass surfaces support it explicitly.",
            ),
        ),
    ),
}


def build_sequence_residue_policy(mode: FastaParseMode) -> SequenceResiduePolicy:
    """Return the explicit uncommon-residue policy for one parser mode."""
    return _SEQUENCE_POLICY_BY_MODE[mode].model_copy(deep=True)


def sequence_checksum(residues: str) -> str:
    """Return a stable SHA-256 checksum over normalized residues."""
    normalized = "".join(
        character for character in residues.strip().upper() if not character.isspace()
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def parse_fasta_records(
    payload: str,
    *,
    mode: FastaParseMode = FastaParseMode.STRICT,
    duplicate_accession_policy: DuplicateAccessionPolicy = DuplicateAccessionPolicy.REJECT,
) -> tuple[FastaSequenceRecord, ...]:
    """Parse FASTA records and raise if any record fails the active policy."""
    report = parse_fasta_document(
        payload,
        mode=mode,
        duplicate_accession_policy=duplicate_accession_policy,
    )
    if report.rejected_records:
        identifiers = ", ".join(
            rejected.source_identifier for rejected in report.rejected_records
        )
        raise ValueError(f"FASTA payload contains rejected records: {identifiers}")
    return tuple(
        FastaSequenceRecord(
            header=record.source_header,
            identifier=record.source_identifier,
            description=record.description,
            residues=record.residues,
        )
        for record in report.accepted_records
    )


def parse_fasta_document(
    payload: str,
    *,
    mode: FastaParseMode = FastaParseMode.STRICT,
    duplicate_accession_policy: DuplicateAccessionPolicy = DuplicateAccessionPolicy.REJECT,
) -> FastaParseReport:
    """Parse FASTA payload into normalized records with explicit rejection details.

    Inputs:
    ``payload`` must contain FASTA text, ``mode`` selects sequence validation
    strictness, and ``duplicate_accession_policy`` controls how repeated
    normalized accessions are treated.

    Outputs:
    Returns one ``FastaParseReport`` with accepted normalized records, rejected
    records, duplicate summaries, and database composition metrics.

    Failure Modes:
    Propagates low-level FASTA record parsing failures if the payload cannot be
    tokenized into records before validation.

    Scientific Caveats:
    Acceptance means the records satisfy the active formatting and residue
    policy only; it does not prove biological correctness, uniqueness in an
    external database, or suitability for one downstream search space.
    """
    raw_records = _parse_raw_fasta_records(payload)
    duplicates = _duplicate_identifiers(record.identifier for record in raw_records)
    duplicate_accessions = _duplicate_accessions(
        _stable_accession_key_from_identifier(record.identifier)
        for record in raw_records
    )
    seen_identifiers: set[str] = set()
    seen_accessions: set[str] = set()
    accepted: list[NormalizedProteinRecord] = []
    rejected: list[RejectedFastaRecord] = []

    for record in raw_records:
        validation = validate_protein_sequence(record.residues, mode=mode)
        issues = list(validation.issues)
        accession_key = _stable_accession_key_from_identifier(record.identifier)
        if record.identifier in seen_identifiers:
            issues.append(
                SequenceValidationIssue(
                    code="duplicate_identifier",
                    severity=(
                        SequenceIssueSeverity.ERROR
                        if mode is FastaParseMode.STRICT
                        else SequenceIssueSeverity.WARNING
                    ),
                    message=f"duplicate FASTA identifier {record.identifier!r}",
                )
            )
        seen_identifiers.add(record.identifier)
        if accession_key in seen_accessions:
            issues.append(
                SequenceValidationIssue(
                    code="duplicate_accession",
                    severity=(
                        SequenceIssueSeverity.ERROR
                        if duplicate_accession_policy is DuplicateAccessionPolicy.REJECT
                        else SequenceIssueSeverity.WARNING
                    ),
                    message=f"duplicate normalized accession {accession_key!r}",
                )
            )
        seen_accessions.add(accession_key)
        if any(issue.severity is SequenceIssueSeverity.ERROR for issue in issues):
            rejected.append(
                RejectedFastaRecord(
                    source_header=record.header,
                    source_identifier=record.identifier,
                    issues=tuple(issues),
                )
            )
            continue
        accepted.append(
            normalize_protein_record(
                record,
                normalized_residues=validation.normalized_residues,
                validation_issues=tuple(issues),
            )
        )

    return FastaParseReport(
        parse_mode=mode,
        duplicate_accession_policy=duplicate_accession_policy,
        total_records=len(raw_records),
        accepted_records=tuple(accepted),
        rejected_records=tuple(rejected),
        duplicate_identifiers=tuple(sorted(duplicates)),
        duplicate_accessions=tuple(sorted(duplicate_accessions)),
        database_composition=_build_fasta_database_composition(tuple(accepted)),
    )


def validate_protein_sequence(
    sequence: str, *, mode: FastaParseMode = FastaParseMode.STRICT
) -> SequenceValidationResult:
    """Validate one protein sequence string under the active parser policy."""
    issues: list[SequenceValidationIssue] = []
    policy = build_sequence_residue_policy(mode)
    policy_map = {entry.residue: entry for entry in policy.entries}
    had_lowercase = any(
        character.isalpha() and character.islower() for character in sequence
    )
    had_whitespace = any(character.isspace() for character in sequence)
    collapsed = "".join(character for character in sequence if not character.isspace())

    if had_lowercase:
        issues.append(
            SequenceValidationIssue(
                code="lowercase_residues",
                severity=SequenceIssueSeverity.WARNING,
                message="lowercase residues were normalized to uppercase",
            )
        )
    if had_whitespace:
        issues.append(
            SequenceValidationIssue(
                code="whitespace_removed",
                severity=SequenceIssueSeverity.WARNING,
                message="embedded whitespace was removed during normalization",
            )
        )
    if not collapsed:
        issues.append(
            SequenceValidationIssue(
                code="empty_sequence",
                severity=SequenceIssueSeverity.ERROR,
                message="sequence must contain at least one amino-acid residue",
            )
        )
        return SequenceValidationResult(normalized_residues="", issues=tuple(issues))

    normalized = collapsed.upper()
    stop_positions = [
        index + 1 for index, residue in enumerate(normalized) if residue == "*"
    ]
    if stop_positions:
        trailing = len(stop_positions)
        terminal_only = stop_positions == list(
            range(len(normalized) - trailing + 1, len(normalized) + 1)
        )
        if mode is FastaParseMode.PERMISSIVE and terminal_only:
            normalized = normalized.rstrip("*")
            issues.append(
                SequenceValidationIssue(
                    code="terminal_stop_codon_removed",
                    severity=SequenceIssueSeverity.WARNING,
                    message="terminal stop codons were removed in permissive mode",
                    positions=tuple(stop_positions),
                )
            )
        else:
            issues.append(
                SequenceValidationIssue(
                    code="stop_codon",
                    severity=SequenceIssueSeverity.ERROR,
                    message="sequence contains stop codons outside the permissive terminal-stop rule",
                    positions=tuple(stop_positions),
                )
            )

    warning_positions = [
        index + 1
        for index, residue in enumerate(normalized)
        if residue in _AMBIGUOUS_RESIDUES
        and policy_map[residue].state is ResiduePolicyState.ACCEPTED_WITH_WARNING
    ]
    error_positions = [
        index + 1
        for index, residue in enumerate(normalized)
        if residue in _AMBIGUOUS_RESIDUES
        and policy_map[residue].state is ResiduePolicyState.REFUSED
    ]
    unsupported_positions = [
        index + 1
        for index, residue in enumerate(normalized)
        if residue in _UNSUPPORTED_RESIDUES
    ]
    if warning_positions:
        issues.append(
            SequenceValidationIssue(
                code="ambiguous_residue",
                severity=SequenceIssueSeverity.WARNING,
                message="sequence contains ambiguous amino-acid symbols that were preserved with warning",
                positions=tuple(warning_positions),
            )
        )
    if error_positions:
        issues.append(
            SequenceValidationIssue(
                code="ambiguous_residue",
                severity=SequenceIssueSeverity.ERROR,
                message="sequence contains ambiguous amino-acid symbols that are refused by policy",
                positions=tuple(error_positions),
            )
        )
    if unsupported_positions:
        issues.append(
            SequenceValidationIssue(
                code="unsupported_residue",
                severity=SequenceIssueSeverity.ERROR,
                message="sequence contains residue symbols that remain unsupported by downstream chemistry surfaces",
                positions=tuple(unsupported_positions),
            )
        )

    invalid_positions = [
        index + 1
        for index, residue in enumerate(normalized)
        if residue not in _CANONICAL_RESIDUES
        and residue not in _AMBIGUOUS_RESIDUES
        and residue not in _UNSUPPORTED_RESIDUES
    ]
    if invalid_positions:
        issues.append(
            SequenceValidationIssue(
                code="invalid_character",
                severity=SequenceIssueSeverity.ERROR,
                message="sequence contains invalid non-residue characters",
                positions=tuple(invalid_positions),
            )
        )

    return SequenceValidationResult(
        normalized_residues=normalized,
        issues=tuple(issues),
    )


def normalize_protein_record(
    record: FastaSequenceRecord,
    *,
    normalized_residues: str | None = None,
    validation_issues: tuple[SequenceValidationIssue, ...] = (),
) -> NormalizedProteinRecord:
    """Normalize one FASTA record into a stable protein record."""
    residues = (
        normalized_residues if normalized_residues is not None else record.residues
    )
    accession_namespace, canonical_accession, isoform = _normalize_accession(
        record.identifier
    )
    gene = _extract_gene(record)
    organism = _extract_organism(record)
    description = _extract_description(record)
    display_name = _build_display_name(record, canonical_accession, gene)
    return NormalizedProteinRecord(
        source_header=record.header,
        source_identifier=record.identifier,
        accession_namespace=accession_namespace,
        canonical_accession=canonical_accession,
        isoform=isoform,
        display_name=display_name,
        gene=gene,
        organism=organism,
        description=description,
        residues=residues,
        residue_count=len(residues),
        sequence_checksum=sequence_checksum(residues),
        contaminant=_is_contaminant_record(record),
        decoy=_is_decoy_record(record),
        validation_issues=validation_issues,
    )


def build_fasta_stats(
    records: tuple[NormalizedProteinRecord, ...],
    *,
    rejected_records: tuple[RejectedFastaRecord, ...] = (),
) -> FastaStatsReport:
    """Summarize normalized FASTA records."""
    lengths = [record.residue_count for record in records]
    namespace_counts = Counter(record.accession_namespace for record in records)
    duplicate_identifier_count = sum(
        count - 1
        for count in Counter(record.source_identifier for record in records).values()
        if count > 1
    )
    duplicate_accession_count = sum(
        count - 1
        for count in Counter(
            _stable_record_accession(record) for record in records
        ).values()
        if count > 1
    )
    duplicate_sequence_count = sum(
        count - 1
        for count in Counter(record.sequence_checksum for record in records).values()
        if count > 1
    )
    return FastaStatsReport(
        total_records=len(records),
        unique_accessions=len({_stable_record_accession(record) for record in records}),
        total_residues=sum(lengths),
        min_length=min(lengths) if lengths else None,
        median_length=float(median(lengths)) if lengths else None,
        max_length=max(lengths) if lengths else None,
        invalid_record_count=len(rejected_records),
        duplicate_identifier_count=duplicate_identifier_count,
        duplicate_accession_count=duplicate_accession_count,
        duplicate_sequence_count=duplicate_sequence_count,
        decoy_count=sum(1 for record in records if record.decoy),
        target_count=sum(1 for record in records if not record.decoy),
        contaminant_count=sum(1 for record in records if record.contaminant),
        accession_namespace_counts=dict(sorted(namespace_counts.items())),
    )


def deduplicate_fasta_records(
    records: tuple[NormalizedProteinRecord, ...],
) -> tuple[tuple[NormalizedProteinRecord, ...], FastaDeduplicationReport]:
    """Deduplicate records by accession first and sequence checksum second."""
    kept: list[NormalizedProteinRecord] = []
    seen_accessions: set[str] = set()
    seen_sequences: set[str] = set()
    duplicate_accessions: list[str] = []
    duplicate_sequences: list[str] = []

    for record in records:
        if _stable_record_accession(record) in seen_accessions:
            duplicate_accessions.append(record.source_identifier)
            continue
        if record.sequence_checksum in seen_sequences:
            duplicate_sequences.append(record.source_identifier)
            continue
        kept.append(record)
        seen_accessions.add(_stable_record_accession(record))
        seen_sequences.add(record.sequence_checksum)

    return tuple(kept), FastaDeduplicationReport(
        input_records=len(records),
        output_records=len(kept),
        duplicate_accessions=tuple(duplicate_accessions),
        duplicate_sequences=tuple(duplicate_sequences),
    )


def _stable_record_accession(record: NormalizedProteinRecord) -> str:
    if record.isoform is None:
        return f"{record.accession_namespace}:{record.canonical_accession}"
    return f"{record.accession_namespace}:{record.canonical_accession}-{record.isoform}"


def _stable_generated_accession(record: NormalizedProteinRecord, *, prefix: str) -> str:
    accession = f"{prefix}{record.canonical_accession}"
    if record.isoform is None:
        return f"{record.accession_namespace}:{accession}"
    return f"{record.accession_namespace}:{accession}-{record.isoform}"


def filter_fasta_records(
    records: tuple[NormalizedProteinRecord, ...],
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    accession_pattern: str | None = None,
    organism: str | None = None,
    exclude_contaminants: bool = False,
) -> tuple[tuple[NormalizedProteinRecord, ...], FastaFilterReport]:
    """Filter FASTA records with explicit accounting for each exclusion path."""
    filtered: list[NormalizedProteinRecord] = []
    regex = re.compile(accession_pattern) if accession_pattern is not None else None
    excluded_by_length = 0
    excluded_by_accession = 0
    excluded_by_organism = 0
    excluded_as_contaminant = 0

    for record in records:
        if min_length is not None and record.residue_count < min_length:
            excluded_by_length += 1
            continue
        if max_length is not None and record.residue_count > max_length:
            excluded_by_length += 1
            continue
        if regex is not None and regex.search(record.canonical_accession) is None:
            excluded_by_accession += 1
            continue
        if organism is not None and (record.organism or "").lower() != organism.lower():
            excluded_by_organism += 1
            continue
        if exclude_contaminants and record.contaminant:
            excluded_as_contaminant += 1
            continue
        filtered.append(record)

    return tuple(filtered), FastaFilterReport(
        input_records=len(records),
        output_records=len(filtered),
        excluded_by_length=excluded_by_length,
        excluded_by_accession=excluded_by_accession,
        excluded_by_organism=excluded_by_organism,
        excluded_as_contaminant=excluded_as_contaminant,
    )


def build_fasta_provenance_manifest(
    *,
    operation: str,
    source_path: Path | None,
    parse_mode: FastaParseMode,
    input_record_count: int,
    accepted_record_count: int,
    rejected_record_count: int,
    output_record_count: int,
    parameters: dict[str, str | int | bool | None] | None = None,
) -> FastaProvenanceManifest:
    """Build a stable provenance manifest for one FASTA operation."""
    source_sha256 = (
        hashlib.sha256(source_path.read_bytes()).hexdigest()
        if source_path is not None
        else None
    )
    schema = DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind="fasta_provenance_manifest",
        package_name="bijux-proteomics-core",
        status="generated",
    )
    manifest = FastaProvenanceManifest(
        document_schema=schema,
        operation=operation,
        source_path=str(source_path) if source_path is not None else None,
        source_sha256=source_sha256,
        parse_mode=parse_mode,
        input_record_count=input_record_count,
        accepted_record_count=accepted_record_count,
        rejected_record_count=rejected_record_count,
        output_record_count=output_record_count,
        parameters=parameters or {},
    )
    payload = manifest.to_dict()
    return manifest.model_copy(
        update={
            "document_schema": manifest.document_schema.with_content_hash(payload),
        }
    )


def compute_decoy_generation_reproducibility_hash(
    records: tuple[NormalizedProteinRecord, ...],
    *,
    mode: DecoyGenerationMode,
    prefix: str,
    seed: int,
) -> str:
    """Return a stable hash over decoy-generation inputs and policy."""
    payload = {
        "mode": mode.value,
        "prefix": prefix,
        "seed": seed,
        "records": [
            {
                "canonical_accession": record.canonical_accession,
                "isoform": record.isoform,
                "sequence_checksum": record.sequence_checksum,
                "source_identifier": record.source_identifier,
            }
            for record in records
        ],
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()


def build_decoy_generation_manifest(
    *,
    input_records: tuple[NormalizedProteinRecord, ...],
    output_records: tuple[NormalizedProteinRecord, ...],
    mode: DecoyGenerationMode,
    prefix: str,
    seed: int,
    source_path: Path | None,
) -> DecoyGenerationManifest:
    """Build a stable manifest for one deterministic decoy-generation output."""
    source_sha256 = (
        hashlib.sha256(source_path.read_bytes()).hexdigest()
        if source_path is not None
        else None
    )
    schema = DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind="decoy_generation_manifest",
        package_name="bijux-proteomics-core",
        status="generated",
    )
    rendered_output = render_records_fasta(output_records)
    manifest = DecoyGenerationManifest(
        document_schema=schema,
        decoy_mode=mode,
        prefix=prefix,
        seed=seed,
        source_path=str(source_path) if source_path is not None else None,
        source_sha256=source_sha256,
        input_record_count=len(input_records),
        output_record_count=len(output_records),
        reproducibility_hash=compute_decoy_generation_reproducibility_hash(
            input_records,
            mode=mode,
            prefix=prefix,
            seed=seed,
        ),
        output_sha256=hashlib.sha256(rendered_output.encode("utf-8")).hexdigest(),
    )
    payload = manifest.to_dict()
    return manifest.model_copy(
        update={
            "document_schema": manifest.document_schema.with_content_hash(payload),
        }
    )


def build_decoy_generation_report(
    input_records: tuple[NormalizedProteinRecord, ...],
    decoy_records: tuple[NormalizedProteinRecord, ...],
    *,
    mode: DecoyGenerationMode,
    prefix: str,
    seed: int,
) -> DecoyGenerationReport:
    """Summarize decoy-generation outcomes and sequence-level caveats."""
    target_sequence_checksums = {record.sequence_checksum for record in input_records}
    unchanged_sequence_accessions = tuple(
        sorted(
            decoy.canonical_accession
            for target, decoy in zip(input_records, decoy_records, strict=False)
            if decoy.sequence_checksum == target.sequence_checksum
        )
    )
    target_sequence_collision_accessions = tuple(
        sorted(
            decoy.canonical_accession
            for decoy in decoy_records
            if decoy.sequence_checksum in target_sequence_checksums
        )
    )
    return DecoyGenerationReport(
        decoy_mode=mode,
        prefix=prefix,
        seed=seed,
        input_target_count=len(input_records),
        generated_decoy_count=len(decoy_records),
        unchanged_sequence_count=len(unchanged_sequence_accessions),
        target_sequence_collision_count=len(target_sequence_collision_accessions),
        unchanged_sequence_accessions=unchanged_sequence_accessions,
        target_sequence_collision_accessions=target_sequence_collision_accessions,
        valid=len(input_records) == len(decoy_records),
    )


def _validate_decoy_generation_inputs(
    records: tuple[NormalizedProteinRecord, ...],
    *,
    prefix: str,
) -> None:
    existing_decoys = tuple(
        sorted(record.canonical_accession for record in records if record.decoy)
    )
    if existing_decoys:
        joined = ", ".join(existing_decoys)
        raise ValueError(
            f"decoy generation requires target-only inputs; found decoy records: {joined}"
        )

    stable_accessions = {_stable_record_accession(record) for record in records}
    generated_accessions = {
        _stable_generated_accession(record, prefix=prefix) for record in records
    }
    colliding_accessions = tuple(sorted(stable_accessions & generated_accessions))
    if colliding_accessions:
        joined = ", ".join(colliding_accessions)
        raise ValueError(
            "decoy generation prefix would collide with existing target accessions: "
            f"{joined}"
        )


def generate_decoy_database(
    records: tuple[NormalizedProteinRecord, ...],
    *,
    mode: DecoyGenerationMode = DecoyGenerationMode.REVERSE,
    prefix: str = "DECOY_",
    seed: int = 17,
) -> tuple[NormalizedProteinRecord, ...]:
    """Generate one decoy record per input record."""
    _validate_decoy_generation_inputs(records, prefix=prefix)
    generated: list[NormalizedProteinRecord] = []
    for index, record in enumerate(records):
        if mode is DecoyGenerationMode.REVERSE:
            decoy_sequence = record.residues[::-1]
        else:
            rng = random.Random(f"{seed}:{record.sequence_checksum}:{index}")
            residues = list(record.residues)
            if len(set(residues)) > 1:
                while True:
                    rng.shuffle(residues)
                    candidate = "".join(residues)
                    if candidate != record.residues:
                        decoy_sequence = candidate
                        break
            else:
                decoy_sequence = record.residues
        generated.append(
            record.model_copy(
                update={
                    "source_header": f"{prefix}{record.source_header}",
                    "source_identifier": f"{prefix}{record.source_identifier}",
                    "canonical_accession": f"{prefix}{record.canonical_accession}",
                    "display_name": f"{prefix}{record.display_name}",
                    "residues": decoy_sequence,
                    "residue_count": len(decoy_sequence),
                    "sequence_checksum": sequence_checksum(decoy_sequence),
                    "decoy": True,
                    "validation_issues": (),
                }
            )
        )
    return tuple(generated)


def generate_decoy_records(
    records: tuple[NormalizedProteinRecord, ...],
    *,
    mode: DecoyGenerationMode = DecoyGenerationMode.REVERSE,
    prefix: str = "DECOY_",
    seed: int = 17,
) -> tuple[NormalizedProteinRecord, ...]:
    """Compatibility wrapper for decoy generation over normalized records."""
    return generate_decoy_database(
        records,
        mode=mode,
        prefix=prefix,
        seed=seed,
    )


def validate_target_decoy_database(
    records: tuple[NormalizedProteinRecord, ...], *, prefix: str = "DECOY_"
) -> TargetDecoyValidationReport:
    """Validate that each target has exactly one matching decoy."""
    target_map: dict[str, NormalizedProteinRecord] = {}
    decoy_keys: list[str] = []
    duplicate_decoys: list[str] = []

    for record in records:
        if record.canonical_accession.startswith(prefix):
            decoy_key = _normalize_decoy_key(
                record.canonical_accession.removeprefix(prefix)
            )
            if decoy_key in decoy_keys:
                duplicate_decoys.append(record.canonical_accession)
            decoy_keys.append(decoy_key)
        else:
            target_map[_normalize_decoy_key(record.canonical_accession)] = record

    decoy_counts = Counter(decoy_keys)
    missing_decoys = sorted(
        accession for accession in target_map if decoy_counts[accession] == 0
    )
    orphan_decoys = sorted(
        accession for accession in decoy_counts if accession not in target_map
    )
    return TargetDecoyValidationReport(
        prefix=prefix,
        target_count=len(target_map),
        decoy_count=len(decoy_keys),
        missing_decoys=tuple(missing_decoys),
        duplicate_decoys=tuple(sorted(duplicate_decoys)),
        orphan_decoys=tuple(orphan_decoys),
        valid=not missing_decoys
        and not duplicate_decoys
        and not orphan_decoys
        and len(target_map) == len(decoy_keys),
    )


def render_records_fasta(records: tuple[NormalizedProteinRecord, ...]) -> str:
    """Render normalized records back into FASTA text."""
    lines: list[str] = []
    for record in records:
        lines.append(f">{record.source_header}")
        lines.extend(
            record.residues[index : index + 60]
            for index in range(0, len(record.residues), 60)
        )
    return "\n".join(lines) + ("\n" if lines else "")


def render_fasta_records(records: tuple[NormalizedProteinRecord, ...]) -> str:
    """Compatibility wrapper for the legacy FASTA renderer name."""

    return render_records_fasta(records)


def parse_uniprot_accession(value: str) -> UniProtAccession:
    """Normalize one UniProt accession token, preserving isoform suffixes."""
    token = value.strip().upper()
    match = _UNIPROT_ACCESSION_RE.fullmatch(token)
    if match is None:
        raise ValueError("value must be a valid UniProt accession")
    isoform = match.group("isoform")
    return UniProtAccession(
        accession=match.group("accession"),
        isoform=int(isoform) if isoform is not None else None,
    )


def canonicalize_protein_reference(value: str) -> str:
    """Normalize one protein reference token onto the canonical accession surface."""

    _namespace, canonical_accession, _isoform = _normalize_accession(value)
    return canonical_accession


def _parse_raw_fasta_records(payload: str) -> tuple[FastaSequenceRecord, ...]:
    records: list[FastaSequenceRecord] = []
    current_header: str | None = None
    current_residues: list[str] = []

    for raw_line in payload.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(">"):
            if current_header is not None:
                records.append(_build_fasta_record(current_header, current_residues))
            current_header = line[1:].strip()
            if not current_header:
                raise ValueError("FASTA headers must contain an identifier")
            current_residues = []
            continue
        if current_header is None:
            raise ValueError("FASTA payload must begin with a header line")
        current_residues.append(line)

    if current_header is not None:
        records.append(_build_fasta_record(current_header, current_residues))
    return tuple(records)


def _build_fasta_record(header: str, residues: list[str]) -> FastaSequenceRecord:
    sequence = "".join(part.strip() for part in residues if part.strip())
    identifier, _, description = header.partition(" ")
    return FastaSequenceRecord(
        header=header,
        identifier=identifier,
        description=description.strip(),
        residues=sequence,
    )


def _duplicate_identifiers(
    identifiers: list[str] | tuple[str, ...] | object,
) -> set[str]:
    if not isinstance(identifiers, Iterable) or isinstance(identifiers, str):
        return set()
    counts: Counter[str] = Counter(str(identifier) for identifier in identifiers)
    return {identifier for identifier, count in counts.items() if count > 1}


def _duplicate_accessions(
    accessions: Iterable[str],
) -> set[str]:
    counts: Counter[str] = Counter(accessions)
    return {accession for accession, count in counts.items() if count > 1}


def _normalize_accession(identifier: str) -> tuple[str, str, int | None]:
    token = identifier.strip()
    decoy_prefix = next(
        (prefix for prefix in _DECOY_PREFIXES if token.upper().startswith(prefix)),
        "",
    )
    normalized_token = token[len(decoy_prefix) :] if decoy_prefix else token
    if "|" in normalized_token:
        parts = normalized_token.split("|")
        if len(parts) >= 3 and parts[0] in {"sp", "tr"}:
            accession = parse_uniprot_accession(parts[1])
            return "uniprot", f"{decoy_prefix}{accession.accession}", accession.isoform
        if len(parts) >= 3 and parts[0] in {"ref", "gb"}:
            refseq = parts[1].upper()
            if _REFSEQ_ACCESSION_RE.fullmatch(refseq):
                return "refseq", f"{decoy_prefix}{refseq}", None
    candidate = normalized_token.upper()
    if _UNIPROT_ACCESSION_RE.fullmatch(candidate):
        accession = parse_uniprot_accession(candidate)
        return "uniprot", f"{decoy_prefix}{accession.accession}", accession.isoform
    if _REFSEQ_ACCESSION_RE.fullmatch(candidate):
        return "refseq", f"{decoy_prefix}{candidate}", None
    if match := _ENSEMBL_ACCESSION_RE.fullmatch(candidate):
        return "ensembl", f"{decoy_prefix}{match.group('accession')}", None
    return "custom", token, None


def _stable_accession_key_from_identifier(identifier: str) -> str:
    namespace, accession, isoform = _normalize_accession(identifier)
    if isoform is None:
        return f"{namespace}:{accession}"
    return f"{namespace}:{accession}-{isoform}"


def _extract_gene(record: FastaSequenceRecord) -> str | None:
    if match := _GENE_FIELD_RE.search(record.header):
        return match.group("gene")
    if match := _ENSEMBL_GENE_SYMBOL_RE.search(record.header):
        return match.group("gene")
    if record.identifier.startswith("sp|") or record.identifier.startswith("tr|"):
        parts = record.identifier.split("|")
        if len(parts) >= 3 and "_" in parts[2]:
            return parts[2].split("_", 1)[0]
    return None


def _extract_organism(record: FastaSequenceRecord) -> str | None:
    if match := _ORGANISM_FIELD_RE.search(record.header):
        return match.group("organism").strip()
    if record.description.endswith("]") and "[" in record.description:
        return record.description.rsplit("[", 1)[1].rstrip("]").strip()
    return None


def _extract_description(record: FastaSequenceRecord) -> str:
    if record.identifier.startswith(("sp|", "tr|")):
        parts = record.header.split(" ", 1)
        description = parts[1] if len(parts) == 2 else ""
        description = re.split(r"\s(?:OS|GN|OX|PE|SV)=", description, maxsplit=1)[0]
        return description.strip()
    if match := _ENSEMBL_DESCRIPTION_RE.search(record.header):
        return match.group("description").strip()
    if record.description.endswith("]") and "[" in record.description:
        return record.description.rsplit("[", 1)[0].strip()
    return record.description.strip()


def _build_display_name(
    record: FastaSequenceRecord, canonical_accession: str, gene: str | None
) -> str:
    if gene:
        return gene
    if record.identifier.startswith(("sp|", "tr|")):
        parts = record.identifier.split("|")
        if len(parts) >= 3:
            return parts[2]
    return canonical_accession


def _is_contaminant_record(record: FastaSequenceRecord) -> bool:
    header = record.header.upper()
    return header.startswith("CON__") or "CONTAMINANT" in header or "CRAP" in header


def _is_decoy_record(record: FastaSequenceRecord) -> bool:
    token = record.identifier.upper()
    return token.startswith(_DECOY_PREFIXES)


def _build_fasta_database_composition(
    records: tuple[NormalizedProteinRecord, ...],
) -> FastaDatabaseComposition:
    namespace_counts = Counter(record.accession_namespace for record in records)
    decoy_count = sum(1 for record in records if record.decoy)
    contaminant_count = sum(1 for record in records if record.contaminant)
    return FastaDatabaseComposition(
        accepted_record_count=len(records),
        target_count=len(records) - decoy_count,
        decoy_count=decoy_count,
        contaminant_count=contaminant_count,
        accession_namespace_counts=dict(sorted(namespace_counts.items())),
    )


def _normalize_decoy_key(value: str) -> str:
    return _normalize_accession(value)[1]
