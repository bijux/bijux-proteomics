# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Protein-set definition table import for owned scoring surfaces."""

from __future__ import annotations

from collections.abc import Iterable
import csv
from pathlib import Path

from bijux_proteomics.interpretation.protein_set_scoring.models import (
    ProteinSetColumnMapping,
    ProteinSetImportReport,
    ProteinSetImportSummary,
    ProteinSetRecord,
    RejectedProteinSetRow,
)
from bijux_proteomics.sequences import canonicalize_protein_reference


def parse_protein_set_table(
    path: Path,
    *,
    mapping: ProteinSetColumnMapping | None = None,
) -> ProteinSetImportReport:
    """Parse one protein-set definition table into owned normalized memberships."""

    lines = read_delimited_lines(path)
    active_mapping = mapping or ProteinSetColumnMapping(
        set_id="set_id",
        protein_ref="protein_ref",
        set_name="set_name",
        set_category="set_category",
        source_name="source_name",
        source_accession="source_accession",
    )
    if not lines:
        return ProteinSetImportReport(
            source_path=str(path),
            total_rows=0,
            accepted_records=(),
            rejected_rows=(
                RejectedProteinSetRow(
                    row_number=2,
                    reason="protein set table is empty",
                ),
            ),
            column_mapping=active_mapping,
            summary=ProteinSetImportSummary(
                accepted_record_count=0,
                rejected_row_count=1,
                distinct_set_count=0,
                distinct_member_count=0,
                source_counts={},
            ),
            note="protein set table did not contain any readable rows",
        )

    reader = csv.DictReader(lines, delimiter=infer_delimiter(lines[0]))
    if reader.fieldnames is None:
        raise ValueError("protein set table must include a header row")
    validate_required_columns(
        reader.fieldnames,
        (active_mapping.set_id, active_mapping.protein_ref),
    )

    accepted_records: list[ProteinSetRecord] = []
    rejected_rows: list[RejectedProteinSetRow] = []
    seen_memberships: set[tuple[str, str]] = set()
    for row_number, raw_row in enumerate(reader, start=2):
        values = normalize_row(raw_row)
        set_id = values.get(active_mapping.set_id, "").strip()
        protein_token = values.get(active_mapping.protein_ref, "").strip()
        if not set_id:
            rejected_rows.append(
                RejectedProteinSetRow(
                    row_number=row_number,
                    values=values,
                    reason="protein set row requires set_id",
                )
            )
            continue
        if not protein_token:
            rejected_rows.append(
                RejectedProteinSetRow(
                    row_number=row_number,
                    values=values,
                    reason="protein set row requires protein_ref",
                )
            )
            continue
        protein_ref = canonicalize_protein_reference(protein_token)
        membership_key = (set_id, protein_ref)
        if membership_key in seen_memberships:
            rejected_rows.append(
                RejectedProteinSetRow(
                    row_number=row_number,
                    values=values,
                    reason=(
                        f"duplicate protein set membership for {set_id} and protein {protein_ref}"
                    ),
                )
            )
            continue
        seen_memberships.add(membership_key)
        accepted_records.append(
            ProteinSetRecord(
                set_id=set_id,
                protein_ref=protein_ref,
                set_name=optional_value(values, active_mapping.set_name),
                set_category=optional_value(values, active_mapping.set_category),
                source_name=optional_value(values, active_mapping.source_name),
                source_accession=optional_value(
                    values, active_mapping.source_accession
                ),
                metadata={
                    key: value
                    for key, value in values.items()
                    if key
                    not in {
                        active_mapping.set_id,
                        active_mapping.protein_ref,
                        active_mapping.set_name,
                        active_mapping.set_category,
                        active_mapping.source_name,
                        active_mapping.source_accession,
                    }
                    and value
                },
            )
        )

    source_counts: dict[str, int] = {}
    for record in accepted_records:
        if record.source_name is not None:
            source_counts[record.source_name] = (
                source_counts.get(record.source_name, 0) + 1
            )

    return ProteinSetImportReport(
        source_path=str(path),
        total_rows=max(len(lines) - 1, 0),
        accepted_records=tuple(accepted_records),
        rejected_rows=tuple(rejected_rows),
        column_mapping=active_mapping,
        summary=ProteinSetImportSummary(
            accepted_record_count=len(accepted_records),
            rejected_row_count=len(rejected_rows),
            distinct_set_count=len({record.set_id for record in accepted_records}),
            distinct_member_count=len(
                {record.protein_ref for record in accepted_records}
            ),
            source_counts=dict(sorted(source_counts.items())),
        ),
        note=(
            "protein set definitions preserve stable set identifiers, provenance, and explicit rejected memberships"
        ),
    )


def infer_delimiter(header_line: str) -> str:
    """Infer whether one protein-set table uses TSV or CSV delimiter conventions."""

    return "\t" if "\t" in header_line else ","


def normalize_row(raw_row: dict[str | None, str | None]) -> dict[str, str]:
    """Normalize whitespace and nullability across one imported membership row."""

    return {
        (key or "").strip(): (value or "").strip()
        for key, value in raw_row.items()
        if key is not None
    }


def optional_value(row: dict[str, str], field_name: str | None) -> str | None:
    """Return one optional mapped field if it carries a non-empty value."""

    if field_name is None:
        return None
    value = row.get(field_name, "").strip()
    return value or None


def read_delimited_lines(path: Path) -> list[str]:
    """Read one protein-set definition table into raw text lines."""

    payload = path.read_text(encoding="utf-8")
    return payload.splitlines()


def validate_required_columns(
    fieldnames: Iterable[str], required_columns: tuple[str, ...]
) -> None:
    """Validate that one imported table exposes the required membership columns."""

    available = {field.strip() for field in fieldnames}
    missing = [column for column in required_columns if column not in available]
    if missing:
        raise ValueError("missing required columns: " + ", ".join(sorted(missing)))


__all__ = [
    "infer_delimiter",
    "normalize_row",
    "optional_value",
    "parse_protein_set_table",
    "read_delimited_lines",
    "validate_required_columns",
]
