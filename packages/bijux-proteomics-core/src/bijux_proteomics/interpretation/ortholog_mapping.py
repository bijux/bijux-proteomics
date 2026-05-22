# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Ortholog parsing and mapping surfaces for cross-species interpretation."""

from __future__ import annotations

from collections.abc import Iterable
import csv
import json
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

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


def render_rejected_ortholog_tsv(report: OrthologImportReport) -> str:
    """Render rejected ortholog rows as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("row_number", "values", "reason"))
    for row in report.rejected_rows:
        writer.writerow((row.row_number, _metadata_json(row.values), row.reason))
    return buffer.getvalue()


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


def _metadata_json(values: dict[str, str]) -> str:
    return json.dumps(values, sort_keys=True)


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
    "OrthologRecord",
    "RejectedOrthologRow",
    "parse_ortholog_table",
    "render_rejected_ortholog_tsv",
]
