# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical shared schema for queryable scientific evidence cards."""

from __future__ import annotations

import csv
from enum import StrEnum
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.confidence import ConfidenceTier, coerce_confidence_tier
from bijux_proteomics_foundation import JsonModel


class StandardCardKind(StrEnum):
    """Stable card families emitted by governed proteomics workflows."""

    PROTEIN = "protein"
    PTM = "ptm"
    PATHWAY = "pathway"
    SAMPLE = "sample"
    BIOMARKER = "biomarker"


class StandardCardSubjectKind(StrEnum):
    """Stable subject families attached to shared evidence cards."""

    PROTEIN = "protein"
    PTM_SITE = "ptm_site"
    PATHWAY = "pathway"
    SAMPLE = "sample"
    BIOMARKER_CANDIDATE = "biomarker_candidate"


STANDARD_CARD_TSV_COLUMNS: tuple[str, ...] = (
    "card_id",
    "card_kind",
    "subject_kind",
    "subject_id",
    "subject_label",
    "claim",
    "evidence_for",
    "evidence_against",
    "confidence",
    "warning_codes",
    "source_ids",
)


class StandardCardEntry(JsonModel):
    """One shared queryable card projection across scientific card families."""

    model_config = ConfigDict(extra="forbid")

    card_id: str = Field(..., min_length=1)
    card_kind: StandardCardKind
    subject_kind: StandardCardSubjectKind
    subject_id: str = Field(..., min_length=1)
    subject_label: str = Field(..., min_length=1)
    claim: str = Field(..., min_length=1)
    evidence_for: str = Field(..., min_length=1)
    evidence_against: str = Field(..., min_length=1)
    confidence: ConfidenceTier
    warning_codes: tuple[str, ...] = Field(default_factory=tuple)
    source_ids: tuple[str, ...] = Field(default_factory=tuple)


class StandardCardIndex(JsonModel):
    """Indexed lookup surface over one governed shared-card TSV."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[StandardCardEntry, ...] = Field(default_factory=tuple)
    card_ids: dict[str, int] = Field(default_factory=dict)
    subject_ids: dict[str, tuple[int, ...]] = Field(default_factory=dict)
    source_ids: dict[str, tuple[int, ...]] = Field(default_factory=dict)


def build_standard_card_row(entry: StandardCardEntry) -> tuple[str, ...]:
    """Build one shared card row in the canonical TSV column order."""

    return (
        entry.card_id,
        entry.card_kind.value,
        entry.subject_kind.value,
        entry.subject_id,
        entry.subject_label,
        entry.claim,
        entry.evidence_for,
        entry.evidence_against,
        entry.confidence.value,
        ";".join(entry.warning_codes),
        ";".join(entry.source_ids),
    )


def render_standard_card_row(entry: StandardCardEntry) -> tuple[str, ...]:
    """Compatibility wrapper for the legacy shared-card row renderer name."""

    return build_standard_card_row(entry)


def load_standard_card_tsv(path: Path) -> tuple[StandardCardEntry, ...]:
    """Load one governed card TSV through the shared queryable card schema."""

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError(f"{path} does not contain a TSV header")
        missing_columns = tuple(
            column for column in STANDARD_CARD_TSV_COLUMNS if column not in reader.fieldnames
        )
        if missing_columns:
            raise ValueError(
                f"{path} is missing shared card columns: {', '.join(missing_columns)}"
            )
        entries = [
            StandardCardEntry(
                card_id=_required_text(row, "card_id"),
                card_kind=StandardCardKind(_required_text(row, "card_kind")),
                subject_kind=StandardCardSubjectKind(_required_text(row, "subject_kind")),
                subject_id=_required_text(row, "subject_id"),
                subject_label=_required_text(row, "subject_label"),
                claim=_required_text(row, "claim"),
                evidence_for=_required_text(row, "evidence_for"),
                evidence_against=_required_text(row, "evidence_against"),
                confidence=_required_confidence_tier(_required_text(row, "confidence")),
                warning_codes=_split_multi(row.get("warning_codes", "")),
                source_ids=_split_multi(row.get("source_ids", "")),
            )
            for row in reader
        ]
    return tuple(entries)


def load_standard_card_index(path: Path) -> StandardCardIndex:
    """Load one governed card TSV and index it by card, subject, and source ids."""

    entries = load_standard_card_tsv(path)
    subject_ids: dict[str, list[int]] = {}
    source_ids: dict[str, list[int]] = {}
    for index, entry in enumerate(entries):
        subject_ids.setdefault(entry.subject_id, []).append(index)
        for source_id in entry.source_ids:
            source_ids.setdefault(source_id, []).append(index)
    return StandardCardIndex(
        entries=entries,
        card_ids={entry.card_id: index for index, entry in enumerate(entries)},
        subject_ids={
            subject_id: tuple(indexes) for subject_id, indexes in subject_ids.items()
        },
        source_ids={
            source_id: tuple(indexes) for source_id, indexes in source_ids.items()
        },
    )


def find_standard_card_by_card_id(
    card_index: StandardCardIndex,
    card_id: str,
) -> StandardCardEntry | None:
    """Return the shared-card entry for one stable card id."""

    row_index = card_index.card_ids.get(card_id)
    if row_index is None:
        return None
    return card_index.entries[row_index]


def find_standard_cards_by_subject_id(
    card_index: StandardCardIndex,
    subject_id: str,
) -> tuple[StandardCardEntry, ...]:
    """Return the shared-card entries anchored on one subject id."""

    return tuple(
        card_index.entries[row_index]
        for row_index in card_index.subject_ids.get(subject_id, ())
    )


def find_standard_cards_by_source_id(
    card_index: StandardCardIndex,
    source_id: str,
) -> tuple[StandardCardEntry, ...]:
    """Return the shared-card entries citing one stable source id."""

    return tuple(
        card_index.entries[row_index]
        for row_index in card_index.source_ids.get(source_id, ())
    )


def _required_text(row: dict[str, str | None], field_name: str) -> str:
    value = str(row.get(field_name, "")).strip()
    if not value:
        raise ValueError(f"shared card field {field_name!r} must not be blank")
    return value


def _required_confidence_tier(value: str) -> ConfidenceTier:
    confidence = coerce_confidence_tier(value)
    if confidence is None:
        raise ValueError("confidence tier must not be blank")
    return confidence


def _split_multi(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(";") if part.strip())


__all__ = [
    "STANDARD_CARD_TSV_COLUMNS",
    "StandardCardEntry",
    "StandardCardIndex",
    "StandardCardKind",
    "StandardCardSubjectKind",
    "build_standard_card_row",
    "find_standard_card_by_card_id",
    "find_standard_cards_by_source_id",
    "find_standard_cards_by_subject_id",
    "load_standard_card_index",
    "load_standard_card_tsv",
    "render_standard_card_row",
]
