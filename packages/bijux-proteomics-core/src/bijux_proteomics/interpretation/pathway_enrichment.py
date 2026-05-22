# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Pathway enrichment surfaces for biological interpretation workflows."""

from __future__ import annotations

import csv
from enum import StrEnum
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.sequences import canonicalize_protein_reference
from bijux_proteomics_foundation import JsonModel


class PathwayMemberKind(StrEnum):
    """Stable comparable member kinds for pathway-set enrichment."""

    PROTEIN = "protein"
    GENE = "gene"


class PathwayMembershipColumnMapping(JsonModel):
    """Column mapping from a pathway membership table into owned fields."""

    model_config = ConfigDict(extra="forbid")

    pathway_id: str = Field(..., min_length=1)
    pathway_name: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    protein_ref: str | None = None
    gene_symbol: str | None = None


class PathwayMembershipRecord(JsonModel):
    """One normalized pathway membership row."""

    model_config = ConfigDict(extra="forbid")

    pathway_id: str = Field(..., min_length=1)
    pathway_name: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    member_kind: PathwayMemberKind
    member_id: str = Field(..., min_length=1)
    metadata: dict[str, str] = Field(default_factory=dict)


class RejectedPathwayMembershipRow(JsonModel):
    """One rejected pathway membership row with a stable reason."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    values: dict[str, str] = Field(default_factory=dict)
    reason: str = Field(..., min_length=1)


class PathwayMembershipImportSummary(JsonModel):
    """Stable summary over one pathway membership import pass."""

    model_config = ConfigDict(extra="forbid")

    accepted_record_count: int = Field(..., ge=0)
    rejected_row_count: int = Field(..., ge=0)
    distinct_pathway_count: int = Field(..., ge=0)
    distinct_member_count: int = Field(..., ge=0)
    member_kind_counts: dict[str, int] = Field(default_factory=dict)
    source_counts: dict[str, int] = Field(default_factory=dict)


class PathwayMembershipImportReport(JsonModel):
    """Governed pathway membership import report."""

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(..., min_length=1)
    total_rows: int = Field(..., ge=0)
    accepted_records: tuple[PathwayMembershipRecord, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[RejectedPathwayMembershipRow, ...] = Field(default_factory=tuple)
    column_mapping: PathwayMembershipColumnMapping
    summary: PathwayMembershipImportSummary
    note: str = Field(..., min_length=1)


def parse_pathway_membership_table(
    path: Path,
    *,
    mapping: PathwayMembershipColumnMapping | None = None,
) -> PathwayMembershipImportReport:
    """Parse one pathway membership table with protein or gene members."""

    lines = _read_delimited_lines(path)
    active_mapping = mapping or PathwayMembershipColumnMapping(
        pathway_id="pathway_id",
        pathway_name="pathway_name",
        source_name="source_name",
        source_accession="source_accession",
        protein_ref="protein_ref",
        gene_symbol="gene_symbol",
    )
    if not lines:
        return PathwayMembershipImportReport(
            source_path=str(path),
            total_rows=0,
            accepted_records=(),
            rejected_rows=(
                RejectedPathwayMembershipRow(
                    row_number=2,
                    reason="pathway membership table is empty",
                ),
            ),
            column_mapping=active_mapping,
            summary=PathwayMembershipImportSummary(
                accepted_record_count=0,
                rejected_row_count=1,
                distinct_pathway_count=0,
                distinct_member_count=0,
                member_kind_counts={},
                source_counts={},
            ),
            note="pathway membership table did not contain any readable rows",
        )

    reader = csv.DictReader(lines, delimiter=_infer_delimiter(lines[0]))
    if reader.fieldnames is None:
        raise ValueError("pathway membership table must include a header row")
    _validate_required_columns(reader.fieldnames, (active_mapping.pathway_id,))

    accepted_records: list[PathwayMembershipRecord] = []
    rejected_rows: list[RejectedPathwayMembershipRow] = []
    seen_memberships: set[tuple[str, str, str]] = set()
    for row_number, raw_row in enumerate(reader, start=2):
        values = _normalize_row(raw_row)
        pathway_id = values.get(active_mapping.pathway_id, "").strip()
        if not pathway_id:
            rejected_rows.append(
                RejectedPathwayMembershipRow(
                    row_number=row_number,
                    values=values,
                    reason="pathway membership row requires pathway_id",
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
                RejectedPathwayMembershipRow(
                    row_number=row_number,
                    values=values,
                    reason="pathway membership row must choose protein_ref or gene_symbol, not both",
                )
            )
            continue
        if protein_token is None and gene_symbol is None:
            rejected_rows.append(
                RejectedPathwayMembershipRow(
                    row_number=row_number,
                    values=values,
                    reason="pathway membership row requires protein_ref or gene_symbol",
                )
            )
            continue
        if protein_token is not None:
            member_kind = PathwayMemberKind.PROTEIN
            member_id = canonicalize_protein_reference(protein_token)
        else:
            member_kind = PathwayMemberKind.GENE
            member_id = str(gene_symbol)
        membership_key = (pathway_id, member_kind.value, member_id)
        if membership_key in seen_memberships:
            rejected_rows.append(
                RejectedPathwayMembershipRow(
                    row_number=row_number,
                    values=values,
                    reason=(
                        f"duplicate pathway membership for {pathway_id} and "
                        f"{member_kind.value} member {member_id}"
                    ),
                )
            )
            continue
        seen_memberships.add(membership_key)
        accepted_records.append(
            PathwayMembershipRecord(
                pathway_id=pathway_id,
                pathway_name=_optional_value(values, active_mapping.pathway_name),
                source_name=_optional_value(values, active_mapping.source_name),
                source_accession=_optional_value(values, active_mapping.source_accession),
                member_kind=member_kind,
                member_id=member_id,
                metadata={
                    key: value
                    for key, value in values.items()
                    if key
                    not in {
                        active_mapping.pathway_id,
                        active_mapping.pathway_name,
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

    return PathwayMembershipImportReport(
        source_path=str(path),
        total_rows=max(len(lines) - 1, 0),
        accepted_records=tuple(accepted_records),
        rejected_rows=tuple(rejected_rows),
        column_mapping=active_mapping,
        summary=PathwayMembershipImportSummary(
            accepted_record_count=len(accepted_records),
            rejected_row_count=len(rejected_rows),
            distinct_pathway_count=len({record.pathway_id for record in accepted_records}),
            distinct_member_count=len(
                {(record.member_kind.value, record.member_id) for record in accepted_records}
            ),
            member_kind_counts=dict(sorted(member_kind_counts.items())),
            source_counts=dict(sorted(source_counts.items())),
        ),
        note="pathway memberships preserve KEGG, Reactome, or user-supplied provenance over protein or gene members",
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
