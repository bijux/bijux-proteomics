# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Dialect-neutral parsing and review for modified peptide notation."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry.contracts import (
    AppliedModification,
    ModificationRegistryDocument,
    ParsedModifiedPeptide,
    build_modified_peptide,
    canonicalize_modified_peptide,
    parse_modified_peptide,
)
from bijux_proteomics_foundation import JsonModel


class ModifiedPeptideNotationDialect(StrEnum):
    """Supported modified-peptide notation dialects."""

    BIJUX = "bijux"
    MAXQUANT = "maxquant"
    MSFRAGGER = "msfragger"
    FRAGPIPE = "fragpipe"
    SAGE = "sage"
    COMET = "comet"


# Compatibility alias for existing chemistry and import surfaces.
SearchEngineModifiedPeptideDialect = ModifiedPeptideNotationDialect


class ModifiedPeptideParseReview(JsonModel):
    """Stable review payload for one modified-peptide notation string."""

    model_config = ConfigDict(extra="forbid")

    dialect: ModifiedPeptideNotationDialect
    original_notation: str = Field(..., min_length=1)
    residue_sequence: str = Field(..., min_length=1)
    canonical_notation: str = Field(..., min_length=1)
    at_protein_n_term: bool = False
    at_protein_c_term: bool = False
    modifications: tuple[AppliedModification, ...] = Field(default_factory=tuple)
    unknown_tokens: tuple[str, ...] = Field(default_factory=tuple)
    modified_peptide_record: ModifiedPeptideReviewRecord


class ModifiedPeptideReviewRecord(JsonModel):
    """Chemistry-owned modified-peptide record for notation review surfaces."""

    model_config = ConfigDict(extra="forbid")

    record_id: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    modified_peptide: str = Field(..., min_length=1)
    modification_names: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, str] = Field(default_factory=dict)


# Compatibility alias for existing chemistry and import surfaces.
SearchEngineModifiedPeptideReport = ModifiedPeptideParseReview


def parse_modified_peptide_notation(
    notation: str,
    *,
    dialect: ModifiedPeptideNotationDialect | str,
    registry: ModificationRegistryDocument | None = None,
) -> ParsedModifiedPeptide:
    """Parse one supported notation into the owned modified-peptide contract."""
    resolved = (
        ModifiedPeptideNotationDialect(dialect)
        if isinstance(dialect, str)
        else dialect
    )
    if resolved is ModifiedPeptideNotationDialect.BIJUX:
        return parse_modified_peptide(notation, registry=registry)
    if resolved is ModifiedPeptideNotationDialect.MAXQUANT:
        return _parse_maxquant_modified_peptide(notation, registry=registry)
    if resolved in {
        ModifiedPeptideNotationDialect.MSFRAGGER,
        ModifiedPeptideNotationDialect.FRAGPIPE,
        ModifiedPeptideNotationDialect.COMET,
    }:
        return _parse_bracket_delta_modified_peptide(notation, registry=registry)
    return parse_modified_peptide(notation, registry=registry)


def canonicalize_modified_peptide_notation(
    notation: str,
    *,
    dialect: ModifiedPeptideNotationDialect | str,
    registry: ModificationRegistryDocument | None = None,
) -> str:
    """Return the owned canonical notation for one modified-peptide string."""
    parsed = parse_modified_peptide_notation(
        notation,
        dialect=dialect,
        registry=registry,
    )
    return canonicalize_modified_peptide(parsed, registry=registry)


def build_modified_peptide_parse_review(
    notation: str,
    *,
    dialect: ModifiedPeptideNotationDialect | str,
    registry: ModificationRegistryDocument | None = None,
) -> ModifiedPeptideParseReview:
    """Build a review payload for one parsed modified-peptide notation."""
    resolved = (
        ModifiedPeptideNotationDialect(dialect)
        if isinstance(dialect, str)
        else dialect
    )
    parsed = parse_modified_peptide_notation(
        notation,
        dialect=resolved,
        registry=registry,
    )
    canonical_notation = canonicalize_modified_peptide(parsed, registry=registry)
    return ModifiedPeptideParseReview(
        dialect=resolved,
        original_notation=notation,
        residue_sequence=parsed.sequence,
        canonical_notation=canonical_notation,
        at_protein_n_term=parsed.at_protein_n_term,
        at_protein_c_term=parsed.at_protein_c_term,
        modifications=parsed.modifications,
        unknown_tokens=(),
        modified_peptide_record=_build_modified_peptide_record(
            parsed,
            canonical_notation=canonical_notation,
        ),
    )


def _build_modified_peptide_record(
    peptide: ParsedModifiedPeptide,
    *,
    canonical_notation: str,
) -> ModifiedPeptideReviewRecord:
    return ModifiedPeptideReviewRecord(
        record_id=canonical_notation,
        peptide_sequence=peptide.sequence,
        canonical_peptide=peptide.sequence,
        modified_peptide=canonical_notation,
        modification_names=tuple(
            dict.fromkeys(modification.name for modification in peptide.modifications)
        ),
        metadata={"source_contract": "chemistry.modified_peptide_parser"},
    )


def _parse_maxquant_modified_peptide(
    notation: str,
    *,
    registry: ModificationRegistryDocument | None,
) -> ParsedModifiedPeptide:
    text = notation.strip()
    if text.startswith("_") and text.endswith("_") and len(text) >= 2:
        text = text[1:-1]
    assignments: list[str] = []
    residues: list[str] = []
    at_protein_n_term = False
    at_protein_c_term = False
    index = 0

    while index < len(text) and text[index] == "(":
        token, index = _consume_parenthetical_token(text, index)
        normalized_token, site_label = _normalize_maxquant_token(
            token,
            default_site="n-term",
        )
        assignments.append(f"{normalized_token}@{site_label}")
        at_protein_n_term = at_protein_n_term or site_label == "protein-n-term"

    while index < len(text):
        character = text[index]
        if character.isalpha() and character.isupper():
            residues.append(character)
            index += 1
            while index < len(text) and text[index] == "(":
                token, index = _consume_parenthetical_token(text, index)
                normalized_token, _ = _normalize_maxquant_token(
                    token,
                    default_site="anywhere",
                )
                assignments.append(f"{normalized_token}@{len(residues)}")
            continue
        if character == "(":
            token, index = _consume_parenthetical_token(text, index)
            normalized_token, site_label = _normalize_maxquant_token(
                token,
                default_site="c-term",
            )
            assignments.append(f"{normalized_token}@{site_label}")
            at_protein_c_term = at_protein_c_term or site_label == "protein-c-term"
            continue
        raise ValueError(
            f"unsupported MaxQuant modified peptide character {character!r}"
        )

    return build_modified_peptide(
        "".join(residues),
        assignments=tuple(assignments),
        registry=registry,
        at_protein_n_term=at_protein_n_term,
        at_protein_c_term=at_protein_c_term,
    )


def _parse_bracket_delta_modified_peptide(
    notation: str,
    *,
    registry: ModificationRegistryDocument | None,
) -> ParsedModifiedPeptide:
    text = notation.strip()
    assignments: list[str] = []
    residues: list[str] = []
    index = 0

    if text.startswith("n["):
        token, index = _consume_bracket_token(text, 1)
        assignments.append(f"{_normalize_delta_or_name_token(token)}@n-term")

    while index < len(text):
        character = text[index]
        if character.isalpha() and character.isupper():
            residues.append(character)
            index += 1
            if index < len(text) and text[index] == "[":
                token, index = _consume_bracket_token(text, index)
                assignments.append(
                    f"{_normalize_delta_or_name_token(token)}@{len(residues)}"
                )
            continue
        if character == "c" and index + 1 < len(text) and text[index + 1] == "[":
            token, index = _consume_bracket_token(text, index + 1)
            assignments.append(f"{_normalize_delta_or_name_token(token)}@c-term")
            continue
        raise ValueError(
            f"unsupported bracket-delta modified peptide character {character!r}"
        )

    return build_modified_peptide(
        "".join(residues),
        assignments=tuple(assignments),
        registry=registry,
    )


def _consume_parenthetical_token(text: str, start: int) -> tuple[str, int]:
    depth = 0
    for index in range(start, len(text)):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                return text[start + 1 : index], index + 1
    raise ValueError("unterminated MaxQuant modification token")


def _consume_bracket_token(text: str, start: int) -> tuple[str, int]:
    close = text.find("]", start)
    if close == -1:
        raise ValueError("unterminated bracket modification token")
    return text[start + 1 : close], close + 1


def _normalize_maxquant_token(token: str, *, default_site: str) -> tuple[str, str]:
    value = token.strip()
    if " (" not in value:
        return _normalize_delta_or_name_token(value), default_site
    name, suffix = value.rsplit(" (", 1)
    suffix = suffix.rstrip(")").strip().lower()
    normalized_name = _normalize_delta_or_name_token(name.strip())
    if suffix in {"m", "sty", "c", "n", "k", "r", "q", "e", "protein c-term"}:
        if suffix == "protein c-term":
            return normalized_name, "protein-c-term"
        return normalized_name, "anywhere"
    if suffix in {"n-term", "protein n-term"}:
        return normalized_name, "protein-n-term" if suffix.startswith(
            "protein"
        ) else "n-term"
    if suffix in {"c-term"}:
        return normalized_name, "c-term"
    if suffix in {"protein cterm", "protein c-term"}:
        return normalized_name, "protein-c-term"
    raise ValueError(f"unsupported MaxQuant modification token {token!r}")


def _normalize_delta_or_name_token(token: str) -> str:
    value = token.strip()
    if not value:
        raise ValueError("modification token cannot be empty")
    if value[0] in {"+", "-"}:
        return value
    try:
        numeric = float(value)
    except ValueError:
        return value
    return f"+{value}" if numeric >= 0 else value


# Compatibility helpers for existing import and CLI surfaces.
def parse_search_engine_modified_peptide(
    notation: str,
    *,
    dialect: SearchEngineModifiedPeptideDialect | str,
    registry: ModificationRegistryDocument | None = None,
) -> ParsedModifiedPeptide:
    return parse_modified_peptide_notation(
        notation,
        dialect=dialect,
        registry=registry,
    )


def canonicalize_search_engine_modified_peptide(
    notation: str,
    *,
    dialect: SearchEngineModifiedPeptideDialect | str,
    registry: ModificationRegistryDocument | None = None,
) -> str:
    return canonicalize_modified_peptide_notation(
        notation,
        dialect=dialect,
        registry=registry,
    )


def build_search_engine_modified_peptide_report(
    notation: str,
    *,
    dialect: SearchEngineModifiedPeptideDialect | str,
    registry: ModificationRegistryDocument | None = None,
) -> SearchEngineModifiedPeptideReport:
    return build_modified_peptide_parse_review(
        notation,
        dialect=dialect,
        registry=registry,
    )


__all__ = [
    "ModifiedPeptideNotationDialect",
    "ModifiedPeptideParseReview",
    "SearchEngineModifiedPeptideDialect",
    "SearchEngineModifiedPeptideReport",
    "build_modified_peptide_parse_review",
    "build_search_engine_modified_peptide_report",
    "canonicalize_modified_peptide_notation",
    "canonicalize_search_engine_modified_peptide",
    "parse_modified_peptide_notation",
    "parse_search_engine_modified_peptide",
]
