# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Governed loader for reusable modification-pack documents."""

from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum
from pathlib import Path

from pydantic import ConfigDict, Field, ValidationError, field_validator, model_validator

from bijux_proteomics.chemistry.amino_acid_mass import _CANONICAL_RESIDUES
from bijux_proteomics.chemistry.contracts import NeutralLoss
from bijux_proteomics_foundation import DocumentSchema, JsonModel


class ModificationPackTerminus(StrEnum):
    """Supported terminal targeting scopes inside one modification pack."""

    PEPTIDE_N_TERM = "peptide_n_term"
    PEPTIDE_C_TERM = "peptide_c_term"
    PROTEIN_N_TERM = "protein_n_term"
    PROTEIN_C_TERM = "protein_c_term"


class ModificationPackRejectedRow(JsonModel):
    """One rejected modification-pack row with a stable reason."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=1)
    values: dict[str, str] = Field(default_factory=dict)
    reason: str = Field(..., min_length=1)


class ModificationPackValidationReport(JsonModel):
    """Structured validation report for one modification pack load."""

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(..., min_length=1)
    rejected_rows: tuple[ModificationPackRejectedRow, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class ModificationPackValidationError(ValueError):
    """Raised when a modification pack violates governed row rules."""

    def __init__(self, report: ModificationPackValidationReport) -> None:
        self.report = report
        first_rejection = report.rejected_rows[0] if report.rejected_rows else None
        message = (
            "modification pack validation failed"
            if first_rejection is None
            else (
                "modification pack validation failed: "
                f"row {first_rejection.row_number} {first_rejection.reason}"
            )
        )
        super().__init__(message)


class ModificationPackEntry(JsonModel):
    """One normalized modification definition from a reusable pack."""

    model_config = ConfigDict(extra="forbid")

    modification_id: str = Field(..., min_length=1)
    aliases: tuple[str, ...] = Field(default_factory=tuple)
    delta_mass: float
    allowed_residues: tuple[str, ...] = Field(default_factory=tuple)
    allowed_termini: tuple[ModificationPackTerminus, ...] = Field(default_factory=tuple)
    neutral_losses: tuple[NeutralLoss, ...] = Field(default_factory=tuple)
    ptm_class: str = Field(..., min_length=1)
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("aliases", mode="before")
    @classmethod
    def _normalize_aliases(cls, value: object) -> tuple[str, ...]:
        if value in (None, ""):
            return ()
        tokens: tuple[str, ...]
        if isinstance(value, str):
            tokens = (value,)
        else:
            if not isinstance(value, Iterable):
                raise ValueError("aliases must be iterable")
            tokens = tuple(str(token) for token in value)
        normalized = tuple(token.strip() for token in tokens if token.strip())
        return tuple(dict.fromkeys(normalized))

    @field_validator("allowed_residues", mode="before")
    @classmethod
    def _normalize_allowed_residues(cls, value: object) -> tuple[str, ...]:
        if value in (None, ""):
            return ()
        residues: tuple[str, ...]
        if isinstance(value, str):
            residues = tuple(value.strip().upper())
        else:
            if not isinstance(value, Iterable):
                raise ValueError("allowed_residues must be iterable")
            residues = tuple(str(token).strip().upper() for token in value)
        invalid = [residue for residue in residues if residue not in _CANONICAL_RESIDUES]
        if invalid:
            raise ValueError(
                "invalid modification-pack residues: "
                + ", ".join(sorted(set(invalid)))
            )
        return tuple(sorted(dict.fromkeys(residues)))

    @field_validator("allowed_termini", mode="before")
    @classmethod
    def _normalize_allowed_termini(
        cls,
        value: object,
    ) -> tuple[ModificationPackTerminus, ...]:
        if value in (None, ""):
            return ()
        tokens: tuple[str, ...]
        if isinstance(value, str):
            tokens = (value,)
        else:
            if not isinstance(value, Iterable):
                raise ValueError("allowed_termini must be iterable")
            tokens = tuple(str(token) for token in value)
        normalized = [
            ModificationPackTerminus(token.strip().lower())
            for token in tokens
            if token.strip()
        ]
        return tuple(
            sorted(
                dict.fromkeys(normalized),
                key=lambda terminus: terminus.value,
            )
        )

    @field_validator("neutral_losses", mode="before")
    @classmethod
    def _normalize_neutral_losses(cls, value: object) -> tuple[object, ...]:
        if value in (None, ""):
            return ()
        if isinstance(value, tuple):
            return value
        if not isinstance(value, Iterable):
            raise ValueError("neutral_losses must be iterable")
        return tuple(value)

    @field_validator("ptm_class")
    @classmethod
    def _normalize_ptm_class(cls, value: str) -> str:
        normalized = value.strip().lower().replace(" ", "_")
        if not normalized:
            raise ValueError("ptm_class must not be blank")
        return normalized

    @model_validator(mode="after")
    def _validate_targeting(self) -> ModificationPackEntry:
        if not self.allowed_residues and not self.allowed_termini:
            raise ValueError(
                "modification pack row requires allowed_residues or allowed_termini"
            )
        if self.allowed_residues and self.allowed_termini:
            raise ValueError(
                "modification pack row must target residues or termini, not both"
            )
        return self


class ModificationPackSummary(JsonModel):
    """Stable counts over one loaded modification pack."""

    model_config = ConfigDict(extra="forbid")

    modification_count: int = Field(..., ge=0)
    residue_targeted_count: int = Field(..., ge=0)
    terminus_targeted_count: int = Field(..., ge=0)
    ptm_class_counts: dict[str, int] = Field(default_factory=dict)


class ModificationPack(JsonModel):
    """One normalized modification pack ready for downstream chemistry workflows."""

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(..., min_length=1)
    pack_name: str = Field(..., min_length=1)
    pack_version: str | None = None
    document_schema: DocumentSchema | None = None
    modifications: tuple[ModificationPackEntry, ...] = Field(default_factory=tuple)
    metadata: dict[str, str] = Field(default_factory=dict)
    summary: ModificationPackSummary


class _RawModificationPack(JsonModel):
    """Raw JSON envelope for one modification pack before row normalization."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema | None = None
    pack_name: str | None = None
    pack_version: str | None = None
    modifications: list[object] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


def load_modification_pack(path: Path) -> ModificationPack:
    """Load one governed modification-pack document from JSON."""

    raw_document = _RawModificationPack.model_validate_json(path.read_text(encoding="utf-8"))
    rejected_rows: list[ModificationPackRejectedRow] = []
    accepted_rows: list[ModificationPackEntry] = []
    seen_ids: set[str] = set()
    alias_owner: dict[str, str] = {}

    for row_number, raw_row in enumerate(raw_document.modifications, start=1):
        if not isinstance(raw_row, dict):
            rejected_rows.append(
                ModificationPackRejectedRow(
                    row_number=row_number,
                    values={"_raw_row": str(raw_row)},
                    reason="modification pack rows must be JSON objects",
                )
            )
            continue
        try:
            entry = ModificationPackEntry.model_validate(raw_row, strict=True)
        except ValidationError as exc:
            rejected_rows.append(
                ModificationPackRejectedRow(
                    row_number=row_number,
                    values=_stringify_mapping(raw_row),
                    reason=_stable_validation_reason(exc),
                )
            )
            continue
        if entry.modification_id in seen_ids:
            rejected_rows.append(
                ModificationPackRejectedRow(
                    row_number=row_number,
                    values=_stringify_mapping(raw_row),
                    reason=f"duplicate modification_id {entry.modification_id!r}",
                )
            )
            continue
        conflicting_alias = next(
            (
                alias
                for alias in entry.aliases
                if alias in alias_owner and alias_owner[alias] != entry.modification_id
            ),
            None,
        )
        if conflicting_alias is not None:
            rejected_rows.append(
                ModificationPackRejectedRow(
                    row_number=row_number,
                    values=_stringify_mapping(raw_row),
                    reason=(
                        f"alias {conflicting_alias!r} conflicts between "
                        f"{alias_owner[conflicting_alias]!r} and {entry.modification_id!r}"
                    ),
                )
            )
            continue
        seen_ids.add(entry.modification_id)
        for alias in entry.aliases:
            alias_owner[alias] = entry.modification_id
        accepted_rows.append(entry)

    if rejected_rows:
        raise ModificationPackValidationError(
            ModificationPackValidationReport(
                source_path=str(path),
                rejected_rows=tuple(rejected_rows),
                note=(
                    "modification pack loading rejected invalid residue or terminus "
                    "rules before downstream chemistry analysis could consume them"
                ),
            )
        )

    ptm_class_counts: dict[str, int] = {}
    for entry in accepted_rows:
        ptm_class_counts[entry.ptm_class] = ptm_class_counts.get(entry.ptm_class, 0) + 1

    return ModificationPack(
        source_path=str(path),
        pack_name=raw_document.pack_name or path.stem,
        pack_version=raw_document.pack_version,
        document_schema=raw_document.document_schema,
        modifications=tuple(accepted_rows),
        metadata=raw_document.metadata,
        summary=ModificationPackSummary(
            modification_count=len(accepted_rows),
            residue_targeted_count=sum(
                1 for entry in accepted_rows if entry.allowed_residues
            ),
            terminus_targeted_count=sum(
                1 for entry in accepted_rows if entry.allowed_termini
            ),
            ptm_class_counts=ptm_class_counts,
        ),
    )


def _stringify_mapping(raw_row: dict[str, object]) -> dict[str, str]:
    return {
        str(key): ("" if value is None else str(value))
        for key, value in raw_row.items()
    }


def _stable_validation_reason(error: ValidationError) -> str:
    reasons: list[str] = []
    for issue in error.errors():
        location = ".".join(str(token) for token in issue.get("loc", ()))
        message = str(issue.get("msg", "invalid field"))
        if message.startswith("Value error, "):
            message = message.removeprefix("Value error, ")
        if location:
            reasons.append(f"{location}: {message}")
        else:
            reasons.append(message)
    return "; ".join(reasons)


__all__ = [
    "ModificationPack",
    "ModificationPackEntry",
    "ModificationPackRejectedRow",
    "ModificationPackSummary",
    "ModificationPackTerminus",
    "ModificationPackValidationError",
    "ModificationPackValidationReport",
    "load_modification_pack",
]
