# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Protein annotation parsing and mapping surfaces for biological interpretation."""

from __future__ import annotations

import csv
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.sequences import canonicalize_protein_reference
from bijux_proteomics_foundation import JsonModel


class ProteinReferenceColumnMapping(JsonModel):
    """Column mapping from an input protein table into owned protein-reference fields."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    row_id: str | None = None


class ProteinReferenceEntry(JsonModel):
    """One normalized protein-reference entry from an input protein table."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    source_row_id: str | None = None
    input_protein_ref: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    metadata: dict[str, str] = Field(default_factory=dict)


class RejectedProteinReferenceRow(JsonModel):
    """One rejected protein-reference row with an explicit stable reason."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    values: dict[str, str] = Field(default_factory=dict)
    reason: str = Field(..., min_length=1)


class ProteinReferenceTableSummary(JsonModel):
    """Stable summary over one parsed protein-reference table."""

    model_config = ConfigDict(extra="forbid")

    accepted_entry_count: int = Field(..., ge=0)
    rejected_row_count: int = Field(..., ge=0)
    distinct_protein_ref_count: int = Field(..., ge=0)


class ProteinReferenceTableReport(JsonModel):
    """Governed parse report over one input protein table."""

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(..., min_length=1)
    total_rows: int = Field(..., ge=0)
    accepted_entries: tuple[ProteinReferenceEntry, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[RejectedProteinReferenceRow, ...] = Field(default_factory=tuple)
    column_mapping: ProteinReferenceColumnMapping
    summary: ProteinReferenceTableSummary
    note: str = Field(..., min_length=1)


class ProteinAnnotationColumnMapping(JsonModel):
    """Column mapping from a custom protein-annotation table into owned annotation fields."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    gene_symbol: str | None = None
    description: str | None = None
    organism: str | None = None
    annotation_identifier: str | None = None


class ProteinAnnotationRecord(JsonModel):
    """One normalized protein annotation from FASTA-adjacent or custom sources."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    gene_symbol: str | None = None
    description: str | None = None
    organism: str | None = None
    annotation_identifier: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class RejectedProteinAnnotationRow(JsonModel):
    """One rejected custom protein-annotation row with an explicit stable reason."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    values: dict[str, str] = Field(default_factory=dict)
    reason: str = Field(..., min_length=1)


class ProteinAnnotationImportSummary(JsonModel):
    """Stable summary over one imported custom protein-annotation table."""

    model_config = ConfigDict(extra="forbid")

    accepted_record_count: int = Field(..., ge=0)
    rejected_row_count: int = Field(..., ge=0)
    distinct_protein_ref_count: int = Field(..., ge=0)
    gene_annotated_count: int = Field(..., ge=0)
    description_annotated_count: int = Field(..., ge=0)
    organism_annotated_count: int = Field(..., ge=0)
    annotation_identifier_count: int = Field(..., ge=0)


class ProteinAnnotationImportReport(JsonModel):
    """Governed parse report over one custom protein-annotation table."""

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(..., min_length=1)
    total_rows: int = Field(..., ge=0)
    accepted_records: tuple[ProteinAnnotationRecord, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[RejectedProteinAnnotationRow, ...] = Field(default_factory=tuple)
    column_mapping: ProteinAnnotationColumnMapping
    summary: ProteinAnnotationImportSummary
    note: str = Field(..., min_length=1)


def parse_protein_reference_table(
    path: Path,
    *,
    mapping: ProteinReferenceColumnMapping | None = None,
    protein_separator: str = ";",
) -> ProteinReferenceTableReport:
    """Parse one protein table into normalized protein-reference entries."""

    lines = _read_delimited_lines(path)
    active_mapping = mapping or ProteinReferenceColumnMapping(
        protein_ref="protein_ref",
        row_id="row_id",
    )
    if not lines:
        return ProteinReferenceTableReport(
            source_path=str(path),
            total_rows=0,
            column_mapping=active_mapping,
            summary=ProteinReferenceTableSummary(
                accepted_entry_count=0,
                rejected_row_count=1,
                distinct_protein_ref_count=0,
            ),
            rejected_rows=(
                RejectedProteinReferenceRow(
                    row_number=2,
                    reason="protein table is empty",
                ),
            ),
            note="protein table did not contain any readable rows",
        )

    reader = csv.DictReader(lines, delimiter=_infer_delimiter(lines[0]))
    if reader.fieldnames is None:
        raise ValueError("protein table must include a header row")
    _validate_required_columns(reader.fieldnames, (active_mapping.protein_ref,))

    accepted_entries: list[ProteinReferenceEntry] = []
    rejected_rows: list[RejectedProteinReferenceRow] = []
    for row_number, raw_row in enumerate(reader, start=2):
        normalized_row = _normalize_row(raw_row)
        protein_cell = normalized_row.get(active_mapping.protein_ref, "")
        row_id = (
            None
            if active_mapping.row_id is None
            else normalized_row.get(active_mapping.row_id, "").strip() or None
        )
        protein_tokens = [
            token.strip()
            for token in protein_cell.split(protein_separator)
            if token.strip()
        ]
        if not protein_tokens:
            rejected_rows.append(
                RejectedProteinReferenceRow(
                    row_number=row_number,
                    values=normalized_row,
                    reason="protein row requires at least one protein reference",
                )
            )
            continue
        metadata = {
            key: value
            for key, value in normalized_row.items()
            if key not in {active_mapping.protein_ref, active_mapping.row_id}
            and value
        }
        for token in protein_tokens:
            accepted_entries.append(
                ProteinReferenceEntry(
                    row_number=row_number,
                    source_row_id=row_id,
                    input_protein_ref=token,
                    protein_ref=canonicalize_protein_reference(token),
                    metadata=metadata,
                )
            )

    distinct_protein_refs = {entry.protein_ref for entry in accepted_entries}
    return ProteinReferenceTableReport(
        source_path=str(path),
        total_rows=max(len(lines) - 1, 0),
        accepted_entries=tuple(accepted_entries),
        rejected_rows=tuple(rejected_rows),
        column_mapping=active_mapping,
        summary=ProteinReferenceTableSummary(
            accepted_entry_count=len(accepted_entries),
            rejected_row_count=len(rejected_rows),
            distinct_protein_ref_count=len(distinct_protein_refs),
        ),
        note="protein references were canonicalized onto the shared sequence accession surface",
    )


def parse_protein_annotation_table(
    path: Path,
    *,
    mapping: ProteinAnnotationColumnMapping | None = None,
) -> ProteinAnnotationImportReport:
    """Parse one custom protein-annotation table into owned normalized records."""

    lines = _read_delimited_lines(path)
    active_mapping = mapping or ProteinAnnotationColumnMapping(
        protein_ref="protein_ref",
        gene_symbol="gene_symbol",
        description="description",
        organism="organism",
        annotation_identifier="annotation_identifier",
    )
    if not lines:
        return ProteinAnnotationImportReport(
            source_path=str(path),
            total_rows=0,
            column_mapping=active_mapping,
            summary=ProteinAnnotationImportSummary(
                accepted_record_count=0,
                rejected_row_count=1,
                distinct_protein_ref_count=0,
                gene_annotated_count=0,
                description_annotated_count=0,
                organism_annotated_count=0,
                annotation_identifier_count=0,
            ),
            rejected_rows=(
                RejectedProteinAnnotationRow(
                    row_number=2,
                    reason="protein annotation table is empty",
                ),
            ),
            note="protein annotation table did not contain any readable rows",
        )

    reader = csv.DictReader(lines, delimiter=_infer_delimiter(lines[0]))
    if reader.fieldnames is None:
        raise ValueError("protein annotation table must include a header row")
    _validate_required_columns(reader.fieldnames, (active_mapping.protein_ref,))

    accepted_records: list[ProteinAnnotationRecord] = []
    rejected_rows: list[RejectedProteinAnnotationRow] = []
    seen_protein_refs: set[str] = set()
    for row_number, raw_row in enumerate(reader, start=2):
        normalized_row = _normalize_row(raw_row)
        protein_token = normalized_row.get(active_mapping.protein_ref, "").strip()
        if not protein_token:
            rejected_rows.append(
                RejectedProteinAnnotationRow(
                    row_number=row_number,
                    values=normalized_row,
                    reason="protein annotation row requires protein_ref",
                )
            )
            continue
        protein_ref = canonicalize_protein_reference(protein_token)
        gene_symbol = _optional_value(normalized_row, active_mapping.gene_symbol)
        description = _optional_value(normalized_row, active_mapping.description)
        organism = _optional_value(normalized_row, active_mapping.organism)
        annotation_identifier = _optional_value(
            normalized_row, active_mapping.annotation_identifier
        )
        if (
            gene_symbol is None
            and description is None
            and organism is None
            and annotation_identifier is None
        ):
            rejected_rows.append(
                RejectedProteinAnnotationRow(
                    row_number=row_number,
                    values=normalized_row,
                    reason="protein annotation row requires at least one annotation field",
                )
            )
            continue
        if protein_ref in seen_protein_refs:
            rejected_rows.append(
                RejectedProteinAnnotationRow(
                    row_number=row_number,
                    values=normalized_row,
                    reason=f"duplicate protein annotation for {protein_ref}",
                )
            )
            continue
        seen_protein_refs.add(protein_ref)
        accepted_records.append(
            ProteinAnnotationRecord(
                protein_ref=protein_ref,
                gene_symbol=gene_symbol,
                description=description,
                organism=organism,
                annotation_identifier=annotation_identifier,
                metadata={
                    key: value
                    for key, value in normalized_row.items()
                    if key
                    not in {
                        active_mapping.protein_ref,
                        active_mapping.gene_symbol,
                        active_mapping.description,
                        active_mapping.organism,
                        active_mapping.annotation_identifier,
                    }
                    and value
                },
            )
        )

    return ProteinAnnotationImportReport(
        source_path=str(path),
        total_rows=max(len(lines) - 1, 0),
        accepted_records=tuple(accepted_records),
        rejected_rows=tuple(rejected_rows),
        column_mapping=active_mapping,
        summary=ProteinAnnotationImportSummary(
            accepted_record_count=len(accepted_records),
            rejected_row_count=len(rejected_rows),
            distinct_protein_ref_count=len({record.protein_ref for record in accepted_records}),
            gene_annotated_count=sum(
                1 for record in accepted_records if record.gene_symbol is not None
            ),
            description_annotated_count=sum(
                1 for record in accepted_records if record.description is not None
            ),
            organism_annotated_count=sum(
                1 for record in accepted_records if record.organism is not None
            ),
            annotation_identifier_count=sum(
                1
                for record in accepted_records
                if record.annotation_identifier is not None
            ),
        ),
        note="custom protein annotations were canonicalized onto the shared sequence accession surface",
    )


def _infer_delimiter(header_line: str) -> str:
    return "\t" if "\t" in header_line else ","


def _normalize_row(raw_row: dict[str | None, str | None]) -> dict[str, str]:
    return {
        (key or "").strip(): (value or "").strip()
        for key, value in raw_row.items()
        if key is not None
    }


def _optional_value(row: dict[str, str], field_name: str | None) -> str | None:
    if field_name is None:
        return None
    value = row.get(field_name, "").strip()
    return value or None


def _read_delimited_lines(path: Path) -> list[str]:
    payload = path.read_text(encoding="utf-8")
    return payload.splitlines()


def _validate_required_columns(fieldnames: list[str], required_columns: tuple[str, ...]) -> None:
    available = {field.strip() for field in fieldnames}
    missing = [column for column in required_columns if column not in available]
    if missing:
        raise ValueError(
            "missing required columns: " + ", ".join(sorted(missing))
        )
