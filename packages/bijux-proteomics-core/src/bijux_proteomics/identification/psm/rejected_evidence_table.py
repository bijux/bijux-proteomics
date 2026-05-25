# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Shared rejected-evidence tables over importer and normalization rejections."""

from __future__ import annotations

import csv
import io
from typing import Protocol

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics.domain.reason_codes import (
    ReasonCodeCategory,
    require_registered_reason_code,
)
from bijux_proteomics.identification.contracts import RejectedPsmRow
from bijux_proteomics._scientific_tables import ScientificTableRejectedRow
from bijux_proteomics_foundation import JsonModel


class _IssueLike(Protocol):
    code: str
    message: str


class RejectedEvidenceTableEntry(JsonModel):
    """One stable rejected-evidence row with explicit reason code."""

    model_config = ConfigDict(extra="forbid")

    source_file: str = Field(..., min_length=1)
    row_number: int = Field(..., ge=1)
    entity_type: str = Field(..., min_length=1)
    entity_id: str = Field(..., min_length=1)
    reason_code: str = Field(..., min_length=1)
    detail: str = Field(..., min_length=1)

    @field_validator("reason_code")
    @classmethod
    def _validate_reason_code(cls, value: str) -> str:
        return require_registered_reason_code(
            value,
            ReasonCodeCategory.VALIDATION_ISSUE,
            ReasonCodeCategory.REJECTED_EVIDENCE,
            ReasonCodeCategory.RESULT_WARNING,
        )


def build_rejected_evidence_rows_from_psm_rows(
    rows: tuple[RejectedPsmRow, ...],
    *,
    source_file: str,
    entity_type: str = "psm",
    entity_id_columns: tuple[str, ...] = (),
) -> tuple[RejectedEvidenceTableEntry, ...]:
    """Convert rejected generic PSM rows into one stable rejected-evidence table."""

    return _build_rejected_evidence_rows(
        rows=rows,
        source_file=source_file,
        entity_type=entity_type,
        entity_id_columns=entity_id_columns,
        default_entity_id_prefix=entity_type,
        raw_values_attrs=("raw_fields",),
        default_reason_code="rejected_psm_row",
    )


def build_rejected_evidence_rows_from_scientific_rows(
    rows: tuple[ScientificTableRejectedRow, ...],
    *,
    source_file: str,
    entity_type: str,
    entity_id_columns: tuple[str, ...] = (),
) -> tuple[RejectedEvidenceTableEntry, ...]:
    """Convert rejected schema-backed table rows into one stable rejected-evidence table."""

    return _build_rejected_evidence_rows(
        rows=rows,
        source_file=source_file,
        entity_type=entity_type,
        entity_id_columns=entity_id_columns,
        default_entity_id_prefix=entity_type,
        raw_values_attrs=("raw_values", "raw_fields"),
        default_reason_code="rejected_scientific_row",
    )


def render_rejected_evidence_tsv(rows: tuple[RejectedEvidenceTableEntry, ...]) -> str:
    """Render one stable rejected-evidence table as TSV."""

    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "source_file",
            "row_number",
            "entity_type",
            "entity_id",
            "reason_code",
            "detail",
        )
    )
    ordered_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                row.source_file,
                row.row_number,
                row.entity_type,
                row.entity_id,
                row.reason_code,
                row.detail,
            ),
        )
    )
    for row in ordered_rows:
        writer.writerow(
            (
                row.source_file,
                row.row_number,
                row.entity_type,
                row.entity_id,
                row.reason_code,
                row.detail,
            )
        )
    return buffer.getvalue()


def _build_rejected_evidence_rows(
    *,
    rows: tuple[object, ...],
    source_file: str,
    entity_type: str,
    entity_id_columns: tuple[str, ...],
    default_entity_id_prefix: str,
    raw_values_attrs: tuple[str, ...],
    default_reason_code: str,
) -> tuple[RejectedEvidenceTableEntry, ...]:
    entries: list[RejectedEvidenceTableEntry] = []
    for row in rows:
        row_number = int(getattr(row, "row_number"))
        raw_values = _read_raw_values(row, raw_values_attrs=raw_values_attrs)
        entity_id = _resolve_entity_id(
            raw_values=raw_values,
            entity_id_columns=entity_id_columns,
            default_entity_id_prefix=default_entity_id_prefix,
            row_number=row_number,
        )
        issues = tuple(getattr(row, "issues"))
        if issues:
            for issue in issues:
                reason_code = str(issue.code).strip() or default_reason_code
                detail = str(issue.message).strip() or "rejected evidence row"
                entries.append(
                    RejectedEvidenceTableEntry(
                        source_file=source_file,
                        row_number=row_number,
                        entity_type=entity_type,
                        entity_id=entity_id,
                        reason_code=reason_code,
                        detail=detail,
                    )
                )
            continue
        entries.append(
            RejectedEvidenceTableEntry(
                source_file=source_file,
                row_number=row_number,
                entity_type=entity_type,
                entity_id=entity_id,
                reason_code=default_reason_code,
                detail="rejected evidence row",
            )
        )
    return tuple(entries)


def _resolve_entity_id(
    *,
    raw_values: dict[str, str],
    entity_id_columns: tuple[str, ...],
    default_entity_id_prefix: str,
    row_number: int,
) -> str:
    preferred_columns = entity_id_columns or (
        "Precursor.Id",
        "precursor_id",
        "spectrum_id",
        "scan_ref",
        "Spectrum",
        "feature_id",
        "Sequence",
        "sequence",
        "sequence_text",
        "peptide",
        "Modified.Sequence",
        "modified_sequence",
        "Protein.Group",
        "protein_group_id",
        "FeatureID",
        "feature_id",
    )
    for column in preferred_columns:
        value = raw_values.get(column)
        if value is not None and str(value).strip():
            return str(value).strip()
    return f"{default_entity_id_prefix}-row-{row_number}"


def _read_raw_values(
    row: object,
    *,
    raw_values_attrs: tuple[str, ...],
) -> dict[str, str]:
    for attribute_name in raw_values_attrs:
        if hasattr(row, attribute_name):
            return dict(getattr(row, attribute_name))
    raise AttributeError(
        f"rejected evidence row does not expose any raw value attribute from {raw_values_attrs}"
    )


__all__ = [
    "RejectedEvidenceTableEntry",
    "build_rejected_evidence_rows_from_psm_rows",
    "build_rejected_evidence_rows_from_scientific_rows",
    "render_rejected_evidence_tsv",
]
