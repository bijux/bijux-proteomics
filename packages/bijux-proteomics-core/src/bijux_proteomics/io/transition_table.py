# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Transition-table parsing for fragment-level DIA and targeted review workflows."""

from __future__ import annotations

import csv
from pathlib import Path

from pydantic import ConfigDict, Field, ValidationError, field_validator

from bijux_proteomics_foundation import JsonModel


class TransitionTableEntry(JsonModel):
    """One normalized transition-level quantitative observation."""

    model_config = ConfigDict(extra="forbid")

    transition_id: str = Field(..., min_length=1)
    precursor_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    intensity: float = Field(..., ge=0.0)
    run_id: str | None = None
    peptide_sequence: str | None = None
    protein_ref: str | None = None
    fragment_label: str | None = None
    precursor_mz: float | None = Field(default=None, gt=0.0)
    fragment_mz: float | None = Field(default=None, gt=0.0)
    q_value: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator(
        "transition_id",
        "precursor_id",
        "sample_id",
        "run_id",
        "peptide_sequence",
        "protein_ref",
        "fragment_label",
        mode="before",
    )
    @classmethod
    def _strip_text(cls, value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @field_validator("peptide_sequence")
    @classmethod
    def _normalize_peptide_sequence(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return "".join(character for character in value.upper() if not character.isspace())


class TransitionTableRejectedRow(JsonModel):
    """One rejected transition-table row with explicit stable reason."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    values: dict[str, str] = Field(default_factory=dict)
    reason: str = Field(..., min_length=1)


class TransitionTableParseReport(JsonModel):
    """Stable parse report for one transition-level quantification table."""

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(..., min_length=1)
    accepted_entries: tuple[TransitionTableEntry, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[TransitionTableRejectedRow, ...] = Field(default_factory=tuple)


def parse_transition_table(path: Path) -> TransitionTableParseReport:
    """Parse one transition-level table from TSV or CSV."""

    raw_text = path.read_text(encoding="utf-8")
    lines = raw_text.splitlines()
    if not lines:
        return TransitionTableParseReport(
            source_path=str(path),
            rejected_rows=(
                TransitionTableRejectedRow(
                    row_number=2,
                    reason="transition table is empty",
                ),
            ),
        )
    delimiter = "\t" if "\t" in lines[0] else ","
    reader = csv.DictReader(lines, delimiter=delimiter)
    fieldnames = {field.strip() for field in reader.fieldnames or () if field is not None}
    accepted_entries: list[TransitionTableEntry] = []
    rejected_rows: list[TransitionTableRejectedRow] = []
    for row_number, raw_row in enumerate(reader, start=2):
        normalized_row = {
            (key or "").strip(): (value or "").strip()
            for key, value in raw_row.items()
            if key is not None
        }
        try:
            accepted_entries.append(_parse_transition_row(normalized_row, fieldnames))
        except (ValueError, ValidationError) as exc:
            rejected_rows.append(
                TransitionTableRejectedRow(
                    row_number=row_number,
                    values=normalized_row,
                    reason=_stable_reason(exc),
                )
            )
    return TransitionTableParseReport(
        source_path=str(path),
        accepted_entries=tuple(accepted_entries),
        rejected_rows=tuple(rejected_rows),
    )


def _parse_transition_row(
    row: dict[str, str],
    fieldnames: set[str],
) -> TransitionTableEntry:
    transition_id = (
        row.get("transition_id")
        or row.get("transition")
        or row.get("fragment_id")
        or None
    )
    precursor_id = row.get("precursor_id") or row.get("precursor") or None
    sample_id = row.get("sample_id") or row.get("sample") or None
    intensity = row.get("intensity") or row.get("area") or row.get("peak_area") or None
    if transition_id is None:
        raise ValueError("transition row requires transition_id")
    if precursor_id is None:
        raise ValueError("transition row requires precursor_id")
    if sample_id is None:
        raise ValueError("transition row requires sample_id")
    if intensity is None:
        raise ValueError("transition row requires intensity")
    metadata = {
        key: value
        for key, value in row.items()
        if key in fieldnames
        and key
        not in {
            "transition_id",
            "transition",
            "fragment_id",
            "precursor_id",
            "precursor",
            "sample_id",
            "sample",
            "intensity",
            "area",
            "peak_area",
            "run_id",
            "run",
            "peptide_sequence",
            "peptide",
            "protein_ref",
            "protein",
            "fragment_label",
            "fragment",
            "product_ion",
            "precursor_mz",
            "q1",
            "fragment_mz",
            "product_mz",
            "q3",
            "q_value",
            "qvalue",
        }
        and value
    }
    return TransitionTableEntry(
        transition_id=transition_id,
        precursor_id=precursor_id,
        sample_id=sample_id,
        intensity=float(intensity),
        run_id=row.get("run_id") or row.get("run") or None,
        peptide_sequence=row.get("peptide_sequence") or row.get("peptide") or None,
        protein_ref=row.get("protein_ref") or row.get("protein") or None,
        fragment_label=(
            row.get("fragment_label")
            or row.get("fragment")
            or row.get("product_ion")
            or None
        ),
        precursor_mz=_optional_float(row.get("precursor_mz") or row.get("q1")),
        fragment_mz=_optional_float(
            row.get("fragment_mz") or row.get("product_mz") or row.get("q3")
        ),
        q_value=_optional_float(row.get("q_value") or row.get("qvalue")),
        metadata=metadata,
    )


def _optional_float(value: str | None) -> float | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    return float(stripped)


def _stable_reason(error: ValueError | ValidationError) -> str:
    if isinstance(error, ValidationError):
        issues = error.errors()
        if issues:
            message = issues[0].get("msg")
            if isinstance(message, str):
                return message.removeprefix("Value error, ")
    return str(error)
