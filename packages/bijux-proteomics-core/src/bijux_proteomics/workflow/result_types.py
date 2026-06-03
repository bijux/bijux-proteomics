# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Shared typed result objects for major workflow-owned outputs."""

from __future__ import annotations

from collections.abc import Iterable
import csv
from enum import StrEnum
from io import StringIO
from typing import Any, Protocol

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics.domain.reason_codes import (
    ReasonCodeCategory,
    require_registered_reason_code,
)
from bijux_proteomics_foundation import JsonModel


class ResultWarningSeverity(StrEnum):
    """Stable severities carried by standardized workflow warnings."""

    WARNING = "warning"
    ERROR = "error"


class ResultWarningEntry(JsonModel):
    """One stable warning emitted by a standardized result object."""

    model_config = ConfigDict(extra="forbid")

    warning_id: str = Field(..., min_length=1)
    warning_code: str = Field(..., min_length=1)
    source_surface: str = Field(..., min_length=1)
    severity: ResultWarningSeverity = ResultWarningSeverity.WARNING
    message: str = Field(..., min_length=1)
    related_artifact: str | None = None
    entity_id: str | None = None

    @field_validator("warning_code")
    @classmethod
    def _validate_warning_code(cls, value: str) -> str:
        return require_registered_reason_code(
            value,
            ReasonCodeCategory.RESULT_WARNING,
        )


class RejectedEvidenceEntry(JsonModel):
    """One stable rejected-evidence row exposed by a standardized result object."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(..., min_length=1)
    source_surface: str = Field(..., min_length=1)
    reason_code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    related_artifact: str | None = None
    source_file: str | None = None
    row_number: int | None = Field(default=None, ge=1)
    entity_type: str | None = None
    entity_id: str | None = None

    @field_validator("reason_code")
    @classmethod
    def _validate_reason_code(cls, value: str) -> str:
        return require_registered_reason_code(
            value,
            ReasonCodeCategory.VALIDATION_ISSUE,
            ReasonCodeCategory.REJECTED_EVIDENCE,
            ReasonCodeCategory.RESULT_WARNING,
        )


class _StandardResult(JsonModel):
    """Common typed result surface shared by major workflow outputs."""

    model_config = ConfigDict(extra="forbid")

    artifacts: dict[str, str] = Field(default_factory=dict)
    warnings: tuple[ResultWarningEntry, ...] = Field(default_factory=tuple)
    rejected_evidence: tuple[RejectedEvidenceEntry, ...] = Field(default_factory=tuple)


class ImportResult(_StandardResult):
    """Typed import result with stable artifacts, warnings, and rejections."""


class QCResult(_StandardResult):
    """Typed QC result with stable artifacts, warnings, and rejections."""


class MatrixResult(_StandardResult):
    """Typed matrix result with stable artifacts, warnings, and rejections."""


class StatisticsResult(_StandardResult):
    """Typed statistical result with stable artifacts, warnings, and rejections."""


class BiologyResult(_StandardResult):
    """Typed biological result with stable artifacts, warnings, and rejections."""


class WorkflowResult(_StandardResult):
    """Typed workflow result with stable artifacts, warnings, and rejections."""


class _RejectedEvidenceTableRow(Protocol):
    @property
    def source_file(self) -> str | None: ...

    @property
    def row_number(self) -> int | None: ...

    @property
    def entity_type(self) -> str | None: ...

    @property
    def entity_id(self) -> str | None: ...

    @property
    def reason_code(self) -> str: ...

    @property
    def detail(self) -> str: ...


def artifact_name_map(artifacts: JsonModel) -> dict[str, str]:
    """Convert one artifact-path model into a stable string-keyed artifact map."""

    return {
        key: value
        for key, value in artifacts.model_dump(mode="python", exclude_none=True).items()
        if isinstance(value, str) and value
    }


def build_result_warning(
    *,
    warning_id: str,
    warning_code: str,
    source_surface: str,
    message: str,
    related_artifact: str | None = None,
    entity_id: str | None = None,
    severity: ResultWarningSeverity = ResultWarningSeverity.WARNING,
) -> ResultWarningEntry:
    """Build one standardized result warning entry."""

    return ResultWarningEntry(
        warning_id=warning_id,
        warning_code=warning_code,
        source_surface=source_surface,
        severity=severity,
        message=message,
        related_artifact=related_artifact,
        entity_id=entity_id,
    )


def build_rejected_evidence_entry(
    *,
    evidence_id: str,
    source_surface: str,
    reason_code: str,
    message: str,
    related_artifact: str | None = None,
    source_file: str | None = None,
    row_number: int | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
) -> RejectedEvidenceEntry:
    """Build one standardized rejected-evidence entry."""

    return RejectedEvidenceEntry(
        evidence_id=evidence_id,
        source_surface=source_surface,
        reason_code=reason_code,
        message=message,
        related_artifact=related_artifact,
        source_file=source_file,
        row_number=row_number,
        entity_type=entity_type,
        entity_id=entity_id,
    )


def build_rejected_evidence_entries_from_issue_rows(
    rows: Iterable[object],
    *,
    source_surface: str,
    related_artifact: str | None = None,
    entity_prefix: str = "row",
    source_file: str | None = None,
    entity_type: str | None = None,
) -> tuple[RejectedEvidenceEntry, ...]:
    """Convert issue-bearing rejected rows into standardized rejected-evidence entries."""

    entries: list[RejectedEvidenceEntry] = []
    for row in rows:
        row_number = _coerce_row_number(row)
        entity_id = _resolve_row_entity_id(row, entity_prefix=entity_prefix)
        issues = tuple(getattr(row, "issues", ()))
        if not issues:
            entries.append(
                build_rejected_evidence_entry(
                    evidence_id=f"{source_surface}:{entity_id}",
                    source_surface=source_surface,
                    reason_code="rejected_row",
                    message="rejected workflow evidence row",
                    related_artifact=related_artifact,
                    source_file=source_file,
                    row_number=row_number,
                    entity_type=entity_type,
                    entity_id=entity_id,
                )
            )
            continue
        for issue in issues:
            reason_code = str(getattr(issue, "code", "")).strip() or "rejected_row"
            message = (
                str(getattr(issue, "message", "")).strip()
                or "rejected workflow evidence row"
            )
            entries.append(
                build_rejected_evidence_entry(
                    evidence_id=f"{source_surface}:{entity_id}:{reason_code}:{row_number}",
                    source_surface=source_surface,
                    reason_code=reason_code,
                    message=message,
                    related_artifact=related_artifact,
                    source_file=source_file,
                    row_number=row_number,
                    entity_type=entity_type,
                    entity_id=entity_id,
                )
            )
    return tuple(entries)


def build_rejected_evidence_entries_from_reason_rows(
    rows: Iterable[object],
    *,
    source_surface: str,
    reason_field: str,
    message_field: str,
    entity_field: str,
    related_artifact: str | None = None,
    source_file: str | None = None,
    row_number_field: str | None = None,
    entity_type: str | None = None,
) -> tuple[RejectedEvidenceEntry, ...]:
    """Convert reason-bearing rows into standardized rejected-evidence entries."""

    return tuple(
        build_rejected_evidence_entry(
            evidence_id=f"{source_surface}:{getattr(row, entity_field)}",
            source_surface=source_surface,
            reason_code=str(getattr(row, reason_field)),
            message=str(getattr(row, message_field)),
            related_artifact=related_artifact,
            source_file=source_file,
            row_number=(
                None
                if row_number_field is None
                else int(getattr(row, row_number_field))
            ),
            entity_type=entity_type,
            entity_id=str(getattr(row, entity_field)),
        )
        for row in rows
    )


def build_rejected_evidence_entries_from_table_rows(
    rows: Iterable[_RejectedEvidenceTableRow],
    *,
    source_surface: str,
    related_artifact: str | None = None,
) -> tuple[RejectedEvidenceEntry, ...]:
    """Convert rejected-evidence table rows into standardized result entries."""

    return tuple(
        build_rejected_evidence_entry(
            evidence_id=(
                f"{source_surface}:{row.entity_type}:{row.entity_id}:{row.row_number}:{row.reason_code}"
            ),
            source_surface=source_surface,
            reason_code=row.reason_code,
            message=row.detail,
            related_artifact=related_artifact,
            source_file=row.source_file,
            row_number=row.row_number,
            entity_type=row.entity_type,
            entity_id=row.entity_id,
        )
        for row in rows
    )


def render_result_rejected_evidence_tsv(
    rows: tuple[RejectedEvidenceEntry, ...],
) -> str:
    """Render standardized workflow rejected evidence as one stable TSV surface."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "rejected_evidence_id",
            "source_surface",
            "source_file",
            "row_number",
            "entity_type",
            "entity_id",
            "reason_code",
            "detail",
            "related_artifact",
        )
    )
    ordered_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                row.source_surface,
                "" if row.source_file is None else row.source_file,
                -1 if row.row_number is None else row.row_number,
                "" if row.entity_type is None else row.entity_type,
                "" if row.entity_id is None else row.entity_id,
                row.reason_code,
                row.evidence_id,
            ),
        )
    )
    for row in ordered_rows:
        writer.writerow(
            (
                row.evidence_id,
                row.source_surface,
                "" if row.source_file is None else row.source_file,
                "" if row.row_number is None else row.row_number,
                "" if row.entity_type is None else row.entity_type,
                "" if row.entity_id is None else row.entity_id,
                row.reason_code,
                row.message,
                "" if row.related_artifact is None else row.related_artifact,
            )
        )
    return handle.getvalue()


def _resolve_row_entity_id(row: object, *, entity_prefix: str) -> str:
    if hasattr(row, "entity_id") and str(row.entity_id).strip():
        return str(row.entity_id).strip()
    raw_fields = dict(_coerce_raw_fields(getattr(row, "raw_fields", {})))
    for key in (
        "candidate_id",
        "source_row_id",
        "protein_ref",
        "protein_id",
        "peptide_sequence",
        "Sequence",
        "Modified.Sequence",
    ):
        value = raw_fields.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return f"{entity_prefix}:{_coerce_row_number(row)}"


def _coerce_row_number(row: object) -> int:
    raw_row_number = getattr(row, "row_number", None)
    if raw_row_number is None:
        raise ValueError("rejected evidence rows must declare row_number")
    return int(raw_row_number)


def _coerce_raw_fields(raw_fields: object) -> dict[str, Any]:
    return raw_fields if isinstance(raw_fields, dict) else {}


__all__ = [
    "BiologyResult",
    "ImportResult",
    "MatrixResult",
    "QCResult",
    "RejectedEvidenceEntry",
    "ResultWarningEntry",
    "ResultWarningSeverity",
    "StatisticsResult",
    "WorkflowResult",
    "artifact_name_map",
    "build_rejected_evidence_entry",
    "build_rejected_evidence_entries_from_issue_rows",
    "build_rejected_evidence_entries_from_reason_rows",
    "build_rejected_evidence_entries_from_table_rows",
    "render_result_rejected_evidence_tsv",
    "build_result_warning",
]
