# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Shared field normalization for FragPipe import tables."""

from __future__ import annotations

from bijux_proteomics.chemistry.modified_peptide_parser import (
    SearchEngineModifiedPeptideDialect,
    build_search_engine_modified_peptide_report,
)
from bijux_proteomics.identification.adapters.fragpipe_import.models import (
    FragpipePeptideReviewEntry,
    FragpipePsmReviewEntry,
)


def canonical_modified_peptide(notation: str | None) -> str | None:
    """Normalize FragPipe peptide notation into canonical modified peptide form."""
    if notation is None:
        return None
    try:
        return build_search_engine_modified_peptide_report(
            notation,
            dialect=SearchEngineModifiedPeptideDialect.FRAGPIPE,
        ).canonical_notation
    except ValueError:
        return None


def split_multi_value(value: object) -> tuple[str, ...]:
    """Split FragPipe multi-value cells while preserving first-seen ordering."""
    if value is None:
        return ()
    text = str(value).strip()
    if not text:
        return ()
    separators = (";", ",")
    tokens = [text]
    for separator in separators:
        expanded: list[str] = []
        for token in tokens:
            expanded.extend(token.split(separator))
        tokens = expanded
    normalized = tuple(token.strip() for token in tokens if token.strip())
    return tuple(dict.fromkeys(normalized))


def optional_float(value: object) -> float | None:
    """Parse an optional floating-point cell from a FragPipe table."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return float(text)


def optional_int(value: object) -> int | None:
    """Parse an optional integer cell from a FragPipe table."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return int(text)


def optional_text(value: object) -> str | None:
    """Parse an optional text cell from a FragPipe table."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def is_open_search_candidate(
    mass_difference: float | None, *, tolerance: float
) -> bool:
    """Flag rows with a mass difference above the configured open-search tolerance."""
    if mass_difference is None:
        return False
    return abs(mass_difference) > tolerance


def has_modified_content(
    row: FragpipePsmReviewEntry | FragpipePeptideReviewEntry,
) -> bool:
    """Detect whether a review row retains modified peptide content."""
    if row.canonical_modified_peptide is None:
        return False
    return row.canonical_modified_peptide != row.peptide


def fragpipe_peptide_entity_id(
    *, peptide: str, modified_peptide: str | None, charge: int | None
) -> str:
    """Build a stable peptide entity identifier for preserved FragPipe evidence."""
    modified_key = modified_peptide or peptide
    if charge is None:
        return f"{modified_key}|unassigned"
    return f"{modified_key}|z{charge}"


__all__ = [
    "canonical_modified_peptide",
    "fragpipe_peptide_entity_id",
    "has_modified_content",
    "is_open_search_candidate",
    "optional_float",
    "optional_int",
    "optional_text",
    "split_multi_value",
]
