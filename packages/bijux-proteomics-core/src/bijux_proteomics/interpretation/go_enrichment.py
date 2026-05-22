# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Gene Ontology enrichment surfaces for biological interpretation workflows."""

from __future__ import annotations

import csv
from enum import StrEnum
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.sequences import canonicalize_protein_reference
from bijux_proteomics_foundation import JsonModel


class GoAspect(StrEnum):
    """Stable Gene Ontology aspect labels."""

    BIOLOGICAL_PROCESS = "biological_process"
    CELLULAR_COMPONENT = "cellular_component"
    MOLECULAR_FUNCTION = "molecular_function"


class GoAnnotationColumnMapping(JsonModel):
    """Column mapping from a GO annotation table into owned fields."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    go_term_id: str = Field(..., min_length=1)
    go_term_name: str | None = None
    go_aspect: str | None = None
    evidence_code: str | None = None


class GoAnnotationRecord(JsonModel):
    """One normalized GO membership row."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    go_term_id: str = Field(..., min_length=1)
    go_term_name: str | None = None
    go_aspect: GoAspect | None = None
    evidence_code: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class RejectedGoAnnotationRow(JsonModel):
    """One rejected GO annotation row with a stable reason."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    values: dict[str, str] = Field(default_factory=dict)
    reason: str = Field(..., min_length=1)


class GoAnnotationImportSummary(JsonModel):
    """Stable summary over one GO annotation import pass."""

    model_config = ConfigDict(extra="forbid")

    accepted_record_count: int = Field(..., ge=0)
    rejected_row_count: int = Field(..., ge=0)
    distinct_protein_ref_count: int = Field(..., ge=0)
    distinct_go_term_count: int = Field(..., ge=0)
    aspect_counts: dict[str, int] = Field(default_factory=dict)


class GoAnnotationImportReport(JsonModel):
    """Governed GO annotation import report."""

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(..., min_length=1)
    total_rows: int = Field(..., ge=0)
    accepted_records: tuple[GoAnnotationRecord, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[RejectedGoAnnotationRow, ...] = Field(default_factory=tuple)
    column_mapping: GoAnnotationColumnMapping
    summary: GoAnnotationImportSummary
    note: str = Field(..., min_length=1)


def parse_go_annotation_table(
    path: Path,
    *,
    mapping: GoAnnotationColumnMapping | None = None,
) -> GoAnnotationImportReport:
    """Parse one GO annotation membership table into owned normalized records."""

    lines = _read_delimited_lines(path)
    active_mapping = mapping or GoAnnotationColumnMapping(
        protein_ref="protein_ref",
        go_term_id="go_term_id",
        go_term_name="go_term_name",
        go_aspect="go_aspect",
        evidence_code="evidence_code",
    )
    if not lines:
        return GoAnnotationImportReport(
            source_path=str(path),
            total_rows=0,
            accepted_records=(),
            rejected_rows=(
                RejectedGoAnnotationRow(
                    row_number=2,
                    reason="GO annotation table is empty",
                ),
            ),
            column_mapping=active_mapping,
            summary=GoAnnotationImportSummary(
                accepted_record_count=0,
                rejected_row_count=1,
                distinct_protein_ref_count=0,
                distinct_go_term_count=0,
                aspect_counts={},
            ),
            note="GO annotation table did not contain any readable rows",
        )

    reader = csv.DictReader(lines, delimiter=_infer_delimiter(lines[0]))
    if reader.fieldnames is None:
        raise ValueError("GO annotation table must include a header row")
    _validate_required_columns(
        reader.fieldnames,
        (active_mapping.protein_ref, active_mapping.go_term_id),
    )

    accepted_records: list[GoAnnotationRecord] = []
    rejected_rows: list[RejectedGoAnnotationRow] = []
    seen_memberships: set[tuple[str, str]] = set()
    for row_number, raw_row in enumerate(reader, start=2):
        values = _normalize_row(raw_row)
        protein_token = values.get(active_mapping.protein_ref, "").strip()
        go_term_id = values.get(active_mapping.go_term_id, "").strip()
        if not protein_token:
            rejected_rows.append(
                RejectedGoAnnotationRow(
                    row_number=row_number,
                    values=values,
                    reason="GO annotation row requires protein_ref",
                )
            )
            continue
        if not go_term_id:
            rejected_rows.append(
                RejectedGoAnnotationRow(
                    row_number=row_number,
                    values=values,
                    reason="GO annotation row requires go_term_id",
                )
            )
            continue
        protein_ref = canonicalize_protein_reference(protein_token)
        membership_key = (protein_ref, go_term_id)
        if membership_key in seen_memberships:
            rejected_rows.append(
                RejectedGoAnnotationRow(
                    row_number=row_number,
                    values=values,
                    reason=f"duplicate GO membership for {protein_ref} and {go_term_id}",
                )
            )
            continue
        seen_memberships.add(membership_key)
        accepted_records.append(
            GoAnnotationRecord(
                protein_ref=protein_ref,
                go_term_id=go_term_id,
                go_term_name=_optional_value(values, active_mapping.go_term_name),
                go_aspect=_parse_go_aspect(
                    _optional_value(values, active_mapping.go_aspect),
                    row_number=row_number,
                    raw_values=values,
                    rejected_rows=rejected_rows,
                ),
                evidence_code=_optional_value(values, active_mapping.evidence_code),
                metadata={
                    key: value
                    for key, value in values.items()
                    if key
                    not in {
                        active_mapping.protein_ref,
                        active_mapping.go_term_id,
                        active_mapping.go_term_name,
                        active_mapping.go_aspect,
                        active_mapping.evidence_code,
                    }
                    and value
                },
            )
        )

    aspect_counts: dict[str, int] = {}
    for record in accepted_records:
        if record.go_aspect is None:
            continue
        aspect_counts[record.go_aspect.value] = (
            aspect_counts.get(record.go_aspect.value, 0) + 1
        )
    return GoAnnotationImportReport(
        source_path=str(path),
        total_rows=max(len(lines) - 1, 0),
        accepted_records=tuple(accepted_records),
        rejected_rows=tuple(rejected_rows),
        column_mapping=active_mapping,
        summary=GoAnnotationImportSummary(
            accepted_record_count=len(accepted_records),
            rejected_row_count=len(rejected_rows),
            distinct_protein_ref_count=len(
                {record.protein_ref for record in accepted_records}
            ),
            distinct_go_term_count=len({record.go_term_id for record in accepted_records}),
            aspect_counts=dict(sorted(aspect_counts.items())),
        ),
        note="GO memberships were canonicalized onto the shared protein reference surface",
    )


def _parse_go_aspect(
    value: str | None,
    *,
    row_number: int,
    raw_values: dict[str, str],
    rejected_rows: list[RejectedGoAnnotationRow],
) -> GoAspect | None:
    if value is None:
        return None
    normalized = value.strip().lower().replace(" ", "_")
    alias_map = {
        "bp": GoAspect.BIOLOGICAL_PROCESS,
        "biological_process": GoAspect.BIOLOGICAL_PROCESS,
        "biological-process": GoAspect.BIOLOGICAL_PROCESS,
        "cc": GoAspect.CELLULAR_COMPONENT,
        "cellular_component": GoAspect.CELLULAR_COMPONENT,
        "cellular-component": GoAspect.CELLULAR_COMPONENT,
        "mf": GoAspect.MOLECULAR_FUNCTION,
        "molecular_function": GoAspect.MOLECULAR_FUNCTION,
        "molecular-function": GoAspect.MOLECULAR_FUNCTION,
    }
    aspect = alias_map.get(normalized)
    if aspect is None:
        rejected_rows.append(
            RejectedGoAnnotationRow(
                row_number=row_number,
                values=raw_values,
                reason=f"unsupported go_aspect {value!r}",
            )
        )
    return aspect


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
