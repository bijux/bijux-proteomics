# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Protein digestion and peptide indexing contracts."""

from __future__ import annotations

from enum import StrEnum
import hashlib
import json
from pathlib import Path
import re
from typing import Literal

from pydantic import ConfigDict, Field, field_validator, model_validator

from bijux_proteomics.chemistry import calculate_monoisotopic_peptide_mass
from bijux_proteomics_foundation import DocumentSchema, JsonModel
from bijux_proteomics_foundation.outcomes.optional_dependencies import (
    import_optional_module,
)


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
        try:
            compiled = re.compile(self.cleavage_pattern)
        except re.error as exc:
            raise ValueError(
                f"invalid regex cleavage_pattern {self.cleavage_pattern!r}: {exc}"
            ) from exc
        if self.cleavage_group not in (None, "", "0"):
            if self.cleavage_group.isdigit():
                if int(self.cleavage_group) > compiled.groups:
                    raise ValueError(
                        f"regex cleavage_group {self.cleavage_group!r} is not present in cleavage_pattern"
                    )
            elif self.cleavage_group not in compiled.groupindex:
                raise ValueError(
                    f"regex cleavage_group {self.cleavage_group!r} is not present in cleavage_pattern"
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


_PROTEASE_REGISTRY: dict[str, ProteaseRule] = {
    "trypsin": ProteaseRule(
        name="trypsin",
        cleavage_mode=ProteaseCleavageMode.C_TERMINAL,
        cleavage_residues="KR",
        blocked_by_next="P",
        description="Cleaves after lysine or arginine unless followed by proline.",
    ),
    "lysc": ProteaseRule(
        name="lysc",
        cleavage_mode=ProteaseCleavageMode.C_TERMINAL,
        cleavage_residues="K",
        blocked_by_next="P",
        description="Cleaves after lysine unless followed by proline.",
    ),
    "argc": ProteaseRule(
        name="argc",
        cleavage_mode=ProteaseCleavageMode.C_TERMINAL,
        cleavage_residues="R",
        blocked_by_next="P",
        description="Cleaves after arginine unless followed by proline.",
    ),
    "gluc": ProteaseRule(
        name="gluc",
        cleavage_mode=ProteaseCleavageMode.C_TERMINAL,
        cleavage_residues="E",
        blocked_by_next="P",
        description="Cleaves after glutamate unless followed by proline.",
    ),
    "chymotrypsin": ProteaseRule(
        name="chymotrypsin",
        cleavage_mode=ProteaseCleavageMode.C_TERMINAL,
        cleavage_residues="FWYL",
        blocked_by_next="P",
        description="Cleaves after aromatic residues unless followed by proline.",
    ),
    "aspn": ProteaseRule(
        name="aspn",
        cleavage_mode=ProteaseCleavageMode.N_TERMINAL,
        cleavage_residues="D",
        blocked_by_previous="P",
        description="Cleaves before aspartate unless preceded by proline.",
    ),
}


def protease_registry() -> dict[str, ProteaseRule]:
    """Return the built-in protease rule registry."""
    return dict(_PROTEASE_REGISTRY)


def get_protease_rule(name: str) -> ProteaseRule:
    """Return one built-in protease rule by normalized name."""
    normalized = name.strip().lower().replace("-", "").replace("_", "")
    try:
        return _PROTEASE_REGISTRY[normalized]
    except KeyError as exc:
        raise ValueError(f"unknown protease rule {name!r}") from exc


def resolve_protease_rule(
    name: str | None = None,
    *,
    custom_specification: str | None = None,
    custom_name: str = "custom",
) -> ProteaseRule:
    """Resolve either one built-in protease or one explicit custom rule."""
    has_name = name is not None and name.strip() != ""
    has_custom = custom_specification is not None and custom_specification.strip() != ""
    if has_name == has_custom:
        raise ValueError(
            "provide exactly one of a built-in protease name or a custom protease specification"
        )
    if has_custom:
        return parse_custom_protease_rule(
            str(custom_specification),
            name=custom_name,
        )
    if name is None:
        raise ValueError("protease name must be provided when no custom rule is used")
    return get_protease_rule(name)


def parse_custom_protease_rule(
    specification: str, *, name: str = "custom"
) -> ProteaseRule:
    """Parse a user-defined protease rule from a compact textual form."""
    # Supported keys:
    # - ``after`` or ``before`` for cleavage residues
    # - ``block_next`` for residues that block a C-terminal cut
    # - ``block_previous`` for residues that block an N-terminal cut
    # - ``pattern`` with ``cut_after`` or ``cut_before`` for regex-backed rules
    # - ``description`` for human-readable metadata

    fields: dict[str, str] = {}
    for fragment in specification.split(";"):
        token = fragment.strip()
        if not token:
            continue
        key, separator, value = token.partition("=")
        if not separator:
            raise ValueError(
                "custom protease rules must use key=value fragments separated by semicolons"
            )
        fields[key.strip().lower()] = value.strip()

    after = fields.get("after")
    before = fields.get("before")
    pattern = fields.get("pattern")
    cut_after = fields.get("cut_after")
    cut_before = fields.get("cut_before")

    has_residue_rule = bool(after) or bool(before)
    has_regex_rule = bool(pattern) or bool(cut_after) or bool(cut_before)
    if has_residue_rule and has_regex_rule:
        raise ValueError(
            "custom protease rule must use either residue keys or regex keys, not both"
        )
    if not has_residue_rule and not has_regex_rule:
        raise ValueError(
            "custom protease rule must define either residue cleavage keys or regex cleavage keys"
        )

    if has_regex_rule:
        if not pattern:
            raise ValueError("regex protease rules must define 'pattern'")
        if bool(cut_after) == bool(cut_before):
            raise ValueError(
                "regex protease rule must define exactly one of 'cut_after' or 'cut_before'"
            )
        if "block_next" in fields or "block_previous" in fields:
            raise ValueError(
                "regex protease rules must encode blocking behavior inside 'pattern'"
            )
        return ProteaseRule(
            name=name,
            cleavage_mode=(
                ProteaseCleavageMode.C_TERMINAL
                if cut_after is not None
                else ProteaseCleavageMode.N_TERMINAL
            ),
            cleavage_pattern=pattern,
            cleavage_cut_side="after" if cut_after is not None else "before",
            cleavage_group=(cut_after or cut_before or "0"),
            description=fields.get("description", ""),
        )

    if bool(after) == bool(before):
        raise ValueError(
            "custom protease rule must define exactly one of 'after' or 'before'"
        )
    cleavage_mode = (
        ProteaseCleavageMode.C_TERMINAL
        if after is not None
        else ProteaseCleavageMode.N_TERMINAL
    )
    cleavage_residues = after if after is not None else before
    if cleavage_residues is None:
        raise ValueError("custom protease rule must resolve to a cleavage residue set")
    return ProteaseRule(
        name=name,
        cleavage_mode=cleavage_mode,
        cleavage_residues=cleavage_residues,
        blocked_by_next=fields.get("block_next", ""),
        blocked_by_previous=fields.get("block_previous", ""),
        description=fields.get("description", ""),
    )


def filter_digested_peptides(
    peptides: tuple[DigestedPeptide, ...],
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    min_mass: float | None = None,
    max_mass: float | None = None,
) -> tuple[tuple[DigestedPeptide, ...], PeptideFilterReport]:
    """Filter digested peptides by sequence length."""
    filtered: list[DigestedPeptide] = []
    excluded_by_length = 0
    excluded_by_mass = 0
    for peptide in peptides:
        if min_length is not None and len(peptide.sequence) < min_length:
            excluded_by_length += 1
            continue
        if max_length is not None and len(peptide.sequence) > max_length:
            excluded_by_length += 1
            continue
        mass = _peptide_neutral_mass(peptide.sequence)
        if min_mass is not None and mass < min_mass:
            excluded_by_mass += 1
            continue
        if max_mass is not None and mass > max_mass:
            excluded_by_mass += 1
            continue
        filtered.append(peptide)
    return tuple(filtered), PeptideFilterReport(
        input_peptides=len(peptides),
        output_peptides=len(filtered),
        excluded_by_length=excluded_by_length,
        excluded_by_mass=excluded_by_mass,
    )


def classify_peptide_uniqueness(
    peptides: tuple[DigestedPeptide, ...],
) -> tuple[PeptideUniquenessEntry, ...]:
    """Classify peptides as unique or shared across parent proteins."""
    sequence_to_peptides: dict[str, list[DigestedPeptide]] = {}
    for peptide in peptides:
        sequence_to_peptides.setdefault(peptide.sequence, []).append(peptide)

    entries = [
        PeptideUniquenessEntry(
            sequence=sequence,
            protein_accessions=tuple(
                sorted({peptide.source_accession for peptide in members})
            ),
            protein_families=tuple(
                sorted({peptide.source_protein_family for peptide in members})
            ),
            uniqueness=_classify_peptide_uniqueness_members(members),
        )
        for sequence, members in sorted(sequence_to_peptides.items())
    ]
    return tuple(entries)


def build_digest_duplicate_accounting(
    peptides: tuple[DigestedPeptide, ...],
) -> DigestDuplicateAccounting:
    """Summarize repeated peptide sequences without hiding total occurrences."""
    grouped: dict[str, list[DigestedPeptide]] = {}
    for peptide in peptides:
        grouped.setdefault(peptide.sequence, []).append(peptide)

    repeated_sequences = tuple(
        DigestDuplicateSequenceEntry(
            sequence=sequence,
            occurrence_count=len(members),
            protein_accessions=tuple(
                sorted({member.source_accession for member in members})
            ),
        )
        for sequence, members in sorted(grouped.items())
        if len(members) > 1
    )
    return DigestDuplicateAccounting(
        total_peptide_occurrences=len(peptides),
        unique_sequence_count=len(grouped),
        duplicate_sequence_count=len(repeated_sequences),
        duplicate_occurrence_count=sum(
            entry.occurrence_count - 1 for entry in repeated_sequences
        ),
        repeated_sequences=repeated_sequences,
    )


def build_peptide_protein_index(
    peptides: tuple[DigestedPeptide, ...],
) -> tuple[PeptideProteinIndexEntry, ...]:
    """Build a stable peptide-to-protein index."""
    grouped: dict[str, list[DigestedPeptide]] = {}
    for peptide in peptides:
        grouped.setdefault(peptide.sequence, []).append(peptide)

    entries: list[PeptideProteinIndexEntry] = []
    for sequence, members in sorted(grouped.items()):
        accessions = tuple(sorted({member.source_accession for member in members}))
        protein_families = tuple(
            sorted({member.source_protein_family for member in members})
        )
        identifiers = tuple(sorted({member.source_identifier for member in members}))
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
        entries.append(
            PeptideProteinIndexEntry(
                sequence=sequence,
                protein_accessions=accessions,
                protein_families=protein_families,
                source_identifiers=identifiers,
                coordinates=coordinates,
                uniqueness=_classify_peptide_uniqueness_members(members),
            )
        )
    return tuple(entries)


def digest_protein_records(
    records: tuple[object, ...],
    *,
    protease: ProteaseRule | str = "trypsin",
    missed_cleavages: int = 0,
    mode: PeptideDigestionMode = PeptideDigestionMode.FULL,
    min_length: int = 1,
    max_length: int | None = None,
    min_mass: float | None = None,
    max_mass: float | None = None,
) -> tuple[DigestedPeptide, ...]:
    """Digest normalized protein records or FASTA-like records into peptides."""
    peptides: list[DigestedPeptide] = []
    for record in records:
        accession = getattr(record, "canonical_accession", None) or getattr(
            record, "identifier", None
        )
        identifier = getattr(record, "source_identifier", None) or getattr(
            record, "identifier", None
        )
        isoform = getattr(record, "isoform", None)
        residues = getattr(record, "residues", None)
        if accession is None or identifier is None or residues is None:
            raise TypeError(
                "digest_protein_records expects records with accession, identifier, and residues"
            )
        stable_accession = _stable_protein_accession(str(accession), isoform=isoform)
        peptides.extend(
            digest_sequence(
                residues,
                protease=protease,
                source_accession=stable_accession,
                source_identifier=str(identifier),
                source_protein_family=str(accession),
                source_isoform=isoform if isinstance(isoform, int) else None,
                missed_cleavages=missed_cleavages,
                mode=mode,
                min_length=min_length,
                max_length=max_length,
            )
        )
    filtered, _report = filter_digested_peptides(
        tuple(peptides),
        min_length=min_length,
        max_length=max_length,
        min_mass=min_mass,
        max_mass=max_mass,
    )
    return filtered


def digest_sequence(
    sequence: str,
    *,
    protease: ProteaseRule | str = "trypsin",
    source_accession: str = "sequence",
    source_identifier: str | None = None,
    source_protein_family: str | None = None,
    source_isoform: int | None = None,
    missed_cleavages: int = 0,
    mode: PeptideDigestionMode = PeptideDigestionMode.FULL,
    min_length: int = 1,
    max_length: int | None = None,
) -> tuple[DigestedPeptide, ...]:
    """Digest one sequence under the selected specificity mode."""
    normalized = sequence.strip().upper()
    rule = get_protease_rule(protease) if isinstance(protease, str) else protease
    boundaries = _full_digest_boundaries(normalized, rule)
    peptides: list[DigestedPeptide] = []
    identifier = source_identifier or source_accession
    protein_family = source_protein_family or source_accession
    max_peptide_length = max_length if max_length is not None else len(normalized)
    if mode is PeptideDigestionMode.NON_SPECIFIC:
        return _non_specific_digest(
            normalized,
            source_accession=source_accession,
            source_identifier=identifier,
            source_protein_family=protein_family,
            source_isoform=source_isoform,
            protease=rule.name,
            min_length=min_length,
            max_length=max_peptide_length,
        )
    if mode is PeptideDigestionMode.SEMI_SPECIFIC:
        return _semi_specific_digest(
            normalized,
            boundaries=boundaries,
            rule=rule,
            source_accession=source_accession,
            source_identifier=identifier,
            source_protein_family=protein_family,
            source_isoform=source_isoform,
            min_length=min_length,
            max_length=max_peptide_length,
        )
    for start_index, start in enumerate(boundaries[:-1]):
        max_span = min(missed_cleavages + 1, len(boundaries) - start_index - 1)
        for span in range(1, max_span + 1):
            end = boundaries[start_index + span]
            peptide = normalized[start:end]
            if (
                not peptide
                or len(peptide) < min_length
                or len(peptide) > max_peptide_length
            ):
                continue
            peptides.append(
                DigestedPeptide(
                    source_accession=source_accession,
                    source_identifier=identifier,
                    source_protein_family=protein_family,
                    source_isoform=source_isoform,
                    sequence=peptide,
                    start=start + 1,
                    end=end,
                    missed_cleavages=span - 1,
                    protease=rule.name,
                    digestion_mode=mode,
                    cleavage_type="enzymatic",
                )
            )
    return tuple(peptides)


def export_peptides_tsv(peptides: tuple[DigestedPeptide, ...], path: Path) -> Path:
    """Write a stable TSV export for digested peptides."""
    header = "\t".join(
        [
            "source_accession",
            "source_identifier",
            "sequence",
            "length",
            "start",
            "end",
            "missed_cleavages",
            "protease",
            "digestion_mode",
            "cleavage_type",
            "neutral_mass",
        ]
    )
    lines = [header]
    for peptide in peptides:
        neutral_mass = _peptide_neutral_mass(peptide.sequence)
        lines.append(
            "\t".join(
                [
                    peptide.source_accession,
                    peptide.source_identifier,
                    peptide.sequence,
                    str(len(peptide.sequence)),
                    str(peptide.start),
                    str(peptide.end),
                    str(peptide.missed_cleavages),
                    peptide.protease,
                    peptide.digestion_mode.value,
                    peptide.cleavage_type,
                    f"{neutral_mass:.5f}",
                ]
            )
        )
    path.write_text("\n".join(lines) + "\n")
    return path


def export_peptides_fasta(peptides: tuple[DigestedPeptide, ...], path: Path) -> Path:
    """Write one stable FASTA entry per peptide occurrence."""
    lines: list[str] = []
    for peptide in peptides:
        neutral_mass = _peptide_neutral_mass(peptide.sequence)
        lines.append(
            f">{peptide.source_accession}|{peptide.start}-{peptide.end}"
            f"|mc={peptide.missed_cleavages}"
            f"|len={len(peptide.sequence)}"
            f"|mass={neutral_mass:.5f}"
            f"|protease={peptide.protease}"
        )
        lines.append(peptide.sequence)
    path.write_text("\n".join(lines) + ("\n" if lines else ""))
    return path


def export_peptides_jsonl(peptides: tuple[DigestedPeptide, ...], path: Path) -> Path:
    """Write a stable JSONL export for digested peptides."""
    payload = []
    for peptide in peptides:
        entry = peptide.to_dict()
        entry["length"] = len(peptide.sequence)
        entry["neutral_mass"] = round(_peptide_neutral_mass(peptide.sequence), 5)
        payload.append(entry)
    path.write_text(
        "\n".join(json.dumps(entry, sort_keys=True) for entry in payload) + "\n"
    )
    return path


def export_peptides_parquet(peptides: tuple[DigestedPeptide, ...], path: Path) -> Path:
    """Write an optional Parquet export for digested peptides."""
    pa = import_optional_module(
        "pyarrow",
        dependency_name="pyarrow",
        feature_name="parquet peptide export",
        install_hint="pip install bijux-proteomics-core[parquet]",
    )
    pq = import_optional_module(
        "pyarrow.parquet",
        dependency_name="pyarrow",
        feature_name="parquet peptide export",
        install_hint="pip install bijux-proteomics-core[parquet]",
    )

    rows = []
    for peptide in peptides:
        rows.append(
            {
                "source_accession": peptide.source_accession,
                "source_identifier": peptide.source_identifier,
                "sequence": peptide.sequence,
                "length": len(peptide.sequence),
                "start": peptide.start,
                "end": peptide.end,
                "missed_cleavages": peptide.missed_cleavages,
                "protease": peptide.protease,
                "digestion_mode": peptide.digestion_mode.value,
                "cleavage_type": peptide.cleavage_type,
                "neutral_mass": round(_peptide_neutral_mass(peptide.sequence), 5),
            }
        )
    table = pa.Table.from_pylist(rows)
    pq.write_table(table, path)
    return path


def export_peptide_protein_table_tsv(
    peptides: tuple[DigestedPeptide, ...],
    path: Path,
) -> Path:
    """Write one stable peptide-to-protein occurrence table."""
    header = "\t".join(
        [
            "sequence",
            "length",
            "neutral_mass",
            "source_accession",
            "source_identifier",
            "source_protein_family",
            "source_isoform",
            "start",
            "end",
            "missed_cleavages",
            "protease",
            "digestion_mode",
            "cleavage_type",
        ]
    )
    lines = [header]
    for peptide in peptides:
        neutral_mass = _peptide_neutral_mass(peptide.sequence)
        lines.append(
            "\t".join(
                [
                    peptide.sequence,
                    str(len(peptide.sequence)),
                    f"{neutral_mass:.5f}",
                    peptide.source_accession,
                    peptide.source_identifier,
                    peptide.source_protein_family,
                    ""
                    if peptide.source_isoform is None
                    else str(peptide.source_isoform),
                    str(peptide.start),
                    str(peptide.end),
                    str(peptide.missed_cleavages),
                    peptide.protease,
                    peptide.digestion_mode.value,
                    peptide.cleavage_type,
                ]
            )
        )
    path.write_text("\n".join(lines) + "\n")
    return path


def peptide_export_fingerprint(peptides: tuple[DigestedPeptide, ...]) -> str:
    """Return a stable digest over peptide export content."""
    payload = [
        {
            "source_accession": peptide.source_accession,
            "source_identifier": peptide.source_identifier,
            "sequence": peptide.sequence,
            "length": len(peptide.sequence),
            "start": peptide.start,
            "end": peptide.end,
            "missed_cleavages": peptide.missed_cleavages,
            "protease": peptide.protease,
            "digestion_mode": peptide.digestion_mode.value,
            "cleavage_type": peptide.cleavage_type,
            "neutral_mass": round(_peptide_neutral_mass(peptide.sequence), 5),
        }
        for peptide in peptides
    ]
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()


def build_digest_policy(
    *,
    protease: ProteaseRule | str,
    digestion_mode: PeptideDigestionMode,
    missed_cleavages: int,
    min_length: int | None,
    max_length: int | None,
    min_mass: float | None,
    max_mass: float | None,
) -> DigestPolicy:
    """Build the stable digestion policy contract for one run."""
    rule = get_protease_rule(protease) if isinstance(protease, str) else protease
    return DigestPolicy(
        protease=rule.name,
        cleavage_mode=rule.cleavage_mode,
        cleavage_residues=rule.cleavage_residues,
        blocked_by_next=rule.blocked_by_next,
        blocked_by_previous=rule.blocked_by_previous,
        cleavage_pattern=rule.cleavage_pattern,
        cleavage_cut_side=rule.cleavage_cut_side,
        cleavage_group=rule.cleavage_group,
        digestion_mode=digestion_mode,
        missed_cleavages=missed_cleavages,
        min_length=min_length,
        max_length=max_length,
        min_mass=min_mass,
        max_mass=max_mass,
    )


def compute_digest_policy_hash(policy: DigestPolicy) -> str:
    """Return a stable hash over digestion assumptions."""
    return hashlib.sha256(
        json.dumps(policy.to_dict(), sort_keys=True).encode("utf-8")
    ).hexdigest()


def build_digest_manifest(
    *,
    peptides: tuple[DigestedPeptide, ...],
    protease: ProteaseRule | str,
    digestion_mode: PeptideDigestionMode,
    missed_cleavages: int,
    min_length: int | None,
    max_length: int | None,
    min_mass: float | None,
    max_mass: float | None,
    source_path: Path | None,
    input_record_count: int,
) -> PeptideDigestManifest:
    """Build a stable digestion manifest."""
    rule = get_protease_rule(protease) if isinstance(protease, str) else protease
    digest_policy = build_digest_policy(
        protease=rule,
        digestion_mode=digestion_mode,
        missed_cleavages=missed_cleavages,
        min_length=min_length,
        max_length=max_length,
        min_mass=min_mass,
        max_mass=max_mass,
    )
    source_sha256 = (
        hashlib.sha256(source_path.read_bytes()).hexdigest()
        if source_path is not None
        else None
    )
    schema = DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind="peptide_digest_manifest",
        package_name="bijux-proteomics-core",
        status="generated",
    )
    manifest = PeptideDigestManifest(
        document_schema=schema,
        digest_policy=digest_policy,
        policy_hash=compute_digest_policy_hash(digest_policy),
        protease=rule.name,
        digestion_mode=digestion_mode,
        missed_cleavages=missed_cleavages,
        min_length=min_length,
        max_length=max_length,
        min_mass=min_mass,
        max_mass=max_mass,
        source_path=str(source_path) if source_path is not None else None,
        source_sha256=source_sha256,
        input_record_count=input_record_count,
        output_peptide_count=len(peptides),
        output_sha256=peptide_export_fingerprint(peptides),
    )
    payload = manifest.to_dict()
    return manifest.model_copy(
        update={"document_schema": manifest.document_schema.with_content_hash(payload)}
    )


def build_digest_benchmark_report(
    *,
    protein_count: int,
    total_residues: int,
    peptides: tuple[DigestedPeptide, ...],
    elapsed_seconds: float,
    peak_memory_bytes: int | None = None,
) -> DigestBenchmarkReport:
    """Build an explicit digestion benchmark report."""
    return DigestBenchmarkReport(
        protein_count=protein_count,
        total_residues=total_residues,
        peptide_count=len(peptides),
        elapsed_seconds=elapsed_seconds,
        peak_memory_bytes=peak_memory_bytes,
        peptides_per_second=(
            len(peptides) / elapsed_seconds if elapsed_seconds > 0 else 0.0
        ),
    )


def count_missed_cleavages(
    sequence: str,
    protease: ProteaseRule | str,
) -> int:
    """Count internal missed-cleavage sites for one peptide sequence."""
    residues = sequence.strip().upper()
    if len(residues) < 2:
        return 0
    rule = resolve_protease_rule(protease) if isinstance(protease, str) else protease
    boundaries = _full_digest_boundaries(residues, rule)
    return max(0, len(boundaries) - 2)


def _classify_peptide_uniqueness_members(
    peptides: list[DigestedPeptide] | tuple[DigestedPeptide, ...],
) -> PeptideUniqueness:
    accessions = {peptide.source_accession for peptide in peptides}
    if len(accessions) == 1:
        return PeptideUniqueness.UNIQUE
    protein_families = {peptide.source_protein_family for peptide in peptides}
    if len(protein_families) == 1:
        return PeptideUniqueness.SHARED_ISOFORM_FAMILY
    return PeptideUniqueness.SHARED


def _full_digest_boundaries(sequence: str, rule: ProteaseRule) -> tuple[int, ...]:
    boundaries = [0]
    if not sequence:
        return (0,)
    if rule.cleavage_pattern is not None:
        boundaries.extend(_regex_digest_boundaries(sequence, rule))
        boundaries = sorted(set(boundaries))
        if boundaries[-1] != len(sequence):
            boundaries.append(len(sequence))
        return tuple(boundaries)

    if rule.cleavage_mode is ProteaseCleavageMode.C_TERMINAL:
        for index, residue in enumerate(sequence):
            if residue not in rule.cleavage_residues:
                continue
            next_residue = sequence[index + 1] if index + 1 < len(sequence) else None
            if next_residue is not None and next_residue in rule.blocked_by_next:
                continue
            boundaries.append(index + 1)
    else:
        for index, residue in enumerate(sequence):
            if residue not in rule.cleavage_residues:
                continue
            previous_residue = sequence[index - 1] if index > 0 else None
            if (
                previous_residue is not None
                and previous_residue in rule.blocked_by_previous
            ):
                continue
            if index not in boundaries:
                boundaries.append(index)

    if boundaries[-1] != len(sequence):
        boundaries.append(len(sequence))
    return tuple(boundaries)


def _regex_digest_boundaries(sequence: str, rule: ProteaseRule) -> tuple[int, ...]:
    if rule.cleavage_pattern is None or rule.cleavage_cut_side is None:
        return ()
    compiled = re.compile(rule.cleavage_pattern)
    group = rule.cleavage_group
    boundaries: list[int] = []
    for match in compiled.finditer(sequence):
        if rule.cleavage_cut_side == "after":
            boundary = match.end() if group in (None, "", "0") else match.end(group)
        else:
            boundary = (
                match.start() if group in (None, "", "0") else match.start(group)
            )
        if 0 < boundary < len(sequence):
            boundaries.append(boundary)
    return tuple(boundaries)


def _semi_specific_digest(
    sequence: str,
    *,
    boundaries: tuple[int, ...],
    rule: ProteaseRule,
    source_accession: str,
    source_identifier: str,
    source_protein_family: str,
    source_isoform: int | None,
    min_length: int,
    max_length: int,
) -> tuple[DigestedPeptide, ...]:
    peptides: list[DigestedPeptide] = []
    seen: set[tuple[int, int]] = set()
    enzymatic_bounds = set(boundaries)

    for start in boundaries[:-1]:
        for end in range(start + 1, len(sequence) + 1):
            cleavage_type: Literal["enzymatic", "semi_specific", "non_specific"]
            if end not in enzymatic_bounds:
                cleavage_type = "semi_specific"
            else:
                cleavage_type = "enzymatic"
            bounds = (start, end)
            if bounds in seen:
                continue
            length = end - start
            if length < min_length or length > max_length:
                continue
            seen.add(bounds)
            peptides.append(
                DigestedPeptide(
                    source_accession=source_accession,
                    source_identifier=source_identifier,
                    source_protein_family=source_protein_family,
                    source_isoform=source_isoform,
                    sequence=sequence[start:end],
                    start=start + 1,
                    end=end,
                    missed_cleavages=0,
                    protease=rule.name,
                    digestion_mode=PeptideDigestionMode.SEMI_SPECIFIC,
                    cleavage_type=cleavage_type,
                )
            )

    for start in range(len(sequence)):
        if start in enzymatic_bounds:
            continue
        for end in boundaries[1:]:
            if end <= start:
                continue
            bounds = (start, end)
            if bounds in seen:
                continue
            length = end - start
            if length < min_length or length > max_length:
                continue
            seen.add(bounds)
            peptides.append(
                DigestedPeptide(
                    source_accession=source_accession,
                    source_identifier=source_identifier,
                    source_protein_family=source_protein_family,
                    source_isoform=source_isoform,
                    sequence=sequence[start:end],
                    start=start + 1,
                    end=end,
                    missed_cleavages=0,
                    protease=rule.name,
                    digestion_mode=PeptideDigestionMode.SEMI_SPECIFIC,
                    cleavage_type="semi_specific",
                )
            )

    peptides.sort(key=lambda peptide: (peptide.start, peptide.end, peptide.sequence))
    return tuple(peptides)


def _non_specific_digest(
    sequence: str,
    *,
    source_accession: str,
    source_identifier: str,
    source_protein_family: str,
    source_isoform: int | None,
    protease: str,
    min_length: int,
    max_length: int,
) -> tuple[DigestedPeptide, ...]:
    peptides: list[DigestedPeptide] = []
    for start in range(len(sequence)):
        for end in range(
            start + min_length, min(len(sequence), start + max_length) + 1
        ):
            peptide = sequence[start:end]
            peptides.append(
                DigestedPeptide(
                    source_accession=source_accession,
                    source_identifier=source_identifier,
                    source_protein_family=source_protein_family,
                    source_isoform=source_isoform,
                    sequence=peptide,
                    start=start + 1,
                    end=end,
                    missed_cleavages=0,
                    protease=protease,
                    digestion_mode=PeptideDigestionMode.NON_SPECIFIC,
                    cleavage_type="non_specific",
                )
            )
    return tuple(peptides)


def _peptide_neutral_mass(sequence: str) -> float:
    return calculate_monoisotopic_peptide_mass(sequence)


def _stable_protein_accession(accession: str, *, isoform: int | None) -> str:
    if isoform is None:
        return accession
    return f"{accession}-{isoform}"
