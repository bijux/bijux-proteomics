# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Transition-table parsing for fragment-level DIA and targeted review workflows."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from pydantic import ConfigDict, Field, ValidationError, field_validator

from bijux_proteomics._scientific_tables import (
    ScientificTableValidationIssue,
    build_transition_table_schema,
    validate_scientific_table,
)
from bijux_proteomics.domain.records import (
    ImportedEvidenceProvenance,
)
from bijux_proteomics.domain.records import (
    RejectedEvidence as CanonicalRejectedEvidence,
)
from bijux_proteomics.domain.records import (
    TransitionRecord as CanonicalTransitionRecord,
)
from bijux_proteomics_foundation import JsonModel


class TransitionTableEntry(JsonModel):
    """One normalized transition-level quantitative observation."""

    model_config = ConfigDict(extra="forbid")

    transition_id: str = Field(..., min_length=1)
    precursor_id: str = Field(..., min_length=1)
    precursor_charge: int = Field(..., ge=1)
    sample_id: str = Field(..., min_length=1)
    intensity: float = Field(..., ge=0.0)
    run_id: str | None = None
    peptide_sequence: str | None = None
    protein_ref: str | None = None
    fragment_label: str | None = None
    retention_time_minutes: float | None = Field(default=None, ge=0.0)
    precursor_mz: float | None = Field(default=None, gt=0.0)
    fragment_mz: float | None = Field(default=None, gt=0.0)
    q_value: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, str] = Field(default_factory=dict)
    provenance: ImportedEvidenceProvenance | None = None

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
        return "".join(
            character for character in value.upper() if not character.isspace()
        )

    def to_domain_record(self) -> CanonicalTransitionRecord:
        """Convert one transition-table row into the canonical transition record."""

        return CanonicalTransitionRecord(
            transition_id=self.transition_id,
            precursor_id=self.precursor_id,
            precursor_charge=self.precursor_charge,
            sample_id=self.sample_id,
            intensity=self.intensity,
            peptide_sequence=self.peptide_sequence or self.precursor_id,
            run_id=self.run_id,
            protein_ref=self.protein_ref,
            fragment_label=self.fragment_label,
            retention_time_minutes=self.retention_time_minutes,
            precursor_mz=self.precursor_mz,
            fragment_mz=self.fragment_mz,
            q_value=self.q_value,
            metadata={
                **dict(self.metadata),
                **(
                    self.provenance.to_metadata_fields()
                    if self.provenance is not None
                    else {}
                ),
            },
        )


class TransitionTableRejectedRow(JsonModel):
    """One rejected transition-table row with explicit stable reason."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=1)
    values: dict[str, str] = Field(default_factory=dict)
    reason: str = Field(..., min_length=1)

    def to_domain_record(self) -> CanonicalRejectedEvidence:
        """Expose one rejected transition row as canonical rejected evidence."""

        return CanonicalRejectedEvidence(
            record_kind="transition",
            rejection_reason=self.reason,
            row_number=self.row_number,
            raw_fields=self.values,
            metadata={"source_contract": "io.transition_table_rejected_row"},
        )


class TransitionTableParseReport(JsonModel):
    """Stable parse report for one transition-level quantification table."""

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(..., min_length=1)
    accepted_entries: tuple[TransitionTableEntry, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[TransitionTableRejectedRow, ...] = Field(default_factory=tuple)


def parse_transition_table(path: Path) -> TransitionTableParseReport:
    """Parse one transition-level table from TSV or CSV."""
    validation_report = validate_scientific_table(
        path,
        schema=build_transition_table_schema(),
    )
    accepted_entries: list[TransitionTableEntry] = []
    rejected_rows = [
        TransitionTableRejectedRow(
            row_number=row.row_number,
            values=row.raw_values,
            reason=_stable_reason_from_scientific_issues(row.issues),
        )
        for row in validation_report.rejected_rows
    ]
    for accepted_row in validation_report.accepted_rows:
        normalized_row = _render_table_row_values(
            accepted_row.values, accepted_row.extra_values
        )
        try:
            accepted_entries.append(
                _parse_transition_row(
                    normalized_row,
                    provenance=ImportedEvidenceProvenance.from_single_row(
                        source_engine="transition-table",
                        source_file=str(path),
                        source_row_number=accepted_row.row_number,
                        original_identifiers={
                            "transition_id": str(
                                accepted_row.values.get("transition_id") or ""
                            ),
                            "precursor_id": str(
                                accepted_row.values.get("precursor_id") or ""
                            ),
                            "sample_id": str(
                                accepted_row.values.get("sample_id") or ""
                            ),
                        },
                    ),
                )
            )
        except (ValueError, ValidationError) as exc:
            rejected_rows.append(
                TransitionTableRejectedRow(
                    row_number=accepted_row.row_number,
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
    row: Mapping[str, str],
    *,
    provenance: ImportedEvidenceProvenance | None = None,
) -> TransitionTableEntry:
    transition_id = row.get("transition_id") or None
    precursor_id = row.get("precursor_id") or None
    precursor_charge = row.get("precursor_charge") or row.get("charge") or None
    sample_id = row.get("sample_id") or None
    intensity = row.get("intensity") or None
    if transition_id is None:
        raise ValueError("transition row requires transition_id")
    if precursor_id is None:
        raise ValueError("transition row requires precursor_id")
    if precursor_charge is None:
        raise ValueError("transition row requires precursor_charge")
    if sample_id is None:
        raise ValueError("transition row requires sample_id")
    if intensity is None:
        raise ValueError("transition row requires intensity")
    metadata = {
        key: value
        for key, value in row.items()
        if key
        not in {
            "transition_id",
            "precursor_id",
            "sample_id",
            "precursor_charge",
            "intensity",
            "run_id",
            "peptide_sequence",
            "protein_ref",
            "fragment_label",
            "retention_time_minutes",
            "precursor_mz",
            "fragment_mz",
            "q_value",
        }
        and value
    }
    return TransitionTableEntry(
        transition_id=transition_id,
        precursor_id=precursor_id,
        precursor_charge=int(precursor_charge),
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
        retention_time_minutes=_optional_float(
            row.get("retention_time_minutes")
            or row.get("retention_time")
            or row.get("rt")
        ),
        precursor_mz=_optional_float(row.get("precursor_mz") or row.get("q1")),
        fragment_mz=_optional_float(
            row.get("fragment_mz") or row.get("product_mz") or row.get("q3")
        ),
        q_value=_optional_float(row.get("q_value") or row.get("qvalue")),
        metadata=metadata,
        provenance=provenance,
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


def _stable_reason_from_scientific_issues(
    issues: tuple[ScientificTableValidationIssue, ...],
) -> str:
    if not issues:
        return "transition table row was rejected"
    issue = issues[0]
    if issue.code == "empty_table":
        return "transition table is empty"
    if issue.code in {"missing_column", "missing_value"} and issue.column:
        return f"transition row requires {issue.column}"
    if issue.code == "wrong_type" and issue.column:
        return f"transition row has invalid numeric value for {issue.column}"
    return issue.message


def _render_table_row_values(
    values: Mapping[str, str | int | float | bool | None],
    extra_values: Mapping[str, str],
) -> dict[str, str]:
    rendered: dict[str, str] = dict(extra_values)
    for key, value in values.items():
        rendered[key] = "" if value is None else str(value)
    return rendered
