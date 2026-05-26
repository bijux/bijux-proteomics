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


def render_standard_card_row(entry: StandardCardEntry) -> tuple[str, ...]:
    """Render one shared card entry in the canonical TSV column order."""

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
                confidence=coerce_confidence_tier(_required_text(row, "confidence")),
                warning_codes=_split_multi(row.get("warning_codes", "")),
                source_ids=_split_multi(row.get("source_ids", "")),
            )
            for row in reader
        ]
    return tuple(entries)


def _required_text(row: dict[str, str | None], field_name: str) -> str:
    value = str(row.get(field_name, "")).strip()
    if not value:
        raise ValueError(f"shared card field {field_name!r} must not be blank")
    return value


def _split_multi(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(";") if part.strip())


__all__ = [
    "STANDARD_CARD_TSV_COLUMNS",
    "StandardCardEntry",
    "StandardCardKind",
    "StandardCardSubjectKind",
    "load_standard_card_tsv",
    "render_standard_card_row",
]
