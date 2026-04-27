# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Protein sequence domain models."""

from __future__ import annotations

from dataclasses import dataclass
import re

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics_foundation import JsonModel, TargetId

_SEQUENCE_RE = re.compile(r"^[ACDEFGHIKLMNPQRSTVWY]+$")
_UNIPROT_ACCESSION_RE = re.compile(
    r"^(?P<accession>(?:[OPQ][0-9][A-Z0-9]{3}[0-9])|(?:[A-NR-Z][0-9][A-Z][A-Z0-9]{2}[0-9]))(?:-(?P<isoform>[1-9][0-9]*))?$"
)


@dataclass(frozen=True)
class FastaSequenceRecord:
    """One parsed FASTA record before it is promoted into a target-bound model."""

    header: str
    identifier: str
    description: str
    residues: str


@dataclass(frozen=True)
class UniProtAccession:
    """Normalized UniProt accession with optional isoform suffix."""

    accession: str
    isoform: int | None = None


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
        if not _SEQUENCE_RE.fullmatch(sequence):
            raise ValueError("residues must contain only canonical amino-acid symbols")
        return sequence


def sequence_length(sequence: ProteinSequence) -> int:
    """Return the amino-acid length of a canonical sequence."""
    return len(sequence.residues)


def parse_fasta_records(payload: str) -> tuple[FastaSequenceRecord, ...]:
    """Parse one FASTA payload into stable sequence records."""
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


def _build_fasta_record(
    header: str, residues: list[str]
) -> FastaSequenceRecord:
    sequence = "".join(part.strip().upper() for part in residues if part.strip())
    if not sequence:
        raise ValueError(f"FASTA record {header!r} must contain sequence residues")
    if not _SEQUENCE_RE.fullmatch(sequence):
        raise ValueError(
            f"FASTA record {header!r} contains non-canonical amino-acid symbols"
        )
    identifier, _, description = header.partition(" ")
    return FastaSequenceRecord(
        header=header,
        identifier=identifier,
        description=description.strip(),
        residues=sequence,
    )
