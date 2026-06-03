# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Ortholog parsing and mapping surfaces for cross-species interpretation."""

from __future__ import annotations

from collections.abc import Iterable
import csv
from enum import StrEnum
from io import StringIO
import json
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.interpretation.protein_annotation_mapping import (
    ProteinReferenceEntry,
)
from bijux_proteomics.sequences import canonicalize_protein_reference
from bijux_proteomics_foundation import JsonModel


class OrthologColumnMapping(JsonModel):
    """Column mapping from one ortholog table into owned ortholog fields."""

    model_config = ConfigDict(extra="forbid")

    source_species: str = Field(..., min_length=1)
    source_protein_ref: str = Field(..., min_length=1)
    target_species: str = Field(..., min_length=1)
    target_protein_ref: str = Field(..., min_length=1)
    source_gene_symbol: str | None = None
    target_gene_symbol: str | None = None
    evidence: str | None = None


class OrthologRecord(JsonModel):
    """One normalized ortholog relationship row."""

    model_config = ConfigDict(extra="forbid")

    source_species: str = Field(..., min_length=1)
    source_protein_ref: str = Field(..., min_length=1)
    target_species: str = Field(..., min_length=1)
    target_protein_ref: str = Field(..., min_length=1)
    source_gene_symbol: str | None = None
    target_gene_symbol: str | None = None
    evidence: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class RejectedOrthologRow(JsonModel):
    """One rejected ortholog row with an explicit stable reason."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    values: dict[str, str] = Field(default_factory=dict)
    reason: str = Field(..., min_length=1)


class OrthologImportSummary(JsonModel):
    """Stable summary over one ortholog import pass."""

    model_config = ConfigDict(extra="forbid")

    accepted_record_count: int = Field(..., ge=0)
    rejected_row_count: int = Field(..., ge=0)
    distinct_source_species_count: int = Field(..., ge=0)
    distinct_target_species_count: int = Field(..., ge=0)
    distinct_source_protein_ref_count: int = Field(..., ge=0)
    distinct_target_protein_ref_count: int = Field(..., ge=0)


class OrthologImportReport(JsonModel):
    """Governed ortholog import report."""

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(..., min_length=1)
    total_rows: int = Field(..., ge=0)
    accepted_records: tuple[OrthologRecord, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[RejectedOrthologRow, ...] = Field(default_factory=tuple)
    column_mapping: OrthologColumnMapping
    summary: OrthologImportSummary
    note: str = Field(..., min_length=1)


class OrthologMappingCardinality(StrEnum):
    """Stable cardinality classes for one ortholog relationship edge."""

    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    MANY_TO_MANY = "many_to_many"


class OrthologMappingEntry(JsonModel):
    """One mapped source-target ortholog edge for a selected species pair."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    source_row_id: str | None = None
    input_protein_ref: str = Field(..., min_length=1)
    source_protein_ref: str = Field(..., min_length=1)
    source_species: str = Field(..., min_length=1)
    target_species: str = Field(..., min_length=1)
    target_protein_ref: str = Field(..., min_length=1)
    source_gene_symbol: str | None = None
    target_gene_symbol: str | None = None
    evidence: str | None = None
    mapping_cardinality: OrthologMappingCardinality
    source_match_count: int = Field(..., ge=1)
    target_match_count: int = Field(..., ge=1)
    input_metadata: dict[str, str] = Field(default_factory=dict)
    ortholog_metadata: dict[str, str] = Field(default_factory=dict)


class UnmappedOrthologEntry(JsonModel):
    """One source protein that did not map for the selected species pair."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    source_row_id: str | None = None
    input_protein_ref: str = Field(..., min_length=1)
    source_protein_ref: str = Field(..., min_length=1)
    source_species: str = Field(..., min_length=1)
    target_species: str = Field(..., min_length=1)
    input_metadata: dict[str, str] = Field(default_factory=dict)
    reason: str = Field(..., min_length=1)


class OrthologMappingSummary(JsonModel):
    """Stable summary over one ortholog mapping run."""

    model_config = ConfigDict(extra="forbid")

    input_entry_count: int = Field(..., ge=0)
    mapped_entry_count: int = Field(..., ge=0)
    unmapped_entry_count: int = Field(..., ge=0)
    distinct_source_protein_ref_count: int = Field(..., ge=0)
    distinct_target_protein_ref_count: int = Field(..., ge=0)
    one_to_one_count: int = Field(..., ge=0)
    one_to_many_count: int = Field(..., ge=0)
    many_to_one_count: int = Field(..., ge=0)
    many_to_many_count: int = Field(..., ge=0)
    ambiguous_mapping_count: int = Field(..., ge=0)


class OrthologMappingReport(JsonModel):
    """Owned report over one source-target ortholog mapping request."""

    model_config = ConfigDict(extra="forbid")

    source_species: str = Field(..., min_length=1)
    target_species: str = Field(..., min_length=1)
    mapped_entries: tuple[OrthologMappingEntry, ...] = Field(default_factory=tuple)
    unmapped_entries: tuple[UnmappedOrthologEntry, ...] = Field(default_factory=tuple)
    summary: OrthologMappingSummary
    note: str = Field(..., min_length=1)


def parse_ortholog_table(
    path: Path,
    *,
    mapping: OrthologColumnMapping | None = None,
) -> OrthologImportReport:
    """Parse one ortholog table into normalized source-target relationships."""

    lines = _read_delimited_lines(path)
    active_mapping = mapping or OrthologColumnMapping(
        source_species="source_species",
        source_protein_ref="source_protein_ref",
        target_species="target_species",
        target_protein_ref="target_protein_ref",
        source_gene_symbol="source_gene_symbol",
        target_gene_symbol="target_gene_symbol",
        evidence="evidence",
    )
    if not lines:
        return OrthologImportReport(
            source_path=str(path),
            total_rows=0,
            accepted_records=(),
            rejected_rows=(
                RejectedOrthologRow(
                    row_number=2,
                    reason="ortholog table is empty",
                ),
            ),
            column_mapping=active_mapping,
            summary=OrthologImportSummary(
                accepted_record_count=0,
                rejected_row_count=1,
                distinct_source_species_count=0,
                distinct_target_species_count=0,
                distinct_source_protein_ref_count=0,
                distinct_target_protein_ref_count=0,
            ),
            note="ortholog table did not contain any readable rows",
        )

    reader = csv.DictReader(lines, delimiter=_infer_delimiter(lines[0]))
    if reader.fieldnames is None:
        raise ValueError("ortholog table must include a header row")
    _validate_required_columns(
        reader.fieldnames,
        (
            active_mapping.source_species,
            active_mapping.source_protein_ref,
            active_mapping.target_species,
            active_mapping.target_protein_ref,
        ),
    )

    accepted_records: list[OrthologRecord] = []
    rejected_rows: list[RejectedOrthologRow] = []
    seen_relationships: set[tuple[str, str, str, str]] = set()
    for row_number, raw_row in enumerate(reader, start=2):
        values = _normalize_row(raw_row)
        source_species = values.get(active_mapping.source_species, "").strip()
        source_protein_token = values.get(active_mapping.source_protein_ref, "").strip()
        target_species = values.get(active_mapping.target_species, "").strip()
        target_protein_token = values.get(active_mapping.target_protein_ref, "").strip()
        if not source_species:
            rejected_rows.append(
                RejectedOrthologRow(
                    row_number=row_number,
                    values=values,
                    reason="ortholog row requires source_species",
                )
            )
            continue
        if not source_protein_token:
            rejected_rows.append(
                RejectedOrthologRow(
                    row_number=row_number,
                    values=values,
                    reason="ortholog row requires source_protein_ref",
                )
            )
            continue
        if not target_species:
            rejected_rows.append(
                RejectedOrthologRow(
                    row_number=row_number,
                    values=values,
                    reason="ortholog row requires target_species",
                )
            )
            continue
        if not target_protein_token:
            rejected_rows.append(
                RejectedOrthologRow(
                    row_number=row_number,
                    values=values,
                    reason="ortholog row requires target_protein_ref",
                )
            )
            continue
        source_protein_ref = canonicalize_protein_reference(source_protein_token)
        target_protein_ref = canonicalize_protein_reference(target_protein_token)
        relationship_key = (
            source_species,
            source_protein_ref,
            target_species,
            target_protein_ref,
        )
        if relationship_key in seen_relationships:
            rejected_rows.append(
                RejectedOrthologRow(
                    row_number=row_number,
                    values=values,
                    reason=(
                        "duplicate ortholog relationship for "
                        f"{source_species}:{source_protein_ref} -> "
                        f"{target_species}:{target_protein_ref}"
                    ),
                )
            )
            continue
        seen_relationships.add(relationship_key)
        accepted_records.append(
            OrthologRecord(
                source_species=source_species,
                source_protein_ref=source_protein_ref,
                target_species=target_species,
                target_protein_ref=target_protein_ref,
                source_gene_symbol=_optional_value(
                    values, active_mapping.source_gene_symbol
                ),
                target_gene_symbol=_optional_value(
                    values, active_mapping.target_gene_symbol
                ),
                evidence=_optional_value(values, active_mapping.evidence),
                metadata={
                    key: value
                    for key, value in values.items()
                    if key
                    not in {
                        active_mapping.source_species,
                        active_mapping.source_protein_ref,
                        active_mapping.target_species,
                        active_mapping.target_protein_ref,
                        active_mapping.source_gene_symbol,
                        active_mapping.target_gene_symbol,
                        active_mapping.evidence,
                    }
                    and value
                },
            )
        )

    return OrthologImportReport(
        source_path=str(path),
        total_rows=max(len(lines) - 1, 0),
        accepted_records=tuple(accepted_records),
        rejected_rows=tuple(rejected_rows),
        column_mapping=active_mapping,
        summary=OrthologImportSummary(
            accepted_record_count=len(accepted_records),
            rejected_row_count=len(rejected_rows),
            distinct_source_species_count=len(
                {record.source_species for record in accepted_records}
            ),
            distinct_target_species_count=len(
                {record.target_species for record in accepted_records}
            ),
            distinct_source_protein_ref_count=len(
                {record.source_protein_ref for record in accepted_records}
            ),
            distinct_target_protein_ref_count=len(
                {record.target_protein_ref for record in accepted_records}
            ),
        ),
        note=(
            "ortholog relationships preserve explicit source and target species identifiers with canonicalized protein references"
        ),
    )


def build_ortholog_mapping_report(
    source_entries: Iterable[ProteinReferenceEntry],
    ortholog_records: Iterable[OrthologRecord],
    *,
    source_species: str,
    target_species: str,
) -> OrthologMappingReport:
    """Map one protein-reference table onto a selected source-target species pair."""

    source_entry_items = tuple(source_entries)
    normalized_source_species = _normalize_species_identifier(source_species)
    normalized_target_species = _normalize_species_identifier(target_species)
    filtered_records = tuple(
        record
        for record in ortholog_records
        if _normalize_species_identifier(record.source_species)
        == normalized_source_species
        and _normalize_species_identifier(record.target_species)
        == normalized_target_species
    )

    source_to_targets: dict[str, tuple[OrthologRecord, ...]] = {}
    target_to_sources: dict[str, set[str]] = {}
    for record in filtered_records:
        source_to_targets.setdefault(record.source_protein_ref, ())
        source_to_targets[record.source_protein_ref] = source_to_targets[
            record.source_protein_ref
        ] + (record,)
        target_to_sources.setdefault(record.target_protein_ref, set()).add(
            record.source_protein_ref
        )

    mapped_entries: list[OrthologMappingEntry] = []
    unmapped_entries: list[UnmappedOrthologEntry] = []
    for entry in source_entry_items:
        relationships = tuple(
            sorted(
                source_to_targets.get(entry.protein_ref, ()),
                key=lambda record: record.target_protein_ref,
            )
        )
        if not relationships:
            unmapped_entries.append(
                UnmappedOrthologEntry(
                    row_number=entry.row_number,
                    source_row_id=entry.source_row_id,
                    input_protein_ref=entry.input_protein_ref,
                    source_protein_ref=entry.protein_ref,
                    source_species=source_species,
                    target_species=target_species,
                    input_metadata=entry.metadata,
                    reason=(
                        "no ortholog relationship for selected species pair "
                        f"{source_species} -> {target_species}"
                    ),
                )
            )
            continue
        source_match_count = len(relationships)
        for relationship in relationships:
            target_match_count = len(
                target_to_sources.get(relationship.target_protein_ref, set())
            )
            mapped_entries.append(
                OrthologMappingEntry(
                    row_number=entry.row_number,
                    source_row_id=entry.source_row_id,
                    input_protein_ref=entry.input_protein_ref,
                    source_protein_ref=entry.protein_ref,
                    source_species=source_species,
                    target_species=target_species,
                    target_protein_ref=relationship.target_protein_ref,
                    source_gene_symbol=relationship.source_gene_symbol,
                    target_gene_symbol=relationship.target_gene_symbol,
                    evidence=relationship.evidence,
                    mapping_cardinality=_classify_mapping_cardinality(
                        source_match_count=source_match_count,
                        target_match_count=target_match_count,
                    ),
                    source_match_count=source_match_count,
                    target_match_count=target_match_count,
                    input_metadata=entry.metadata,
                    ortholog_metadata=relationship.metadata,
                )
            )

    summary = OrthologMappingSummary(
        input_entry_count=len(source_entry_items),
        mapped_entry_count=len(mapped_entries),
        unmapped_entry_count=len(unmapped_entries),
        distinct_source_protein_ref_count=len(
            {entry.source_protein_ref for entry in mapped_entries}
        ),
        distinct_target_protein_ref_count=len(
            {entry.target_protein_ref for entry in mapped_entries}
        ),
        one_to_one_count=sum(
            1
            for entry in mapped_entries
            if entry.mapping_cardinality == OrthologMappingCardinality.ONE_TO_ONE
        ),
        one_to_many_count=sum(
            1
            for entry in mapped_entries
            if entry.mapping_cardinality == OrthologMappingCardinality.ONE_TO_MANY
        ),
        many_to_one_count=sum(
            1
            for entry in mapped_entries
            if entry.mapping_cardinality == OrthologMappingCardinality.MANY_TO_ONE
        ),
        many_to_many_count=sum(
            1
            for entry in mapped_entries
            if entry.mapping_cardinality == OrthologMappingCardinality.MANY_TO_MANY
        ),
        ambiguous_mapping_count=sum(
            1
            for entry in mapped_entries
            if entry.mapping_cardinality != OrthologMappingCardinality.ONE_TO_ONE
        ),
    )
    return OrthologMappingReport(
        source_species=source_species,
        target_species=target_species,
        mapped_entries=tuple(mapped_entries),
        unmapped_entries=tuple(unmapped_entries),
        summary=summary,
        note=(
            "ortholog mapping preserves every accepted edge for the selected source-target species pair and labels its ambiguity explicitly"
        ),
    )


def render_rejected_ortholog_tsv(report: OrthologImportReport) -> str:
    """Render rejected ortholog rows as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("row_number", "values", "reason"))
    for row in report.rejected_rows:
        writer.writerow((row.row_number, _metadata_json(row.values), row.reason))
    return buffer.getvalue()


def render_ortholog_mapping_summary_tsv(report: OrthologMappingReport) -> str:
    """Render the stable ortholog mapping summary ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "source_species",
            "target_species",
            "input_entry_count",
            "mapped_entry_count",
            "unmapped_entry_count",
            "distinct_source_protein_ref_count",
            "distinct_target_protein_ref_count",
            "one_to_one_count",
            "one_to_many_count",
            "many_to_one_count",
            "many_to_many_count",
            "ambiguous_mapping_count",
        )
    )
    writer.writerow(
        (
            report.source_species,
            report.target_species,
            report.summary.input_entry_count,
            report.summary.mapped_entry_count,
            report.summary.unmapped_entry_count,
            report.summary.distinct_source_protein_ref_count,
            report.summary.distinct_target_protein_ref_count,
            report.summary.one_to_one_count,
            report.summary.one_to_many_count,
            report.summary.many_to_one_count,
            report.summary.many_to_many_count,
            report.summary.ambiguous_mapping_count,
        )
    )
    return buffer.getvalue()


def render_mapped_ortholog_tsv(report: OrthologMappingReport) -> str:
    """Render mapped ortholog edges as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "row_number",
            "source_row_id",
            "input_protein_ref",
            "source_protein_ref",
            "source_species",
            "target_species",
            "target_protein_ref",
            "source_gene_symbol",
            "target_gene_symbol",
            "evidence",
            "mapping_cardinality",
            "source_match_count",
            "target_match_count",
            "input_metadata",
            "ortholog_metadata",
        )
    )
    for entry in report.mapped_entries:
        writer.writerow(
            (
                entry.row_number,
                entry.source_row_id or "",
                entry.input_protein_ref,
                entry.source_protein_ref,
                entry.source_species,
                entry.target_species,
                entry.target_protein_ref,
                entry.source_gene_symbol or "",
                entry.target_gene_symbol or "",
                entry.evidence or "",
                entry.mapping_cardinality.value,
                entry.source_match_count,
                entry.target_match_count,
                _metadata_json(entry.input_metadata),
                _metadata_json(entry.ortholog_metadata),
            )
        )
    return buffer.getvalue()


def render_unmapped_ortholog_tsv(report: OrthologMappingReport) -> str:
    """Render unmapped ortholog requests as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "row_number",
            "source_row_id",
            "input_protein_ref",
            "source_protein_ref",
            "source_species",
            "target_species",
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
                entry.source_protein_ref,
                entry.source_species,
                entry.target_species,
                _metadata_json(entry.input_metadata),
                entry.reason,
            )
        )
    return buffer.getvalue()


def _infer_delimiter(header_line: str) -> str:
    return "\t" if "\t" in header_line else ","


def _classify_mapping_cardinality(
    *,
    source_match_count: int,
    target_match_count: int,
) -> OrthologMappingCardinality:
    if source_match_count == 1 and target_match_count == 1:
        return OrthologMappingCardinality.ONE_TO_ONE
    if source_match_count > 1 and target_match_count > 1:
        return OrthologMappingCardinality.MANY_TO_MANY
    if source_match_count > 1:
        return OrthologMappingCardinality.ONE_TO_MANY
    return OrthologMappingCardinality.MANY_TO_ONE


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


def _metadata_json(values: dict[str, str]) -> str:
    return json.dumps(values, sort_keys=True)


def _normalize_species_identifier(value: str) -> str:
    return value.strip().casefold()


def _validate_required_columns(
    fieldnames: Iterable[str], required_columns: tuple[str, ...]
) -> None:
    available = {field.strip() for field in fieldnames}
    missing = [column for column in required_columns if column not in available]
    if missing:
        raise ValueError("missing required columns: " + ", ".join(sorted(missing)))


__all__ = [
    "OrthologColumnMapping",
    "OrthologImportReport",
    "OrthologImportSummary",
    "OrthologMappingCardinality",
    "OrthologMappingEntry",
    "OrthologMappingReport",
    "OrthologMappingSummary",
    "OrthologRecord",
    "RejectedOrthologRow",
    "UnmappedOrthologEntry",
    "build_ortholog_mapping_report",
    "parse_ortholog_table",
    "render_mapped_ortholog_tsv",
    "render_ortholog_mapping_summary_tsv",
    "render_rejected_ortholog_tsv",
    "render_unmapped_ortholog_tsv",
]
