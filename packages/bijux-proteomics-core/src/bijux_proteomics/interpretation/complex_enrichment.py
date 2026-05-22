# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Protein complex enrichment surfaces for biological interpretation workflows."""

from __future__ import annotations

import csv
from enum import StrEnum
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.sequences import canonicalize_protein_reference
from bijux_proteomics_foundation import JsonModel


class ComplexMemberKind(StrEnum):
    """Stable comparable member kinds for protein complex enrichment."""

    PROTEIN = "protein"
    GENE = "gene"


class ComplexMembershipColumnMapping(JsonModel):
    """Column mapping from a complex membership table into owned fields."""

    model_config = ConfigDict(extra="forbid")

    complex_id: str = Field(..., min_length=1)
    complex_name: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    protein_ref: str | None = None
    gene_symbol: str | None = None


class ComplexMembershipRecord(JsonModel):
    """One normalized protein complex membership row."""

    model_config = ConfigDict(extra="forbid")

    complex_id: str = Field(..., min_length=1)
    complex_name: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    member_kind: ComplexMemberKind
    member_id: str = Field(..., min_length=1)
    metadata: dict[str, str] = Field(default_factory=dict)


class RejectedComplexMembershipRow(JsonModel):
    """One rejected complex membership row with a stable reason."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    values: dict[str, str] = Field(default_factory=dict)
    reason: str = Field(..., min_length=1)


class ComplexMembershipImportSummary(JsonModel):
    """Stable summary over one complex membership import pass."""

    model_config = ConfigDict(extra="forbid")

    accepted_record_count: int = Field(..., ge=0)
    rejected_row_count: int = Field(..., ge=0)
    distinct_complex_count: int = Field(..., ge=0)
    distinct_member_count: int = Field(..., ge=0)
    member_kind_counts: dict[str, int] = Field(default_factory=dict)
    source_counts: dict[str, int] = Field(default_factory=dict)


class ComplexMembershipImportReport(JsonModel):
    """Governed protein complex membership import report."""

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(..., min_length=1)
    total_rows: int = Field(..., ge=0)
    accepted_records: tuple[ComplexMembershipRecord, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[RejectedComplexMembershipRow, ...] = Field(default_factory=tuple)
    column_mapping: ComplexMembershipColumnMapping
    summary: ComplexMembershipImportSummary
    note: str = Field(..., min_length=1)


def parse_complex_membership_table(
    path: Path,
    *,
    mapping: ComplexMembershipColumnMapping | None = None,
) -> ComplexMembershipImportReport:
    """Parse one protein complex membership table with protein or gene members."""

    lines = _read_delimited_lines(path)
    active_mapping = mapping or ComplexMembershipColumnMapping(
        complex_id="complex_id",
        complex_name="complex_name",
        source_name="source_name",
        source_accession="source_accession",
        protein_ref="protein_ref",
        gene_symbol="gene_symbol",
    )
    if not lines:
        return ComplexMembershipImportReport(
            source_path=str(path),
            total_rows=0,
            accepted_records=(),
            rejected_rows=(
                RejectedComplexMembershipRow(
                    row_number=2,
                    reason="complex membership table is empty",
                ),
            ),
            column_mapping=active_mapping,
            summary=ComplexMembershipImportSummary(
                accepted_record_count=0,
                rejected_row_count=1,
                distinct_complex_count=0,
                distinct_member_count=0,
                member_kind_counts={},
                source_counts={},
            ),
            note="complex membership table did not contain any readable rows",
        )

    reader = csv.DictReader(lines, delimiter=_infer_delimiter(lines[0]))
    if reader.fieldnames is None:
        raise ValueError("complex membership table must include a header row")
    _validate_required_columns(reader.fieldnames, (active_mapping.complex_id,))

    accepted_records: list[ComplexMembershipRecord] = []
    rejected_rows: list[RejectedComplexMembershipRow] = []
    seen_memberships: set[tuple[str, str, str]] = set()
    for row_number, raw_row in enumerate(reader, start=2):
        values = _normalize_row(raw_row)
        complex_id = values.get(active_mapping.complex_id, "").strip()
        if not complex_id:
            rejected_rows.append(
                RejectedComplexMembershipRow(
                    row_number=row_number,
                    values=values,
                    reason="complex membership row requires complex_id",
                )
            )
            continue
        protein_token = (
            None
            if active_mapping.protein_ref is None
            else values.get(active_mapping.protein_ref, "").strip() or None
        )
        gene_symbol = (
            None
            if active_mapping.gene_symbol is None
            else values.get(active_mapping.gene_symbol, "").strip() or None
        )
        if protein_token and gene_symbol:
            rejected_rows.append(
                RejectedComplexMembershipRow(
                    row_number=row_number,
                    values=values,
                    reason="complex membership row must choose protein_ref or gene_symbol, not both",
                )
            )
            continue
        if protein_token is None and gene_symbol is None:
            rejected_rows.append(
                RejectedComplexMembershipRow(
                    row_number=row_number,
                    values=values,
                    reason="complex membership row requires protein_ref or gene_symbol",
                )
            )
            continue
        if protein_token is not None:
            member_kind = ComplexMemberKind.PROTEIN
            member_id = canonicalize_protein_reference(protein_token)
        else:
            member_kind = ComplexMemberKind.GENE
            member_id = str(gene_symbol)
        membership_key = (complex_id, member_kind.value, member_id)
        if membership_key in seen_memberships:
            rejected_rows.append(
                RejectedComplexMembershipRow(
                    row_number=row_number,
                    values=values,
                    reason=(
                        f"duplicate complex membership for {complex_id} and "
                        f"{member_kind.value} member {member_id}"
                    ),
                )
            )
            continue
        seen_memberships.add(membership_key)
        accepted_records.append(
            ComplexMembershipRecord(
                complex_id=complex_id,
                complex_name=_optional_value(values, active_mapping.complex_name),
                source_name=_optional_value(values, active_mapping.source_name),
                source_accession=_optional_value(values, active_mapping.source_accession),
                member_kind=member_kind,
                member_id=member_id,
                metadata={
                    key: value
                    for key, value in values.items()
                    if key
                    not in {
                        active_mapping.complex_id,
                        active_mapping.complex_name,
                        active_mapping.source_name,
                        active_mapping.source_accession,
                        active_mapping.protein_ref,
                        active_mapping.gene_symbol,
                    }
                    and value
                },
            )
        )

    member_kind_counts: dict[str, int] = {}
    source_counts: dict[str, int] = {}
    for record in accepted_records:
        member_kind_counts[record.member_kind.value] = (
            member_kind_counts.get(record.member_kind.value, 0) + 1
        )
        if record.source_name is not None:
            source_counts[record.source_name] = source_counts.get(record.source_name, 0) + 1

    return ComplexMembershipImportReport(
        source_path=str(path),
        total_rows=max(len(lines) - 1, 0),
        accepted_records=tuple(accepted_records),
        rejected_rows=tuple(rejected_rows),
        column_mapping=active_mapping,
        summary=ComplexMembershipImportSummary(
            accepted_record_count=len(accepted_records),
            rejected_row_count=len(rejected_rows),
            distinct_complex_count=len({record.complex_id for record in accepted_records}),
            distinct_member_count=len(
                {(record.member_kind.value, record.member_id) for record in accepted_records}
            ),
            member_kind_counts=dict(sorted(member_kind_counts.items())),
            source_counts=dict(sorted(source_counts.items())),
        ),
        note="complex memberships preserve CORUM or custom provenance over protein or gene members",
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
        raise ValueError("missing required columns: " + ", ".join(sorted(missing)))
