# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable digestion contracts and peptide indexing models."""

from __future__ import annotations

from enum import StrEnum
import re
from typing import Literal

from pydantic import ConfigDict, Field, field_validator, model_validator

from bijux_proteomics_foundation import DocumentSchema, JsonModel


class ProteaseCleavageMode(StrEnum):
    """Direction for protease cleavage semantics."""

    C_TERMINAL = "c_terminal"
    N_TERMINAL = "n_terminal"


class ProteaseRule(JsonModel):
    """Stable cleavage contract for one protease."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1)
    cleavage_mode: ProteaseCleavageMode = ProteaseCleavageMode.C_TERMINAL
    cleavage_residues: str = ""
    blocked_by_next: str = ""
    blocked_by_previous: str = ""
    cleavage_pattern: str | None = None
    cleavage_cut_side: Literal["before", "after"] | None = None
    cleavage_group: str | None = None
    description: str = ""

    @field_validator("cleavage_residues", "blocked_by_next", "blocked_by_previous")
    @classmethod
    def _normalize_residue_token(cls, value: str) -> str:
        return "".join(sorted(set(value.strip().upper())))

    @model_validator(mode="after")
    def _validate_cleavage_contract(self) -> ProteaseRule:
        has_pattern = self.cleavage_pattern is not None and self.cleavage_pattern != ""
        has_residues = self.cleavage_residues != ""
        if has_pattern == has_residues:
            raise ValueError(
                "protease rules must define exactly one of cleavage_residues or cleavage_pattern"
            )
        if not has_pattern:
            if self.cleavage_cut_side is not None or self.cleavage_group is not None:
                raise ValueError(
                    "residue-based protease rules cannot define regex cleavage cut controls"
                )
            return self
        if self.cleavage_cut_side is None:
            raise ValueError(
                "regex protease rules must define cleavage_cut_side as 'before' or 'after'"
            )
        if self.blocked_by_next or self.blocked_by_previous:
            raise ValueError(
                "regex protease rules must encode blocking behavior inside cleavage_pattern"
            )
        cleavage_pattern = self.cleavage_pattern
        if cleavage_pattern is None:
            raise ValueError("regex protease rules must declare cleavage_pattern")
        try:
            compiled = re.compile(cleavage_pattern)
        except re.error as exc:
            raise ValueError(
                f"invalid regex cleavage_pattern {cleavage_pattern!r}: {exc}"
            ) from exc
        cleavage_group = self.cleavage_group
        if cleavage_group is not None and cleavage_group not in ("", "0"):
            if cleavage_group.isdigit():
                if int(cleavage_group) > compiled.groups:
                    raise ValueError(
                        f"regex cleavage_group {cleavage_group!r} is not present in cleavage_pattern"
                    )
            elif cleavage_group not in compiled.groupindex:
                raise ValueError(
                    f"regex cleavage_group {cleavage_group!r} is not present in cleavage_pattern"
                )
        return self


class PeptideDigestionMode(StrEnum):
    """Supported peptide digestion strategies."""

    FULL = "full"
    SEMI_SPECIFIC = "semi_specific"
    NON_SPECIFIC = "non_specific"


class DigestedPeptide(JsonModel):
    """One peptide generated from protein digestion."""

    model_config = ConfigDict(extra="forbid")

    source_accession: str = Field(..., min_length=1)
    source_identifier: str = Field(..., min_length=1)
    source_protein_family: str = Field(..., min_length=1)
    source_isoform: int | None = Field(default=None, ge=1)
    sequence: str = Field(..., min_length=1)
    start: int = Field(..., ge=1)
    end: int = Field(..., ge=1)
    missed_cleavages: int = Field(default=0, ge=0)
    protease: str = Field(..., min_length=1)
    digestion_mode: PeptideDigestionMode
    cleavage_type: Literal["enzymatic", "semi_specific", "non_specific"] = "enzymatic"

    @field_validator("sequence")
    @classmethod
    def _normalize_sequence(cls, value: str) -> str:
        return value.strip().upper()


class PeptideFilterReport(JsonModel):
    """Accounting for peptide-level post-digestion filtering."""

    model_config = ConfigDict(extra="forbid")

    input_peptides: int = Field(..., ge=0)
    output_peptides: int = Field(..., ge=0)
    excluded_by_length: int = Field(default=0, ge=0)
    excluded_by_mass: int = Field(default=0, ge=0)


class DigestDuplicateSequenceEntry(JsonModel):
    """One repeated peptide sequence with explicit occurrence accounting."""

    model_config = ConfigDict(extra="forbid")

    sequence: str = Field(..., min_length=1)
    occurrence_count: int = Field(..., ge=2)
    protein_accessions: tuple[str, ...] = Field(default_factory=tuple)


class DigestDuplicateAccounting(JsonModel):
    """Honest peptide duplicate accounting for one digestion result."""

    model_config = ConfigDict(extra="forbid")

    total_peptide_occurrences: int = Field(..., ge=0)
    unique_sequence_count: int = Field(..., ge=0)
    duplicate_sequence_count: int = Field(..., ge=0)
    duplicate_occurrence_count: int = Field(..., ge=0)
    repeated_sequences: tuple[DigestDuplicateSequenceEntry, ...] = Field(
        default_factory=tuple
    )


class PeptideUniqueness(StrEnum):
    """Classification of peptide uniqueness across proteins."""

    UNIQUE = "unique"
    SHARED_ISOFORM_FAMILY = "shared_isoform_family"
    SHARED = "shared"


class PeptideUniquenessEntry(JsonModel):
    """One peptide uniqueness classification entry."""

    model_config = ConfigDict(extra="forbid")

    sequence: str = Field(..., min_length=1)
    protein_accessions: tuple[str, ...] = Field(default_factory=tuple)
    protein_families: tuple[str, ...] = Field(default_factory=tuple)
    uniqueness: PeptideUniqueness


class PeptideProteinIndexEntry(JsonModel):
    """Index entry from peptide sequence to source proteins and positions."""

    model_config = ConfigDict(extra="forbid")

    sequence: str = Field(..., min_length=1)
    protein_accessions: tuple[str, ...] = Field(default_factory=tuple)
    protein_families: tuple[str, ...] = Field(default_factory=tuple)
    source_identifiers: tuple[str, ...] = Field(default_factory=tuple)
    coordinates: tuple[PeptideOriginCoordinate, ...] = Field(default_factory=tuple)
    uniqueness: PeptideUniqueness


class PeptideOriginCoordinate(JsonModel):
    """One peptide origin coordinate with preserved accession family metadata."""

    model_config = ConfigDict(extra="forbid")

    protein_accession: str = Field(..., min_length=1)
    protein_family: str = Field(..., min_length=1)
    source_identifier: str = Field(..., min_length=1)
    start: int = Field(..., ge=1)
    end: int = Field(..., ge=1)
    isoform: int | None = Field(default=None, ge=1)


class DigestPolicy(JsonModel):
    """Stable digestion assumptions that must survive export and rerun."""

    model_config = ConfigDict(extra="forbid")

    protease: str = Field(..., min_length=1)
    cleavage_mode: ProteaseCleavageMode
    cleavage_residues: str = ""
    blocked_by_next: str = ""
    blocked_by_previous: str = ""
    cleavage_pattern: str | None = None
    cleavage_cut_side: Literal["before", "after"] | None = None
    cleavage_group: str | None = None
    digestion_mode: PeptideDigestionMode
    missed_cleavages: int = Field(..., ge=0)
    min_length: int | None = None
    max_length: int | None = None
    min_mass: float | None = None
    max_mass: float | None = None


class PeptideDigestManifest(JsonModel):
    """Stable manifest for one digestion job."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    digest_policy: DigestPolicy
    policy_hash: str = Field(..., min_length=64, max_length=64)
    protease: str = Field(..., min_length=1)
    digestion_mode: PeptideDigestionMode
    missed_cleavages: int = Field(..., ge=0)
    min_length: int | None = None
    max_length: int | None = None
    min_mass: float | None = None
    max_mass: float | None = None
    source_path: str | None = None
    source_sha256: str | None = None
    input_record_count: int = Field(..., ge=0)
    output_peptide_count: int = Field(..., ge=0)
    output_sha256: str = Field(..., min_length=64, max_length=64)


class DigestBenchmarkReport(JsonModel):
    """Measured digestion benchmark summary."""

    model_config = ConfigDict(extra="forbid")

    protein_count: int = Field(..., ge=0)
    total_residues: int = Field(..., ge=0)
    peptide_count: int = Field(..., ge=0)
    elapsed_seconds: float = Field(..., ge=0.0)
    peak_memory_bytes: int | None = Field(default=None, ge=0)
    peptides_per_second: float = Field(..., ge=0.0)


__all__ = [
    "DigestBenchmarkReport",
    "DigestDuplicateAccounting",
    "DigestDuplicateSequenceEntry",
    "DigestPolicy",
    "DigestedPeptide",
    "PeptideDigestionMode",
    "PeptideDigestManifest",
    "PeptideFilterReport",
    "PeptideOriginCoordinate",
    "PeptideProteinIndexEntry",
    "PeptideUniqueness",
    "PeptideUniquenessEntry",
    "ProteaseCleavageMode",
    "ProteaseRule",
]
