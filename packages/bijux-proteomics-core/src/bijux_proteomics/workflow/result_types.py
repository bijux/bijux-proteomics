# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Shared typed result objects for major workflow-owned outputs."""

from __future__ import annotations

from enum import StrEnum
from typing import Iterable

from pydantic import ConfigDict, Field

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


class RejectedEvidenceEntry(JsonModel):
    """One stable rejected-evidence row exposed by a standardized result object."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(..., min_length=1)
    source_surface: str = Field(..., min_length=1)
    reason_code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    related_artifact: str | None = None
    entity_id: str | None = None


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
    entity_id: str | None = None,
) -> RejectedEvidenceEntry:
    """Build one standardized rejected-evidence entry."""

    return RejectedEvidenceEntry(
        evidence_id=evidence_id,
        source_surface=source_surface,
        reason_code=reason_code,
        message=message,
        related_artifact=related_artifact,
        entity_id=entity_id,
    )


def build_rejected_evidence_entries_from_issue_rows(
    rows: Iterable[object],
    *,
    source_surface: str,
    related_artifact: str | None = None,
    entity_prefix: str = "row",
) -> tuple[RejectedEvidenceEntry, ...]:
    """Convert issue-bearing rejected rows into standardized rejected-evidence entries."""

    entries: list[RejectedEvidenceEntry] = []
    for row in rows:
        row_number = int(getattr(row, "row_number"))
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
) -> tuple[RejectedEvidenceEntry, ...]:
    """Convert reason-bearing rows into standardized rejected-evidence entries."""

    return tuple(
        build_rejected_evidence_entry(
            evidence_id=f"{source_surface}:{getattr(row, entity_field)}",
            source_surface=source_surface,
            reason_code=str(getattr(row, reason_field)),
            message=str(getattr(row, message_field)),
            related_artifact=related_artifact,
            entity_id=str(getattr(row, entity_field)),
        )
        for row in rows
    )


def _resolve_row_entity_id(row: object, *, entity_prefix: str) -> str:
    if hasattr(row, "entity_id") and str(getattr(row, "entity_id")).strip():
        return str(getattr(row, "entity_id")).strip()
    raw_fields = dict(getattr(row, "raw_fields", {}))
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
    return f"{entity_prefix}:{int(getattr(row, 'row_number'))}"


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
    "build_result_warning",
]
