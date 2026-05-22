# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Protein annotation parsing and mapping surfaces for biological interpretation."""

from __future__ import annotations

import csv
from enum import StrEnum
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.sequences import canonicalize_protein_reference
from bijux_proteomics.sequences.core import NormalizedProteinRecord
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


class ProteinAnnotationSourceKind(StrEnum):
    """Stable source kinds for protein annotation provenance."""

    FASTA = "fasta"
    CUSTOM = "custom"
    MERGED = "merged"


class ProteinAnnotationEntry(JsonModel):
    """One mapped protein annotation row with explicit provenance."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    source_row_id: str | None = None
    input_protein_ref: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    accession_namespace: str | None = None
    source_identifier: str | None = None
    gene_symbol: str | None = None
    description: str | None = None
    organism: str | None = None
    annotation_identifier: str = Field(..., min_length=1)
    annotation_source: ProteinAnnotationSourceKind
    input_metadata: dict[str, str] = Field(default_factory=dict)
    annotation_metadata: dict[str, str] = Field(default_factory=dict)


class UnmappedProteinAnnotationEntry(JsonModel):
    """One input protein reference that could not be annotated."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    source_row_id: str | None = None
    input_protein_ref: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    input_metadata: dict[str, str] = Field(default_factory=dict)
    reason: str = Field(..., min_length=1)


class ProteinAnnotationMappingSummary(JsonModel):
    """Stable summary over protein annotation mapping results."""

    model_config = ConfigDict(extra="forbid")

    input_entry_count: int = Field(..., ge=0)
    mapped_entry_count: int = Field(..., ge=0)
    unmapped_entry_count: int = Field(..., ge=0)
    distinct_protein_ref_count: int = Field(..., ge=0)
    fasta_annotation_count: int = Field(..., ge=0)
    custom_annotation_count: int = Field(..., ge=0)
    merged_annotation_count: int = Field(..., ge=0)
    gene_annotated_count: int = Field(..., ge=0)
    description_annotated_count: int = Field(..., ge=0)
    organism_annotated_count: int = Field(..., ge=0)


class ProteinAnnotationMappingReport(JsonModel):
    """Owned mapping report from protein references into biological annotations."""

    model_config = ConfigDict(extra="forbid")

    mapped_entries: tuple[ProteinAnnotationEntry, ...] = Field(default_factory=tuple)
    unmapped_entries: tuple[UnmappedProteinAnnotationEntry, ...] = Field(
        default_factory=tuple
    )
    summary: ProteinAnnotationMappingSummary
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


def build_protein_annotation_mapping_report(
    protein_entries: tuple[ProteinReferenceEntry, ...],
    fasta_records: tuple[NormalizedProteinRecord, ...],
    *,
    custom_annotations: tuple[ProteinAnnotationRecord, ...] = (),
) -> ProteinAnnotationMappingReport:
    """Map protein-reference entries onto FASTA and custom biological annotations."""

    fasta_annotations = {
        record.canonical_accession: record for record in fasta_records if not record.decoy
    }
    custom_annotation_map = {
        record.protein_ref: record for record in custom_annotations
    }
    mapped_entries: list[ProteinAnnotationEntry] = []
    unmapped_entries: list[UnmappedProteinAnnotationEntry] = []
    for entry in protein_entries:
        fasta_record = fasta_annotations.get(entry.protein_ref)
        custom_record = custom_annotation_map.get(entry.protein_ref)
        if fasta_record is None and custom_record is None:
            unmapped_entries.append(
                UnmappedProteinAnnotationEntry(
                    row_number=entry.row_number,
                    source_row_id=entry.source_row_id,
                    input_protein_ref=entry.input_protein_ref,
                    protein_ref=entry.protein_ref,
                    input_metadata=entry.metadata,
                    reason=(
                        "protein reference was not present in the FASTA annotations "
                        "or the custom annotation table"
                    ),
                )
            )
            continue
        annotation_source = _annotation_source_kind(fasta_record, custom_record)
        mapped_entries.append(
            ProteinAnnotationEntry(
                row_number=entry.row_number,
                source_row_id=entry.source_row_id,
                input_protein_ref=entry.input_protein_ref,
                protein_ref=entry.protein_ref,
                accession_namespace=(
                    None if fasta_record is None else fasta_record.accession_namespace
                ),
                source_identifier=(
                    None if fasta_record is None else fasta_record.source_identifier
                ),
                gene_symbol=_merged_gene_symbol(fasta_record, custom_record),
                description=_merged_description(fasta_record, custom_record),
                organism=_merged_organism(fasta_record, custom_record),
                annotation_identifier=_merged_annotation_identifier(
                    entry.protein_ref,
                    fasta_record,
                    custom_record,
                ),
                annotation_source=annotation_source,
                input_metadata=entry.metadata,
                annotation_metadata=(
                    {} if custom_record is None else custom_record.metadata
                ),
            )
        )

    summary = ProteinAnnotationMappingSummary(
        input_entry_count=len(protein_entries),
        mapped_entry_count=len(mapped_entries),
        unmapped_entry_count=len(unmapped_entries),
        distinct_protein_ref_count=len({entry.protein_ref for entry in protein_entries}),
        fasta_annotation_count=sum(
            1
            for entry in mapped_entries
            if entry.annotation_source is ProteinAnnotationSourceKind.FASTA
        ),
        custom_annotation_count=sum(
            1
            for entry in mapped_entries
            if entry.annotation_source is ProteinAnnotationSourceKind.CUSTOM
        ),
        merged_annotation_count=sum(
            1
            for entry in mapped_entries
            if entry.annotation_source is ProteinAnnotationSourceKind.MERGED
        ),
        gene_annotated_count=sum(
            1 for entry in mapped_entries if entry.gene_symbol is not None
        ),
        description_annotated_count=sum(
            1 for entry in mapped_entries if entry.description is not None
        ),
        organism_annotated_count=sum(
            1 for entry in mapped_entries if entry.organism is not None
        ),
    )
    return ProteinAnnotationMappingReport(
        mapped_entries=tuple(mapped_entries),
        unmapped_entries=tuple(unmapped_entries),
        summary=summary,
        note=(
            "custom annotations supplement or override FASTA-derived gene, description, "
            "organism, and identifier fields while preserving explicit unmapped rows"
        ),
    )


def _infer_delimiter(header_line: str) -> str:
    return "\t" if "\t" in header_line else ","


def _annotation_source_kind(
    fasta_record: NormalizedProteinRecord | None,
    custom_record: ProteinAnnotationRecord | None,
) -> ProteinAnnotationSourceKind:
    if fasta_record is not None and custom_record is not None:
        return ProteinAnnotationSourceKind.MERGED
    if custom_record is not None:
        return ProteinAnnotationSourceKind.CUSTOM
    return ProteinAnnotationSourceKind.FASTA


def _merged_gene_symbol(
    fasta_record: NormalizedProteinRecord | None,
    custom_record: ProteinAnnotationRecord | None,
) -> str | None:
    if custom_record is not None and custom_record.gene_symbol is not None:
        return custom_record.gene_symbol
    return None if fasta_record is None else fasta_record.gene


def _merged_description(
    fasta_record: NormalizedProteinRecord | None,
    custom_record: ProteinAnnotationRecord | None,
) -> str | None:
    if custom_record is not None and custom_record.description is not None:
        return custom_record.description
    if fasta_record is None or not fasta_record.description:
        return None
    return fasta_record.description


def _merged_organism(
    fasta_record: NormalizedProteinRecord | None,
    custom_record: ProteinAnnotationRecord | None,
) -> str | None:
    if custom_record is not None and custom_record.organism is not None:
        return custom_record.organism
    return None if fasta_record is None else fasta_record.organism


def _merged_annotation_identifier(
    protein_ref: str,
    fasta_record: NormalizedProteinRecord | None,
    custom_record: ProteinAnnotationRecord | None,
) -> str:
    if custom_record is not None and custom_record.annotation_identifier is not None:
        return custom_record.annotation_identifier
    if fasta_record is not None:
        return fasta_record.source_identifier
    return protein_ref


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
