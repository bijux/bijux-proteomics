# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Explicit foreground/background biology models for enrichment workflows."""

from __future__ import annotations

from bijux_proteomics._output_tables import write_output_table_tsv

import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.interpretation.protein_annotation_mapping import ProteinReferenceEntry
from bijux_proteomics_foundation import JsonModel


class BiologicalSetSourceKind(StrEnum):
    """Stable source kinds for enrichment foreground/background sets."""

    DIFFERENTIAL_SIGNIFICANT_RESULTS = "differential_significant_results"
    MEASURED_QUANT_MATRIX = "measured_quant_matrix"
    EXPLICIT_INPUT = "explicit_input"
    MEMBERSHIP_UNIVERSE = "membership_universe"
    ANNOTATION_UNIVERSE = "annotation_universe"


class BiologicalSetRole(StrEnum):
    """Stable set roles in one enrichment model."""

    FOREGROUND = "foreground"
    BACKGROUND = "background"


class InvalidBackgroundAction(StrEnum):
    """Action taken when the background source is scientifically weak."""

    WARN = "warn"
    REJECT = "reject"


class BiologicalSetFilteringPolicy(JsonModel):
    """Filtering policy preserved for one enrichment set."""

    model_config = ConfigDict(extra="forbid")

    policy_name: str = Field(..., min_length=1)
    max_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    min_absolute_log2_fold_change: float | None = Field(default=None, ge=0.0)
    measured_entities_only: bool = True
    deduplicate_protein_refs: bool = True
    note: str = Field(..., min_length=1)


class BiologicalSetEntry(JsonModel):
    """One protein preserved on a foreground/background biology model."""

    model_config = ConfigDict(extra="forbid")

    set_role: BiologicalSetRole
    protein_ref: str = Field(..., min_length=1)
    source_row_id: str | None = None


class BiologicalSetIssueSeverity(StrEnum):
    """Severity labels for foreground/background model issues."""

    CAUTION = "caution"
    BLOCKING = "blocking"


class BiologicalSetIssue(JsonModel):
    """One validity issue on a foreground/background biology model."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    severity: BiologicalSetIssueSeverity
    message: str = Field(..., min_length=1)


class BiologicalForegroundBackgroundSummary(JsonModel):
    """Stable summary over one foreground/background biology model."""

    model_config = ConfigDict(extra="forbid")

    foreground_size: int = Field(..., ge=0)
    background_size: int = Field(..., ge=0)
    issue_count: int = Field(..., ge=0)
    blocking_issue_count: int = Field(..., ge=0)
    valid_for_enrichment: bool


class BiologicalForegroundBackgroundModel(JsonModel):
    """Explicit foreground/background input model for biological enrichment."""

    model_config = ConfigDict(extra="forbid")

    foreground_source_kind: BiologicalSetSourceKind
    background_source_kind: BiologicalSetSourceKind
    foreground_policy: BiologicalSetFilteringPolicy
    background_policy: BiologicalSetFilteringPolicy
    foreground_entries: tuple[BiologicalSetEntry, ...] = Field(default_factory=tuple)
    background_entries: tuple[BiologicalSetEntry, ...] = Field(default_factory=tuple)
    issues: tuple[BiologicalSetIssue, ...] = Field(default_factory=tuple)
    summary: BiologicalForegroundBackgroundSummary
    note: str = Field(..., min_length=1)


def build_biological_foreground_background_model(
    foreground_entries: tuple[ProteinReferenceEntry, ...],
    background_entries: tuple[ProteinReferenceEntry, ...],
    *,
    foreground_source_kind: BiologicalSetSourceKind,
    background_source_kind: BiologicalSetSourceKind,
    foreground_policy: BiologicalSetFilteringPolicy,
    background_policy: BiologicalSetFilteringPolicy,
    invalid_background_action: InvalidBackgroundAction = InvalidBackgroundAction.REJECT,
) -> BiologicalForegroundBackgroundModel:
    """Build one explicit foreground/background enrichment model and validate it."""

    stable_foreground = _stable_entries(foreground_entries, role=BiologicalSetRole.FOREGROUND)
    stable_background = _stable_entries(background_entries, role=BiologicalSetRole.BACKGROUND)
    foreground_refs = {entry.protein_ref for entry in stable_foreground}
    background_refs = {entry.protein_ref for entry in stable_background}

    issues: list[BiologicalSetIssue] = []
    if not foreground_refs:
        issues.append(
            BiologicalSetIssue(
                code="empty_foreground",
                severity=BiologicalSetIssueSeverity.BLOCKING,
                message="foreground biology model must contain at least one protein",
            )
        )
    if not background_refs:
        issues.append(
            BiologicalSetIssue(
                code="empty_background",
                severity=BiologicalSetIssueSeverity.BLOCKING,
                message="background biology model must contain at least one protein",
            )
        )
    if foreground_refs and background_refs and not foreground_refs <= background_refs:
        missing = tuple(sorted(foreground_refs - background_refs))
        issues.append(
            BiologicalSetIssue(
                code="foreground_outside_background",
                severity=BiologicalSetIssueSeverity.BLOCKING,
                message=(
                    "foreground proteins must all be present in the background set: "
                    + ", ".join(missing)
                ),
            )
        )
    if background_refs and foreground_refs and len(background_refs) <= len(foreground_refs):
        issues.append(
            BiologicalSetIssue(
                code="background_not_broader_than_foreground",
                severity=BiologicalSetIssueSeverity.BLOCKING,
                message=(
                    "background set must be broader than the foreground set for "
                    "scientifically interpretable enrichment"
                ),
            )
        )
    if background_source_kind in {
        BiologicalSetSourceKind.MEMBERSHIP_UNIVERSE,
        BiologicalSetSourceKind.ANNOTATION_UNIVERSE,
    }:
        issues.append(
            BiologicalSetIssue(
                code=f"{background_source_kind.value}_background",
                severity=(
                    BiologicalSetIssueSeverity.CAUTION
                    if invalid_background_action is InvalidBackgroundAction.WARN
                    else BiologicalSetIssueSeverity.BLOCKING
                ),
                message=(
                    "background derived from annotation or membership universe can be "
                    "scientifically invalid because it is broader than the measured study "
                    "universe"
                ),
            )
        )

    stable_issues = tuple(
        sorted(
            issues,
            key=lambda issue: (
                issue.severity.value,
                issue.code,
            ),
        )
    )
    blocking_issue_count = sum(
        1
        for issue in stable_issues
        if issue.severity is BiologicalSetIssueSeverity.BLOCKING
    )
    return BiologicalForegroundBackgroundModel(
        foreground_source_kind=foreground_source_kind,
        background_source_kind=background_source_kind,
        foreground_policy=foreground_policy,
        background_policy=background_policy,
        foreground_entries=stable_foreground,
        background_entries=stable_background,
        issues=stable_issues,
        summary=BiologicalForegroundBackgroundSummary(
            foreground_size=len(foreground_refs),
            background_size=len(background_refs),
            issue_count=len(stable_issues),
            blocking_issue_count=blocking_issue_count,
            valid_for_enrichment=blocking_issue_count == 0,
        ),
        note=(
            "foreground/background biology models preserve explicit source and "
            "filtering policy so enrichment never relies on a silent universe choice"
        ),
    )


def require_valid_biological_foreground_background_model(
    model: BiologicalForegroundBackgroundModel,
) -> BiologicalForegroundBackgroundModel:
    """Require a biology model that is valid for enrichment."""

    if model.summary.valid_for_enrichment:
        return model
    messages = "; ".join(issue.message for issue in model.issues)
    raise ValueError(f"invalid enrichment foreground/background model: {messages}")


def render_biological_foreground_background_summary_tsv(
    model: BiologicalForegroundBackgroundModel,
) -> str:
    """Render compact foreground/background summary as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "foreground_source_kind",
            "background_source_kind",
            "foreground_policy_name",
            "background_policy_name",
            "foreground_size",
            "background_size",
            "issue_count",
            "blocking_issue_count",
            "valid_for_enrichment",
        )
    )
    writer.writerow(
        (
            model.foreground_source_kind.value,
            model.background_source_kind.value,
            model.foreground_policy.policy_name,
            model.background_policy.policy_name,
            model.summary.foreground_size,
            model.summary.background_size,
            model.summary.issue_count,
            model.summary.blocking_issue_count,
            str(model.summary.valid_for_enrichment).lower(),
        )
    )
    return handle.getvalue()


def render_biological_foreground_background_entry_tsv(
    model: BiologicalForegroundBackgroundModel,
) -> str:
    """Render foreground/background protein entries as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("set_role", "protein_ref", "source_row_id"))
    for entry in model.foreground_entries + model.background_entries:
        writer.writerow(
            (
                entry.set_role.value,
                entry.protein_ref,
                "" if entry.source_row_id is None else entry.source_row_id,
            )
        )
    return handle.getvalue()


def render_biological_foreground_background_issue_tsv(
    model: BiologicalForegroundBackgroundModel,
) -> str:
    """Render foreground/background validity issues as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("code", "severity", "message"))
    for issue in model.issues:
        writer.writerow((issue.code, issue.severity.value, issue.message))
    return handle.getvalue()


def export_biological_foreground_background_summary_tsv(
    model: BiologicalForegroundBackgroundModel,
    path: Path,
) -> None:
    """Write one biological foreground/background summary TSV artifact."""

    write_output_table_tsv(path, render_biological_foreground_background_summary_tsv(model))


def export_biological_foreground_background_entry_tsv(
    model: BiologicalForegroundBackgroundModel,
    path: Path,
) -> None:
    """Write one biological foreground/background entry TSV artifact."""

    write_output_table_tsv(path, render_biological_foreground_background_entry_tsv(model))


def export_biological_foreground_background_issue_tsv(
    model: BiologicalForegroundBackgroundModel,
    path: Path,
) -> None:
    """Write one biological foreground/background issue TSV artifact."""

    write_output_table_tsv(path, render_biological_foreground_background_issue_tsv(model))


def _stable_entries(
    entries: tuple[ProteinReferenceEntry, ...],
    *,
    role: BiologicalSetRole,
) -> tuple[BiologicalSetEntry, ...]:
    deduplicated: dict[str, BiologicalSetEntry] = {}
    for entry in entries:
        deduplicated.setdefault(
            entry.protein_ref,
            BiologicalSetEntry(
                set_role=role,
                protein_ref=entry.protein_ref,
                source_row_id=entry.source_row_id,
            ),
        )
    return tuple(
        sorted(
            deduplicated.values(),
            key=lambda entry: (entry.protein_ref, entry.source_row_id or ""),
        )
    )


__all__ = [
    "BiologicalForegroundBackgroundModel",
    "BiologicalForegroundBackgroundSummary",
    "BiologicalSetEntry",
    "BiologicalSetFilteringPolicy",
    "BiologicalSetIssue",
    "BiologicalSetIssueSeverity",
    "BiologicalSetRole",
    "BiologicalSetSourceKind",
    "InvalidBackgroundAction",
    "build_biological_foreground_background_model",
    "export_biological_foreground_background_entry_tsv",
    "export_biological_foreground_background_issue_tsv",
    "export_biological_foreground_background_summary_tsv",
    "render_biological_foreground_background_entry_tsv",
    "render_biological_foreground_background_issue_tsv",
    "render_biological_foreground_background_summary_tsv",
    "require_valid_biological_foreground_background_model",
]
