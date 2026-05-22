# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Target-panel parsing for peptide- and protein-focused review workflows."""

from __future__ import annotations

import csv
from enum import StrEnum
from pathlib import Path

from pydantic import ConfigDict, Field, ValidationError, field_validator, model_validator

from bijux_proteomics_foundation import JsonModel


class TargetPanelKind(StrEnum):
    """Primary matching semantics for one target-panel row."""

    PEPTIDE = "peptide"
    PROTEIN = "protein"


class TargetPanelEntry(JsonModel):
    """One normalized peptide or protein target inside a user-defined panel."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    target_kind: TargetPanelKind
    peptide_sequence: str | None = None
    protein_ref: str | None = None
    display_name: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator(
        "target_id",
        "peptide_sequence",
        "protein_ref",
        "display_name",
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

    @model_validator(mode="after")
    def _validate_primary_target(self) -> TargetPanelEntry:
        if self.target_kind is TargetPanelKind.PEPTIDE and self.peptide_sequence is None:
            raise ValueError("peptide targets require peptide_sequence")
        if self.target_kind is TargetPanelKind.PROTEIN and self.protein_ref is None:
            raise ValueError("protein targets require protein_ref")
        return self


class TargetPanelRejectedRow(JsonModel):
    """One rejected target-panel row with explicit stable reason."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    values: dict[str, str] = Field(default_factory=dict)
    reason: str = Field(..., min_length=1)


class TargetPanelParseReport(JsonModel):
    """Stable parse report for one peptide/protein target panel."""

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(..., min_length=1)
    accepted_entries: tuple[TargetPanelEntry, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[TargetPanelRejectedRow, ...] = Field(default_factory=tuple)


def parse_target_panel_table(path: Path) -> TargetPanelParseReport:
    """Parse one peptide/protein target panel from TSV or CSV."""

    raw_text = path.read_text(encoding="utf-8")
    lines = raw_text.splitlines()
    if not lines:
        return TargetPanelParseReport(
            source_path=str(path),
            rejected_rows=(
                TargetPanelRejectedRow(
                    row_number=2,
                    reason="target panel is empty",
                ),
            ),
        )
    delimiter = "\t" if "\t" in lines[0] else ","
    reader = csv.DictReader(lines, delimiter=delimiter)
    fieldnames = {field.strip() for field in reader.fieldnames or () if field is not None}
    accepted_entries: list[TargetPanelEntry] = []
    rejected_rows: list[TargetPanelRejectedRow] = []
    for row_number, raw_row in enumerate(reader, start=2):
        normalized_row = {
            (key or "").strip(): (value or "").strip()
            for key, value in raw_row.items()
            if key is not None
        }
        try:
            accepted_entries.append(_parse_target_panel_row(normalized_row, fieldnames))
        except (ValueError, ValidationError) as exc:
            rejected_rows.append(
                TargetPanelRejectedRow(
                    row_number=row_number,
                    values=normalized_row,
                    reason=_stable_reason(exc),
                )
            )
    return TargetPanelParseReport(
        source_path=str(path),
        accepted_entries=tuple(accepted_entries),
        rejected_rows=tuple(rejected_rows),
    )


def _parse_target_panel_row(
    row: dict[str, str],
    fieldnames: set[str],
) -> TargetPanelEntry:
    peptide_sequence = row.get("peptide_sequence") or row.get("peptide") or None
    protein_ref = row.get("protein_ref") or row.get("protein") or None
    explicit_kind = row.get("target_kind") or row.get("kind") or None
    if explicit_kind is None:
        if peptide_sequence:
            target_kind = TargetPanelKind.PEPTIDE
        elif protein_ref:
            target_kind = TargetPanelKind.PROTEIN
        else:
            raise ValueError("target row requires peptide_sequence or protein_ref")
    else:
        normalized_kind = explicit_kind.strip().lower()
        if normalized_kind not in {kind.value for kind in TargetPanelKind}:
            raise ValueError(f"unsupported target_kind {explicit_kind!r}")
        target_kind = TargetPanelKind(normalized_kind)
    target_id = row.get("target_id") or row.get("id") or peptide_sequence or protein_ref
    if target_id is None:
        raise ValueError("target row requires target_id, peptide_sequence, or protein_ref")
    metadata = {
        key: value
        for key, value in row.items()
        if key in fieldnames
        and key
        not in {
            "target_id",
            "id",
            "target_kind",
            "kind",
            "peptide_sequence",
            "peptide",
            "protein_ref",
            "protein",
            "display_name",
        }
        and value
    }
    return TargetPanelEntry(
        target_id=target_id,
        target_kind=target_kind,
        peptide_sequence=peptide_sequence,
        protein_ref=protein_ref,
        display_name=row.get("display_name") or row.get("name") or None,
        metadata=metadata,
    )


def _stable_reason(error: ValueError | ValidationError) -> str:
    if isinstance(error, ValidationError):
        issues = error.errors()
        if issues:
            message = issues[0].get("msg")
            if isinstance(message, str):
                return message.removeprefix("Value error, ")
    return str(error)
