# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Targeted result import over Skyline-style and exported transition tables."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.records import (
    ImportedEvidenceProvenance,
)
from bijux_proteomics.domain.records import (
    TransitionRecord as CanonicalTransitionRecord,
)
from bijux_proteomics.io.transition_table import parse_transition_table
from bijux_proteomics_foundation import JsonModel


class TargetedResultSourceKind(StrEnum):
    """Owned targeted-result source kinds."""

    SKYLINE_EXPORT = "skyline_export"
    TRANSITION_TABLE = "transition_table"


class TargetedResultObservation(JsonModel):
    """One targeted transition observation with intensity, RT, and quality context."""

    model_config = ConfigDict(extra="forbid")

    source_kind: TargetedResultSourceKind
    transition_id: str = Field(..., min_length=1)
    precursor_id: str = Field(..., min_length=1)
    precursor_charge: int | None = Field(default=None, ge=1)
    peptide_sequence: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    intensity: float = Field(..., ge=0.0)
    retention_time_minutes: float | None = Field(default=None, ge=0.0)
    quality_flag: str | None = None
    protein_ref: str | None = None
    fragment_label: str | None = None
    precursor_mz: float | None = Field(default=None, gt=0.0)
    fragment_mz: float | None = Field(default=None, gt=0.0)
    provenance: ImportedEvidenceProvenance

    def to_domain_record(self) -> CanonicalTransitionRecord:
        """Convert one targeted observation into the canonical transition record."""

        return CanonicalTransitionRecord(
            transition_id=self.transition_id,
            precursor_id=self.precursor_id,
            precursor_charge=self.precursor_charge,
            sample_id=self.sample_id,
            intensity=self.intensity,
            peptide_sequence=self.peptide_sequence,
            protein_ref=self.protein_ref,
            fragment_label=self.fragment_label,
            retention_time_minutes=self.retention_time_minutes,
            precursor_mz=self.precursor_mz,
            fragment_mz=self.fragment_mz,
            quality_flag=self.quality_flag,
            metadata={
                "source_contract": f"targeted.{self.source_kind.value}",
                **self.provenance.to_metadata_fields(),
            },
        )


class TargetedResultImportSummary(JsonModel):
    """Compact summary over one targeted result import packet."""

    model_config = ConfigDict(extra="forbid")

    observation_count: int = Field(..., ge=0)
    precursor_count: int = Field(..., ge=0)
    transition_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    retention_time_count: int = Field(..., ge=0)
    quality_flag_count: int = Field(..., ge=0)


class TargetedResultImportReport(JsonModel):
    """One governed targeted result import report."""

    model_config = ConfigDict(extra="forbid")

    source_kind: TargetedResultSourceKind
    source_name: str = Field(..., min_length=1)
    observations: tuple[TargetedResultObservation, ...] = Field(default_factory=tuple)
    summary: TargetedResultImportSummary
    note: str = Field(..., min_length=1)


def build_skyline_result_import_report(path: Path) -> TargetedResultImportReport:
    """Import one Skyline-style transition export into owned targeted observations."""

    reader = csv.DictReader(
        path.read_text(encoding="utf-8").splitlines(), delimiter="\t"
    )
    observations: list[TargetedResultObservation] = []
    for row_number, row in enumerate(reader, start=2):
        peptide_sequence = _required_value(
            row,
            "PeptideModifiedSequence",
            "PeptideSequence",
        )
        precursor_charge = _required_value(row, "PrecursorCharge")
        precursor_id = (
            _optional_value(row, "PrecursorName", "PrecursorId")
            or f"{peptide_sequence}/{precursor_charge}"
        )
        transition_id = _optional_value(
            row, "TransitionName", "TransitionId"
        ) or _required_value(row, "FragmentIon")
        observations.append(
            TargetedResultObservation(
                source_kind=TargetedResultSourceKind.SKYLINE_EXPORT,
                transition_id=transition_id,
                precursor_id=precursor_id,
                precursor_charge=int(precursor_charge),
                peptide_sequence=peptide_sequence,
                sample_id=_required_value(row, "ReplicateName", "SampleName"),
                intensity=float(_required_value(row, "Area")),
                retention_time_minutes=_optional_float(
                    _optional_value(row, "RetentionTime", "RetentionTimeMinutes")
                ),
                quality_flag=_optional_value(row, "PeakQuality", "QualityFlag"),
                protein_ref=_optional_value(row, "ProteinName", "Protein"),
                fragment_label=_optional_value(row, "FragmentIon"),
                precursor_mz=_optional_float(_optional_value(row, "PrecursorMz", "Q1")),
                fragment_mz=_optional_float(_optional_value(row, "ProductMz", "Q3")),
                provenance=ImportedEvidenceProvenance.from_single_row(
                    source_engine="skyline",
                    source_file=str(path),
                    source_row_number=row_number,
                    original_identifiers={
                        "transition_id": transition_id,
                        "precursor_id": precursor_id,
                        "sample_id": _required_value(
                            row, "ReplicateName", "SampleName"
                        ),
                    },
                ),
            )
        )
    return _build_import_report(
        source_kind=TargetedResultSourceKind.SKYLINE_EXPORT,
        source_name="Skyline",
        observations=tuple(
            sorted(
                observations,
                key=lambda item: (
                    item.precursor_id,
                    item.transition_id,
                    item.sample_id,
                ),
            )
        ),
        note=(
            "targeted import keeps Skyline-style peptide, precursor, transition, sample intensity, retention-time, and quality-flag evidence explicit before any matrix rollup"
        ),
    )


def build_transition_table_result_import_report(
    path: Path,
) -> TargetedResultImportReport:
    """Import one exported transition table into owned targeted observations."""

    parse_report = parse_transition_table(path)
    observations = tuple(
        TargetedResultObservation(
            source_kind=TargetedResultSourceKind.TRANSITION_TABLE,
            transition_id=entry.transition_id,
            precursor_id=entry.precursor_id,
            precursor_charge=entry.precursor_charge,
            peptide_sequence=entry.peptide_sequence or entry.precursor_id,
            sample_id=entry.sample_id,
            intensity=entry.intensity,
            retention_time_minutes=entry.retention_time_minutes,
            quality_flag=entry.metadata.get("quality_flag")
            or entry.metadata.get("flag"),
            protein_ref=entry.protein_ref,
            fragment_label=entry.fragment_label,
            precursor_mz=entry.precursor_mz,
            fragment_mz=entry.fragment_mz,
            provenance=entry.provenance
            or ImportedEvidenceProvenance.from_single_row(
                source_engine="transition-table",
                source_file=parse_report.source_path,
                source_row_number=1,
                original_identifiers={
                    "transition_id": entry.transition_id,
                    "precursor_id": entry.precursor_id,
                    "sample_id": entry.sample_id,
                },
            ),
        )
        for entry in parse_report.accepted_entries
    )
    return _build_import_report(
        source_kind=TargetedResultSourceKind.TRANSITION_TABLE,
        source_name="transition table",
        observations=observations,
        note=(
            "targeted import keeps exported transition-table peptide, precursor, transition, sample intensity, retention-time, and quality-flag evidence explicit before any matrix rollup"
        ),
    )


def _build_import_report(
    *,
    source_kind: TargetedResultSourceKind,
    source_name: str,
    observations: tuple[TargetedResultObservation, ...],
    note: str,
) -> TargetedResultImportReport:
    return TargetedResultImportReport(
        source_kind=source_kind,
        source_name=source_name,
        observations=observations,
        summary=TargetedResultImportSummary(
            observation_count=len(observations),
            precursor_count=len({item.precursor_id for item in observations}),
            transition_count=len({item.transition_id for item in observations}),
            sample_count=len({item.sample_id for item in observations}),
            retention_time_count=sum(
                1 for item in observations if item.retention_time_minutes is not None
            ),
            quality_flag_count=sum(
                1 for item in observations if item.quality_flag is not None
            ),
        ),
        note=note,
    )


def _required_value(row: dict[str, str], *keys: str) -> str:
    value = _optional_value(row, *keys)
    if value is None:
        joined = " or ".join(keys)
        raise ValueError(f"targeted result row requires {joined}")
    return value


def _optional_value(row: dict[str, str], *keys: str) -> str | None:
    for key in keys:
        if key in row:
            text = (row[key] or "").strip()
            if text:
                return text
    return None


def _optional_float(value: str | None) -> float | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    return float(stripped)


def render_targeted_result_observation_tsv(report: TargetedResultImportReport) -> str:
    """Render imported targeted observations as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "source_kind",
            "transition_id",
            "precursor_id",
            "precursor_charge",
            "peptide_sequence",
            "sample_id",
            "intensity",
            "retention_time_minutes",
            "quality_flag",
            "protein_ref",
            "fragment_label",
            "precursor_mz",
            "fragment_mz",
            *ImportedEvidenceProvenance.tsv_header(),
        ]
    )
    for item in report.observations:
        writer.writerow(
            [
                item.source_kind.value,
                item.transition_id,
                item.precursor_id,
                "" if item.precursor_charge is None else item.precursor_charge,
                item.peptide_sequence,
                item.sample_id,
                f"{item.intensity:g}",
                (
                    ""
                    if item.retention_time_minutes is None
                    else f"{item.retention_time_minutes:g}"
                ),
                "" if item.quality_flag is None else item.quality_flag,
                "" if item.protein_ref is None else item.protein_ref,
                "" if item.fragment_label is None else item.fragment_label,
                "" if item.precursor_mz is None else f"{item.precursor_mz:g}",
                "" if item.fragment_mz is None else f"{item.fragment_mz:g}",
                *item.provenance.to_tsv_cells(),
            ]
        )
    return buffer.getvalue()
