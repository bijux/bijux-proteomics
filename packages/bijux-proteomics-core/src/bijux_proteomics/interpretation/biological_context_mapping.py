# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""User-supplied biological context mapping surfaces for downstream interpretation."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
import csv
from enum import StrEnum
import json
from io import StringIO
from pathlib import Path
from typing import TypedDict

from pydantic import ConfigDict, Field

from bijux_proteomics.interpretation.protein_annotation_mapping import (
    ProteinReferenceEntry,
)
from bijux_proteomics.sequences import canonicalize_protein_reference
from bijux_proteomics_foundation import JsonModel


class BiologicalContextKind(StrEnum):
    """Supported user-supplied biological context kinds."""

    DRUG_TARGET = "drug_target"
    DISEASE_TERM = "disease_term"
    PHENOTYPE_TERM = "phenotype_term"
    SUBCELLULAR_COMPARTMENT = "subcellular_compartment"
    TISSUE_MARKER = "tissue_marker"
    CELL_TYPE_MARKER = "cell_type_marker"


class BiologicalContextColumnMapping(JsonModel):
    """Column mapping from one biological-context table into owned fields."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    context_id: str = Field(..., min_length=1)
    context_kind: str | None = None
    context_name: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    evidence: str | None = None


class BiologicalContextRecord(JsonModel):
    """One normalized user-supplied biological context relationship."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    context_kind: BiologicalContextKind
    context_id: str = Field(..., min_length=1)
    context_name: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    evidence: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class RejectedBiologicalContextRow(JsonModel):
    """One rejected biological-context row with a stable reason."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    values: dict[str, str] = Field(default_factory=dict)
    reason: str = Field(..., min_length=1)


class BiologicalContextImportSummary(JsonModel):
    """Stable summary over one biological-context import pass."""

    model_config = ConfigDict(extra="forbid")

    accepted_record_count: int = Field(..., ge=0)
    rejected_row_count: int = Field(..., ge=0)
    distinct_protein_ref_count: int = Field(..., ge=0)
    distinct_context_count: int = Field(..., ge=0)
    context_kind_counts: dict[str, int] = Field(default_factory=dict)


class BiologicalContextImportReport(JsonModel):
    """Governed import report over one user-supplied biological-context table."""

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(..., min_length=1)
    total_rows: int = Field(..., ge=0)
    accepted_records: tuple[BiologicalContextRecord, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[RejectedBiologicalContextRow, ...] = Field(default_factory=tuple)
    column_mapping: BiologicalContextColumnMapping
    fixed_context_kind: BiologicalContextKind | None = None
    summary: BiologicalContextImportSummary
    note: str = Field(..., min_length=1)


class BiologicalContextMappingEntry(JsonModel):
    """One mapped protein-to-context relationship over selected proteins."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    source_row_id: str | None = None
    input_protein_ref: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    context_kind: BiologicalContextKind
    context_id: str = Field(..., min_length=1)
    context_name: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    evidence: str | None = None
    input_metadata: dict[str, str] = Field(default_factory=dict)
    context_metadata: dict[str, str] = Field(default_factory=dict)


class UnmappedBiologicalContextEntry(JsonModel):
    """One selected protein without any supplied biological context."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    source_row_id: str | None = None
    input_protein_ref: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    input_metadata: dict[str, str] = Field(default_factory=dict)
    reason: str = Field(..., min_length=1)


class BiologicalContextTermEntry(JsonModel):
    """One aggregated biological context term with explicit supporting proteins."""

    model_config = ConfigDict(extra="forbid")

    context_kind: BiologicalContextKind
    context_id: str = Field(..., min_length=1)
    context_name: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    evidence_values: tuple[str, ...] = Field(default_factory=tuple)
    supporting_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    supporting_protein_count: int = Field(..., ge=1)


class BiologicalContextMappingSummary(JsonModel):
    """Stable summary over one user-supplied biological-context mapping run."""

    model_config = ConfigDict(extra="forbid")

    input_entry_count: int = Field(..., ge=0)
    mapped_entry_count: int = Field(..., ge=0)
    unmapped_entry_count: int = Field(..., ge=0)
    distinct_mapped_protein_ref_count: int = Field(..., ge=0)
    term_count: int = Field(..., ge=0)
    context_kind_counts: dict[str, int] = Field(default_factory=dict)


class BiologicalContextMappingReport(JsonModel):
    """Owned report over mapping proteins to user-supplied biological context."""

    model_config = ConfigDict(extra="forbid")

    mapped_entries: tuple[BiologicalContextMappingEntry, ...] = Field(default_factory=tuple)
    unmapped_entries: tuple[UnmappedBiologicalContextEntry, ...] = Field(
        default_factory=tuple
    )
    term_entries: tuple[BiologicalContextTermEntry, ...] = Field(default_factory=tuple)
    summary: BiologicalContextMappingSummary
    note: str = Field(..., min_length=1)


class _BiologicalContextTermSupport(TypedDict):
    context_kind: BiologicalContextKind
    context_id: str
    context_name: str | None
    source_name: str | None
    source_accession: str | None
    evidence_values: set[str]
    supporting_protein_refs: set[str]


def parse_biological_context_table(
    path: Path,
    *,
    mapping: BiologicalContextColumnMapping | None = None,
    fixed_context_kind: BiologicalContextKind | None = None,
) -> BiologicalContextImportReport:
    """Parse one user-supplied biological-context table into owned records."""

    lines = _read_delimited_lines(path)
    active_mapping = mapping or BiologicalContextColumnMapping(
        protein_ref="protein_ref",
        context_id="context_id",
        context_kind="context_kind",
        context_name="context_name",
        source_name="source_name",
        source_accession="source_accession",
        evidence="evidence",
    )
    if not lines:
        return BiologicalContextImportReport(
            source_path=str(path),
            total_rows=0,
            accepted_records=(),
            rejected_rows=(
                RejectedBiologicalContextRow(
                    row_number=2,
                    reason="biological context table is empty",
                ),
            ),
            column_mapping=active_mapping,
            fixed_context_kind=fixed_context_kind,
            summary=BiologicalContextImportSummary(
                accepted_record_count=0,
                rejected_row_count=1,
                distinct_protein_ref_count=0,
                distinct_context_count=0,
                context_kind_counts={},
            ),
            note="biological context table did not contain any readable rows",
        )

    reader = csv.DictReader(lines, delimiter=_infer_delimiter(lines[0]))
    if reader.fieldnames is None:
        raise ValueError("biological context table must include a header row")
    required_columns = [active_mapping.protein_ref, active_mapping.context_id]
    if active_mapping.context_kind is not None and fixed_context_kind is None:
        required_columns.append(active_mapping.context_kind)
    _validate_required_columns(reader.fieldnames, tuple(required_columns))

    accepted_records: list[BiologicalContextRecord] = []
    rejected_rows: list[RejectedBiologicalContextRow] = []
    seen_records: set[tuple[str, str, str, str | None, str | None]] = set()
    for row_number, raw_row in enumerate(reader, start=2):
        values = _normalize_row(raw_row)
        protein_token = values.get(active_mapping.protein_ref, "").strip()
        if not protein_token:
            rejected_rows.append(
                RejectedBiologicalContextRow(
                    row_number=row_number,
                    values=values,
                    reason="biological context row requires protein_ref",
                )
            )
            continue
        context_id = values.get(active_mapping.context_id, "").strip()
        if not context_id:
            rejected_rows.append(
                RejectedBiologicalContextRow(
                    row_number=row_number,
                    values=values,
                    reason="biological context row requires context_id",
                )
            )
            continue
        kind_token = (
            fixed_context_kind.value
            if fixed_context_kind is not None
            else values.get(active_mapping.context_kind or "", "").strip()
        )
        if not kind_token:
            rejected_rows.append(
                RejectedBiologicalContextRow(
                    row_number=row_number,
                    values=values,
                    reason=(
                        "biological context row requires context_kind unless a fixed "
                        "context kind is supplied"
                    ),
                )
            )
            continue
        try:
            context_kind = BiologicalContextKind(kind_token)
        except ValueError:
            rejected_rows.append(
                RejectedBiologicalContextRow(
                    row_number=row_number,
                    values=values,
                    reason=(
                        "unsupported biological context kind "
                        f"{kind_token!r}; expected one of "
                        + ", ".join(kind.value for kind in BiologicalContextKind)
                    ),
                )
            )
            continue
        protein_ref = canonicalize_protein_reference(protein_token)
        dedupe_key = (
            protein_ref,
            context_kind.value,
            context_id,
            _optional_value(values, active_mapping.source_name),
            _optional_value(values, active_mapping.source_accession),
        )
        if dedupe_key in seen_records:
            rejected_rows.append(
                RejectedBiologicalContextRow(
                    row_number=row_number,
                    values=values,
                    reason=(
                        "duplicate biological context mapping for "
                        f"{protein_ref} / {context_kind.value} / {context_id}"
                    ),
                )
            )
            continue
        seen_records.add(dedupe_key)
        accepted_records.append(
            BiologicalContextRecord(
                protein_ref=protein_ref,
                context_kind=context_kind,
                context_id=context_id,
                context_name=_optional_value(values, active_mapping.context_name),
                source_name=_optional_value(values, active_mapping.source_name),
                source_accession=_optional_value(values, active_mapping.source_accession),
                evidence=_optional_value(values, active_mapping.evidence),
                metadata={
                    key: value
                    for key, value in values.items()
                    if key
                    not in {
                        active_mapping.protein_ref,
                        active_mapping.context_id,
                        active_mapping.context_kind,
                        active_mapping.context_name,
                        active_mapping.source_name,
                        active_mapping.source_accession,
                        active_mapping.evidence,
                    }
                    and value
                },
            )
        )

    context_kind_counts: dict[str, int] = {}
    for record in accepted_records:
        context_kind_counts[record.context_kind.value] = (
            context_kind_counts.get(record.context_kind.value, 0) + 1
        )
    return BiologicalContextImportReport(
        source_path=str(path),
        total_rows=max(len(lines) - 1, 0),
        accepted_records=tuple(accepted_records),
        rejected_rows=tuple(rejected_rows),
        column_mapping=active_mapping,
        fixed_context_kind=fixed_context_kind,
        summary=BiologicalContextImportSummary(
            accepted_record_count=len(accepted_records),
            rejected_row_count=len(rejected_rows),
            distinct_protein_ref_count=len(
                {record.protein_ref for record in accepted_records}
            ),
            distinct_context_count=len(
                {
                    (
                        record.context_kind.value,
                        record.context_id,
                        record.source_name,
                        record.source_accession,
                    )
                    for record in accepted_records
                }
            ),
            context_kind_counts=dict(sorted(context_kind_counts.items())),
        ),
        note=(
            "biological context import preserves only user-supplied drug, disease, phenotype, "
            "subcellular, tissue-marker, and cell-type-marker annotations, and it rejects "
            "duplicate or underspecified claims"
        ),
    )


def build_biological_context_mapping_report(
    protein_entries: tuple[ProteinReferenceEntry, ...],
    context_records: tuple[BiologicalContextRecord, ...],
) -> BiologicalContextMappingReport:
    """Map selected proteins onto user-supplied biological context records."""

    context_by_protein: dict[str, list[BiologicalContextRecord]] = defaultdict(list)
    for record in context_records:
        context_by_protein[record.protein_ref].append(record)

    mapped_entries: list[BiologicalContextMappingEntry] = []
    unmapped_entries: list[UnmappedBiologicalContextEntry] = []
    term_support: dict[
        tuple[str, str, str | None, str | None, str | None],
        _BiologicalContextTermSupport,
    ] = {}
    context_kind_counts: dict[str, int] = {}
    for entry in protein_entries:
        matches = tuple(
            sorted(
                context_by_protein.get(entry.protein_ref, ()),
                key=lambda record: (
                    record.context_kind.value,
                    record.context_id,
                    record.source_name or "",
                    record.source_accession or "",
                ),
            )
        )
        if not matches:
            unmapped_entries.append(
                UnmappedBiologicalContextEntry(
                    row_number=entry.row_number,
                    source_row_id=entry.source_row_id,
                    input_protein_ref=entry.input_protein_ref,
                    protein_ref=entry.protein_ref,
                    input_metadata=entry.metadata,
                    reason=(
                        "protein had no user-supplied biological context annotation"
                    ),
                )
            )
            continue
        for match in matches:
            mapped_entries.append(
                BiologicalContextMappingEntry(
                    row_number=entry.row_number,
                    source_row_id=entry.source_row_id,
                    input_protein_ref=entry.input_protein_ref,
                    protein_ref=entry.protein_ref,
                    context_kind=match.context_kind,
                    context_id=match.context_id,
                    context_name=match.context_name,
                    source_name=match.source_name,
                    source_accession=match.source_accession,
                    evidence=match.evidence,
                    input_metadata=entry.metadata,
                    context_metadata=match.metadata,
                )
            )
            context_kind_counts[match.context_kind.value] = (
                context_kind_counts.get(match.context_kind.value, 0) + 1
            )
            term_key = (
                match.context_kind.value,
                match.context_id,
                match.context_name,
                match.source_name,
                match.source_accession,
            )
            support = term_support.setdefault(
                term_key,
                {
                    "context_kind": match.context_kind,
                    "context_id": match.context_id,
                    "context_name": match.context_name,
                    "source_name": match.source_name,
                    "source_accession": match.source_accession,
                    "evidence_values": set(),
                    "supporting_protein_refs": set(),
                },
            )
            if match.evidence:
                support["evidence_values"].add(match.evidence)
            support["supporting_protein_refs"].add(entry.protein_ref)

    term_entries = tuple(
        sorted(
            (
                BiologicalContextTermEntry(
                    context_kind=support["context_kind"],
                    context_id=support["context_id"],
                    context_name=support["context_name"],
                    source_name=support["source_name"],
                    source_accession=support["source_accession"],
                    evidence_values=tuple(sorted(support["evidence_values"])),
                    supporting_protein_refs=tuple(
                        sorted(support["supporting_protein_refs"])
                    ),
                    supporting_protein_count=len(support["supporting_protein_refs"]),
                )
                for support in term_support.values()
            ),
            key=lambda entry: (
                entry.context_kind.value,
                entry.context_id,
                entry.source_name or "",
                entry.source_accession or "",
            ),
        )
    )
    return BiologicalContextMappingReport(
        mapped_entries=tuple(mapped_entries),
        unmapped_entries=tuple(unmapped_entries),
        term_entries=term_entries,
        summary=BiologicalContextMappingSummary(
            input_entry_count=len(protein_entries),
            mapped_entry_count=len(mapped_entries),
            unmapped_entry_count=len(unmapped_entries),
            distinct_mapped_protein_ref_count=len(
                {entry.protein_ref for entry in mapped_entries}
            ),
            term_count=len(term_entries),
            context_kind_counts=dict(sorted(context_kind_counts.items())),
        ),
        note=(
            "biological context mapping makes no external claim unless a user-supplied context table "
            "provides that claim explicitly, and every aggregated term preserves its supporting proteins"
        ),
    )


def render_biological_context_mapping_summary_tsv(
    report: BiologicalContextMappingReport,
) -> str:
    """Render the compact biological-context mapping summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "input_entry_count",
            "mapped_entry_count",
            "unmapped_entry_count",
            "distinct_mapped_protein_ref_count",
            "term_count",
            "context_kind_counts",
        )
    )
    writer.writerow(
        (
            report.summary.input_entry_count,
            report.summary.mapped_entry_count,
            report.summary.unmapped_entry_count,
            report.summary.distinct_mapped_protein_ref_count,
            report.summary.term_count,
            json.dumps(report.summary.context_kind_counts, sort_keys=True),
        )
    )
    return buffer.getvalue()


def render_biological_context_mapping_tsv(
    report: BiologicalContextMappingReport,
) -> str:
    """Render mapped protein-to-context relationships as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "row_number",
            "source_row_id",
            "input_protein_ref",
            "protein_ref",
            "context_kind",
            "context_id",
            "context_name",
            "source_name",
            "source_accession",
            "evidence",
            "input_metadata",
            "context_metadata",
        )
    )
    for entry in report.mapped_entries:
        writer.writerow(
            (
                entry.row_number,
                entry.source_row_id or "",
                entry.input_protein_ref,
                entry.protein_ref,
                entry.context_kind.value,
                entry.context_id,
                entry.context_name or "",
                entry.source_name or "",
                entry.source_accession or "",
                entry.evidence or "",
                _metadata_json(entry.input_metadata),
                _metadata_json(entry.context_metadata),
            )
        )
    return buffer.getvalue()


def render_biological_context_term_tsv(report: BiologicalContextMappingReport) -> str:
    """Render aggregated biological-context terms with supporting proteins as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "context_kind",
            "context_id",
            "context_name",
            "source_name",
            "source_accession",
            "evidence_values",
            "supporting_protein_count",
            "supporting_protein_refs",
        )
    )
    for entry in report.term_entries:
        writer.writerow(
            (
                entry.context_kind.value,
                entry.context_id,
                entry.context_name or "",
                entry.source_name or "",
                entry.source_accession or "",
                ";".join(entry.evidence_values),
                entry.supporting_protein_count,
                ";".join(entry.supporting_protein_refs),
            )
        )
    return buffer.getvalue()


def render_unmapped_biological_context_tsv(
    report: BiologicalContextMappingReport,
) -> str:
    """Render unmapped proteins from one biological-context mapping run as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "row_number",
            "source_row_id",
            "input_protein_ref",
            "protein_ref",
            "input_metadata",
            "reason",
        )
    )
    for entry in report.unmapped_entries:
        writer.writerow(
            (
                entry.row_number,
                entry.source_row_id or "",
                entry.input_protein_ref,
                entry.protein_ref,
                _metadata_json(entry.input_metadata),
                entry.reason,
            )
        )
    return buffer.getvalue()


def render_rejected_biological_context_tsv(report: BiologicalContextImportReport) -> str:
    """Render rejected biological-context rows as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("row_number", "values", "reason"))
    for row in report.rejected_rows:
        writer.writerow((row.row_number, _metadata_json(row.values), row.reason))
    return buffer.getvalue()


def _read_delimited_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


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


def _metadata_json(values: dict[str, str]) -> str:
    return json.dumps(values, sort_keys=True)


def _validate_required_columns(
    fieldnames: Iterable[str],
    required_columns: tuple[str, ...],
) -> None:
    available = {field.strip() for field in fieldnames}
    missing = [column for column in required_columns if column not in available]
    if missing:
        raise ValueError("missing required columns: " + ", ".join(sorted(missing)))


__all__ = [
    "BiologicalContextColumnMapping",
    "BiologicalContextImportReport",
    "BiologicalContextImportSummary",
    "BiologicalContextKind",
    "BiologicalContextMappingEntry",
    "BiologicalContextMappingReport",
    "BiologicalContextMappingSummary",
    "BiologicalContextRecord",
    "BiologicalContextTermEntry",
    "RejectedBiologicalContextRow",
    "UnmappedBiologicalContextEntry",
    "build_biological_context_mapping_report",
    "parse_biological_context_table",
    "render_biological_context_mapping_summary_tsv",
    "render_biological_context_mapping_tsv",
    "render_biological_context_term_tsv",
    "render_rejected_biological_context_tsv",
    "render_unmapped_biological_context_tsv",
]
