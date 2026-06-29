# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""FASTA database profiling and export surfaces."""

from __future__ import annotations

from collections.abc import Iterable
import csv
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.sequences.fasta import (
    NormalizedProteinRecord,
    RejectedFastaRecord,
    SequenceValidationIssue,
    build_fasta_stats,
)
from bijux_proteomics_foundation import JsonModel

_LENGTH_BINS: tuple[tuple[str, int, int | None], ...] = (
    ("1-99", 1, 99),
    ("100-249", 100, 249),
    ("250-499", 250, 499),
    ("500-999", 500, 999),
    ("1000+", 1000, None),
)


class FastaProfileSummary(JsonModel):
    """High-level reviewer-facing FASTA database summary."""

    model_config = ConfigDict(extra="forbid")

    input_record_count: int = Field(..., ge=0)
    protein_count: int = Field(..., ge=0)
    rejected_record_count: int = Field(..., ge=0)
    unique_accession_count: int = Field(..., ge=0)
    target_count: int = Field(..., ge=0)
    decoy_count: int = Field(..., ge=0)
    contaminant_count: int = Field(..., ge=0)
    total_residues: int = Field(..., ge=0)
    min_length: int | None = None
    median_length: float | None = None
    max_length: int | None = None
    organism_annotated_count: int = Field(..., ge=0)
    organism_missing_count: int = Field(..., ge=0)
    accession_namespace_counts: dict[str, int] = Field(default_factory=dict)


class FastaLengthDistributionBin(JsonModel):
    """One length-bin row for FASTA composition review."""

    model_config = ConfigDict(extra="forbid")

    bin_label: str = Field(..., min_length=1)
    min_length: int = Field(..., ge=1)
    max_length: int | None = Field(default=None, ge=1)
    protein_count: int = Field(..., ge=0)
    residue_count: int = Field(..., ge=0)


class FastaOrganismProfileEntry(JsonModel):
    """One organism-level FASTA composition row."""

    model_config = ConfigDict(extra="forbid")

    organism: str = Field(..., min_length=1)
    protein_count: int = Field(..., ge=0)
    target_count: int = Field(..., ge=0)
    decoy_count: int = Field(..., ge=0)
    contaminant_count: int = Field(..., ge=0)


class FastaInvalidSequenceProfileEntry(JsonModel):
    """One rejected FASTA row with row-level invalid-sequence reasons."""

    model_config = ConfigDict(extra="forbid")

    source_identifier: str = Field(..., min_length=1)
    source_header: str = Field(..., min_length=1)
    primary_issue_code: str = Field(..., min_length=1)
    primary_issue_message: str = Field(..., min_length=1)
    issue_codes: tuple[str, ...] = Field(default_factory=tuple)
    issue_messages: tuple[str, ...] = Field(default_factory=tuple)


class FastaDatabaseProfile(JsonModel):
    """Full FASTA database profile with summary and ledgers."""

    model_config = ConfigDict(extra="forbid")

    summary: FastaProfileSummary
    length_distribution: tuple[FastaLengthDistributionBin, ...] = Field(
        default_factory=tuple
    )
    organism_distribution: tuple[FastaOrganismProfileEntry, ...] = Field(
        default_factory=tuple
    )
    invalid_sequence_report: tuple[FastaInvalidSequenceProfileEntry, ...] = Field(
        default_factory=tuple
    )


def build_fasta_database_profile(
    records: tuple[NormalizedProteinRecord, ...],
    *,
    rejected_records: tuple[RejectedFastaRecord, ...] = (),
) -> FastaDatabaseProfile:
    """Build a full FASTA profile for search and digestion review."""
    stats = build_fasta_stats(records, rejected_records=rejected_records)
    organism_annotated_count = sum(1 for record in records if record.organism)
    summary = FastaProfileSummary(
        input_record_count=len(records) + len(rejected_records),
        protein_count=stats.total_records,
        rejected_record_count=len(rejected_records),
        unique_accession_count=stats.unique_accessions,
        target_count=stats.target_count,
        decoy_count=stats.decoy_count,
        contaminant_count=stats.contaminant_count,
        total_residues=stats.total_residues,
        min_length=stats.min_length,
        median_length=stats.median_length,
        max_length=stats.max_length,
        organism_annotated_count=organism_annotated_count,
        organism_missing_count=len(records) - organism_annotated_count,
        accession_namespace_counts=dict(stats.accession_namespace_counts),
    )
    return FastaDatabaseProfile(
        summary=summary,
        length_distribution=_build_length_distribution(records),
        organism_distribution=_build_organism_distribution(records),
        invalid_sequence_report=_build_invalid_sequence_report(rejected_records),
    )


def render_fasta_profile_summary_tsv(profile: FastaDatabaseProfile) -> str:
    """Render the profile summary as a one-row TSV table."""
    summary = profile.summary
    namespace_counts = ",".join(
        f"{namespace}:{count}"
        for namespace, count in sorted(summary.accession_namespace_counts.items())
    )
    return _render_tsv(
        (
            "input_record_count",
            "protein_count",
            "rejected_record_count",
            "unique_accession_count",
            "target_count",
            "decoy_count",
            "contaminant_count",
            "total_residues",
            "min_length",
            "median_length",
            "max_length",
            "organism_annotated_count",
            "organism_missing_count",
            "accession_namespace_counts",
        ),
        (
            (
                summary.input_record_count,
                summary.protein_count,
                summary.rejected_record_count,
                summary.unique_accession_count,
                summary.target_count,
                summary.decoy_count,
                summary.contaminant_count,
                summary.total_residues,
                summary.min_length if summary.min_length is not None else "",
                summary.median_length if summary.median_length is not None else "",
                summary.max_length if summary.max_length is not None else "",
                summary.organism_annotated_count,
                summary.organism_missing_count,
                namespace_counts,
            ),
        ),
    )


def render_fasta_profile_length_distribution_tsv(profile: FastaDatabaseProfile) -> str:
    """Render length-distribution bins as TSV."""
    return _render_tsv(
        ("bin_label", "min_length", "max_length", "protein_count", "residue_count"),
        (
            (
                row.bin_label,
                row.min_length,
                row.max_length if row.max_length is not None else "",
                row.protein_count,
                row.residue_count,
            )
            for row in profile.length_distribution
        ),
    )


def render_fasta_profile_organism_distribution_tsv(
    profile: FastaDatabaseProfile,
) -> str:
    """Render organism distribution rows as TSV."""
    return _render_tsv(
        (
            "organism",
            "protein_count",
            "target_count",
            "decoy_count",
            "contaminant_count",
        ),
        (
            (
                row.organism,
                row.protein_count,
                row.target_count,
                row.decoy_count,
                row.contaminant_count,
            )
            for row in profile.organism_distribution
        ),
    )


def render_fasta_profile_invalid_sequence_tsv(profile: FastaDatabaseProfile) -> str:
    """Render rejected invalid-sequence rows as TSV."""
    return _render_tsv(
        (
            "source_identifier",
            "source_header",
            "primary_issue_code",
            "primary_issue_message",
            "issue_codes",
            "issue_messages",
        ),
        (
            (
                row.source_identifier,
                row.source_header,
                row.primary_issue_code,
                row.primary_issue_message,
                "|".join(row.issue_codes),
                "|".join(row.issue_messages),
            )
            for row in profile.invalid_sequence_report
        ),
    )


def _build_length_distribution(
    records: tuple[NormalizedProteinRecord, ...],
) -> tuple[FastaLengthDistributionBin, ...]:
    rows: list[FastaLengthDistributionBin] = []
    for label, minimum, maximum in _LENGTH_BINS:
        members = [
            record
            for record in records
            if record.residue_count >= minimum
            and (maximum is None or record.residue_count <= maximum)
        ]
        rows.append(
            FastaLengthDistributionBin(
                bin_label=label,
                min_length=minimum,
                max_length=maximum,
                protein_count=len(members),
                residue_count=sum(record.residue_count for record in members),
            )
        )
    return tuple(rows)


def _build_organism_distribution(
    records: tuple[NormalizedProteinRecord, ...],
) -> tuple[FastaOrganismProfileEntry, ...]:
    grouped: dict[str, list[NormalizedProteinRecord]] = {}
    for record in records:
        if record.organism is None:
            continue
        grouped.setdefault(record.organism, []).append(record)
    ordered = sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0]))
    return tuple(
        FastaOrganismProfileEntry(
            organism=organism,
            protein_count=len(members),
            target_count=sum(1 for record in members if not record.decoy),
            decoy_count=sum(1 for record in members if record.decoy),
            contaminant_count=sum(1 for record in members if record.contaminant),
        )
        for organism, members in ordered
    )


def _build_invalid_sequence_report(
    rejected_records: tuple[RejectedFastaRecord, ...],
) -> tuple[FastaInvalidSequenceProfileEntry, ...]:
    rows: list[FastaInvalidSequenceProfileEntry] = []
    for rejected in rejected_records:
        sequence_issues = tuple(
            issue for issue in rejected.issues if issue.code != "duplicate_accession"
        )
        if not sequence_issues:
            continue
        primary_issue = _select_primary_invalid_sequence_issue(sequence_issues)
        rows.append(
            FastaInvalidSequenceProfileEntry(
                source_identifier=rejected.source_identifier,
                source_header=rejected.source_header,
                primary_issue_code=primary_issue.code,
                primary_issue_message=primary_issue.message,
                issue_codes=tuple(issue.code for issue in sequence_issues),
                issue_messages=tuple(issue.message for issue in sequence_issues),
            )
        )
    return tuple(rows)


def _select_primary_invalid_sequence_issue(
    issues: tuple[SequenceValidationIssue, ...],
) -> SequenceValidationIssue:
    preferred_codes = (
        "empty_sequence",
        "invalid_character",
        "stop_codon",
        "ambiguous_residue",
        "unsupported_residue",
    )
    for code in preferred_codes:
        for issue in issues:
            if issue.code == code:
                return issue
    return issues[0]


def _render_tsv(
    header: tuple[str, ...],
    rows: Iterable[tuple[object, ...]],
) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(header)
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue()
