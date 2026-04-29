# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Protein digestion and peptide indexing contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics_foundation import JsonModel


class ProteaseCleavageMode(StrEnum):
    """Direction for protease cleavage semantics."""

    C_TERMINAL = "c_terminal"
    N_TERMINAL = "n_terminal"


class ProteaseRule(JsonModel):
    """Stable cleavage contract for one protease."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1)
    cleavage_mode: ProteaseCleavageMode = ProteaseCleavageMode.C_TERMINAL
    cleavage_residues: str = Field(..., min_length=1)
    blocked_by_next: str = ""
    blocked_by_previous: str = ""
    description: str = ""

    @field_validator("cleavage_residues", "blocked_by_next", "blocked_by_previous")
    @classmethod
    def _normalize_residue_token(cls, value: str) -> str:
        return "".join(sorted(set(value.strip().upper())))


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


def parse_custom_protease_rule(specification: str, *, name: str = "custom") -> ProteaseRule:
    """Parse a user-defined protease rule from a compact textual form.

    Supported keys:
    - ``after`` or ``before`` for cleavage residues
    - ``block_next`` for residues that block a C-terminal cut
    - ``block_previous`` for residues that block an N-terminal cut
    - ``description`` for human-readable metadata
    """

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
    if bool(after) == bool(before):
        raise ValueError("custom protease rule must define exactly one of 'after' or 'before'")

    cleavage_mode = (
        ProteaseCleavageMode.C_TERMINAL if after is not None else ProteaseCleavageMode.N_TERMINAL
    )
    cleavage_residues = after if after is not None else before
    assert cleavage_residues is not None
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
) -> tuple[tuple[DigestedPeptide, ...], PeptideFilterReport]:
    """Filter digested peptides by sequence length."""
    filtered: list[DigestedPeptide] = []
    excluded_by_length = 0
    for peptide in peptides:
        if min_length is not None and len(peptide.sequence) < min_length:
            excluded_by_length += 1
            continue
        if max_length is not None and len(peptide.sequence) > max_length:
            excluded_by_length += 1
            continue
        filtered.append(peptide)
    return tuple(filtered), PeptideFilterReport(
        input_peptides=len(peptides),
        output_peptides=len(filtered),
        excluded_by_length=excluded_by_length,
        excluded_by_mass=0,
    )


def digest_sequence(
    sequence: str,
    *,
    protease: ProteaseRule | str = "trypsin",
    source_accession: str = "sequence",
    source_identifier: str | None = None,
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
    max_peptide_length = max_length if max_length is not None else len(normalized)
    if mode is PeptideDigestionMode.NON_SPECIFIC:
        return _non_specific_digest(
            normalized,
            source_accession=source_accession,
            source_identifier=identifier,
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
            min_length=min_length,
            max_length=max_peptide_length,
        )
    for start_index, start in enumerate(boundaries[:-1]):
        max_span = min(missed_cleavages + 1, len(boundaries) - start_index - 1)
        for span in range(1, max_span + 1):
            end = boundaries[start_index + span]
            peptide = normalized[start:end]
            if not peptide or len(peptide) < min_length or len(peptide) > max_peptide_length:
                continue
            peptides.append(
                DigestedPeptide(
                    source_accession=source_accession,
                    source_identifier=identifier,
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


def _full_digest_boundaries(sequence: str, rule: ProteaseRule) -> tuple[int, ...]:
    boundaries = [0]
    if not sequence:
        return (0,)

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
            if previous_residue is not None and previous_residue in rule.blocked_by_previous:
                continue
            if index not in boundaries:
                boundaries.append(index)

    if boundaries[-1] != len(sequence):
        boundaries.append(len(sequence))
    return tuple(boundaries)


def _semi_specific_digest(
    sequence: str,
    *,
    boundaries: tuple[int, ...],
    rule: ProteaseRule,
    source_accession: str,
    source_identifier: str,
    min_length: int,
    max_length: int,
) -> tuple[DigestedPeptide, ...]:
    peptides: list[DigestedPeptide] = []
    seen: set[tuple[int, int]] = set()
    enzymatic_bounds = set(boundaries)

    for start in boundaries[:-1]:
        for end in range(start + 1, len(sequence) + 1):
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
                    sequence=sequence[start:end],
                    start=start + 1,
                    end=end,
                    missed_cleavages=0,
                    protease=rule.name,
                    digestion_mode=PeptideDigestionMode.SEMI_SPECIFIC,
                    cleavage_type=cleavage_type,
                )
            )

    for start in range(0, len(sequence)):
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
    protease: str,
    min_length: int,
    max_length: int,
) -> tuple[DigestedPeptide, ...]:
    peptides: list[DigestedPeptide] = []
    for start in range(0, len(sequence)):
        for end in range(start + min_length, min(len(sequence), start + max_length) + 1):
            peptide = sequence[start:end]
            peptides.append(
                DigestedPeptide(
                    source_accession=source_accession,
                    source_identifier=source_identifier,
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
