# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned study contrast parsing and semantic expansion surfaces."""

from __future__ import annotations

from itertools import combinations
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.records import (
    Contrast,
    ContrastKind,
    RejectedEvidence,
    SampleMetadata,
)
from bijux_proteomics._scientific_tables import (
    ScientificTableValidationContext,
    ScientificTableValidationIssue,
    build_contrast_table_schema,
    validate_scientific_table,
)
from bijux_proteomics_foundation import JsonModel


class StudyContrastIssue(JsonModel):
    """One stable issue over a governed study contrast specification."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    row_number: int | None = Field(default=None, ge=1)
    column: str | None = None
    specification: str | None = None


class StudyContrastRejectedSpecification(JsonModel):
    """One rejected contrast specification from text or table input."""

    model_config = ConfigDict(extra="forbid")

    row_number: int | None = Field(default=None, ge=1)
    specification: str | None = None
    raw_values: dict[str, str] = Field(default_factory=dict)
    issues: tuple[StudyContrastIssue, ...] = Field(default_factory=tuple)

    def to_domain_record(self) -> RejectedEvidence:
        """Expose one rejected contrast specification as canonical evidence."""

        return RejectedEvidence(
            record_kind="contrast",
            rejection_reason="; ".join(issue.message for issue in self.issues)
            or "rejected contrast specification",
            row_number=self.row_number,
            raw_fields=self.raw_values,
            metadata={
                "source_contract": "study.contrast_rejected_specification",
                "specification": self.specification or "",
                "issue_codes": ";".join(issue.code for issue in self.issues),
            },
        )


class StudyContrastSummary(JsonModel):
    """Compact summary over one study contrast parsing run."""

    model_config = ConfigDict(extra="forbid")

    requested_specification_count: int = Field(..., ge=0)
    expanded_contrast_count: int = Field(..., ge=0)
    rejected_specification_count: int = Field(..., ge=0)
    pairwise_count: int = Field(..., ge=0)
    case_control_count: int = Field(..., ge=0)
    paired_count: int = Field(..., ge=0)
    time_course_count: int = Field(..., ge=0)
    multi_condition_count: int = Field(..., ge=0)


class StudyContrastParseReport(JsonModel):
    """Stable parse report over explicit study contrast semantics."""

    model_config = ConfigDict(extra="forbid")

    contrasts: tuple[Contrast, ...] = Field(default_factory=tuple)
    rejected_specifications: tuple[StudyContrastRejectedSpecification, ...] = Field(
        default_factory=tuple
    )
    summary: StudyContrastSummary


def build_case_control_contrast(
    *,
    case_condition: str,
    control_condition: str,
    contrast_id: str | None = None,
    metadata: dict[str, str] | None = None,
) -> Contrast:
    """Build one explicit case-control contrast."""

    return Contrast(
        contrast_id=contrast_id or _contrast_id(case_condition, control_condition),
        left_condition=case_condition,
        right_condition=control_condition,
        kind=ContrastKind.CASE_CONTROL,
        metadata=metadata or {},
    )


def build_pairwise_contrast(
    *,
    left_condition: str,
    right_condition: str,
    contrast_id: str | None = None,
    metadata: dict[str, str] | None = None,
) -> Contrast:
    """Build one explicit pairwise contrast."""

    return Contrast(
        contrast_id=contrast_id or _contrast_id(left_condition, right_condition),
        left_condition=left_condition,
        right_condition=right_condition,
        kind=ContrastKind.PAIRWISE,
        metadata=metadata or {},
    )


def build_paired_contrast(
    *,
    left_condition: str,
    right_condition: str,
    pair_id_field: str = "pair_id",
    contrast_id: str | None = None,
    metadata: dict[str, str] | None = None,
) -> Contrast:
    """Build one explicit paired contrast."""

    return Contrast(
        contrast_id=contrast_id or _contrast_id(left_condition, right_condition),
        left_condition=left_condition,
        right_condition=right_condition,
        kind=ContrastKind.PAIRED,
        pair_id_field=pair_id_field,
        metadata=metadata or {},
    )


def build_time_course_contrast(
    *,
    left_condition: str,
    right_condition: str,
    timepoint_field: str = "timepoint",
    contrast_id: str | None = None,
    metadata: dict[str, str] | None = None,
) -> Contrast:
    """Build one explicit time-course contrast."""

    return Contrast(
        contrast_id=contrast_id or _contrast_id(left_condition, right_condition),
        left_condition=left_condition,
        right_condition=right_condition,
        kind=ContrastKind.TIME_COURSE,
        timepoint_field=timepoint_field,
        metadata=metadata or {},
    )


def parse_study_contrast_specifications(
    specifications: tuple[str, ...],
    *,
    sample_metadata: tuple[SampleMetadata, ...],
) -> StudyContrastParseReport:
    """Parse explicit study comparison specifications into canonical contrasts."""

    contrasts: list[Contrast] = []
    rejected: list[StudyContrastRejectedSpecification] = []
    for specification in specifications:
        parsed_contrasts, issues = _parse_inline_specification(
            specification,
            sample_metadata=sample_metadata,
        )
        if issues:
            rejected.append(
                StudyContrastRejectedSpecification(
                    specification=specification,
                    issues=issues,
                )
            )
            continue
        contrasts.extend(parsed_contrasts)
    return _build_parse_report(
        requested_specification_count=len(specifications),
        contrasts=contrasts,
        rejected_specifications=rejected,
    )


def parse_study_contrast_table(
    path: Path,
    *,
    sample_metadata: tuple[SampleMetadata, ...],
) -> StudyContrastParseReport:
    """Parse a governed study contrast table into canonical contrasts."""

    validation_report = validate_scientific_table(
        path,
        schema=build_contrast_table_schema(),
        context=ScientificTableValidationContext(
            known_conditions=tuple(
                sorted({entry.condition for entry in sample_metadata if entry.condition})
            )
        ),
    )
    contrasts: list[Contrast] = []
    rejected = [
        StudyContrastRejectedSpecification(
            row_number=row.row_number,
            raw_values=row.raw_values,
            issues=_translate_scientific_issues(row.issues),
        )
        for row in validation_report.rejected_rows
    ]
    for row in validation_report.accepted_rows:
        parsed_contrasts, issues = _parse_table_row(
            row_number=row.row_number,
            raw_values=row.raw_values,
            values={
                key: str(value) if value is not None else ""
                for key, value in row.values.items()
            },
            sample_metadata=sample_metadata,
        )
        if issues:
            rejected.append(
                StudyContrastRejectedSpecification(
                    row_number=row.row_number,
                    raw_values=row.raw_values,
                    issues=issues,
                )
            )
            continue
        contrasts.extend(parsed_contrasts)
    return _build_parse_report(
        requested_specification_count=len(validation_report.accepted_rows)
        + len(validation_report.rejected_rows),
        contrasts=contrasts,
        rejected_specifications=rejected,
    )


def resolve_pairwise_study_contrast(
    specification: str,
    *,
    sample_metadata: tuple[SampleMetadata, ...],
) -> Contrast:
    """Resolve one explicit pairwise-like study contrast for pairwise workflows."""

    report = parse_study_contrast_specifications(
        (specification,),
        sample_metadata=sample_metadata,
    )
    if report.rejected_specifications:
        first_issue = report.rejected_specifications[0].issues[0]
        raise ValueError(first_issue.message)
    if len(report.contrasts) != 1:
        raise ValueError(
            "pairwise workflows require a contrast specification that resolves to exactly one comparison"
        )
    return report.contrasts[0]


def _parse_inline_specification(
    specification: str,
    *,
    sample_metadata: tuple[SampleMetadata, ...],
) -> tuple[tuple[Contrast, ...], tuple[StudyContrastIssue, ...]]:
    normalized = specification.strip()
    if not normalized:
        return (), (
            _issue(
                code="invalid_contrast_specification",
                message="contrast specification cannot be empty",
                specification=specification,
            ),
        )
    lowered = normalized.lower()
    if lowered.startswith(("case-control:", "case_control:")):
        payload = normalized.split(":", maxsplit=1)[1]
        return _build_binary_contrast(
            payload=payload,
            kind=ContrastKind.CASE_CONTROL,
            sample_metadata=sample_metadata,
            specification=specification,
        )
    if lowered.startswith("paired:"):
        payload = normalized.split(":", maxsplit=1)[1]
        return _build_binary_contrast(
            payload=payload,
            kind=ContrastKind.PAIRED,
            sample_metadata=sample_metadata,
            pair_id_field="pair_id",
            specification=specification,
        )
    if lowered.startswith(("time-course:", "time_course:")):
        payload = normalized.split(":", maxsplit=1)[1]
        return _build_binary_contrast(
            payload=payload,
            kind=ContrastKind.TIME_COURSE,
            sample_metadata=sample_metadata,
            timepoint_field="timepoint",
            specification=specification,
        )
    if lowered.startswith(("multi-condition:", "multi_condition:")):
        payload = normalized.split(":", maxsplit=1)[1]
        return _build_multi_condition_contrasts(
            payload=payload,
            sample_metadata=sample_metadata,
            specification=specification,
        )
    return _build_binary_contrast(
        payload=normalized,
        kind=ContrastKind.PAIRWISE,
        sample_metadata=sample_metadata,
        specification=specification,
    )


def _parse_table_row(
    *,
    row_number: int,
    raw_values: dict[str, str],
    values: dict[str, str],
    sample_metadata: tuple[SampleMetadata, ...],
) -> tuple[tuple[Contrast, ...], tuple[StudyContrastIssue, ...]]:
    kind_text = values.get("kind", "").strip()
    try:
        kind = ContrastKind(kind_text)
    except ValueError:
        return (), (
            _issue(
                code="invalid_contrast_kind",
                message=f"contrast row uses unsupported kind {kind_text!r}",
                row_number=row_number,
                column="kind",
            ),
        )

    if kind is ContrastKind.MULTI_CONDITION:
        return _build_multi_condition_contrasts(
            payload=values.get("condition_set", ""),
            sample_metadata=sample_metadata,
            specification=raw_values.get("contrast_id"),
            contrast_id_prefix=values.get("contrast_id") or None,
            row_number=row_number,
        )

    pair_id_field = _optional_text(values.get("pair_id_field"))
    timepoint_field = _optional_text(values.get("timepoint_field"))
    if kind is ContrastKind.PAIRED and pair_id_field is None:
        pair_id_field = "pair_id"
    if kind is ContrastKind.TIME_COURSE and timepoint_field is None:
        timepoint_field = "timepoint"
    return _build_binary_contrast(
        payload=f"{values.get('left_condition', '')}-{values.get('right_condition', '')}",
        kind=kind,
        sample_metadata=sample_metadata,
        pair_id_field=pair_id_field,
        timepoint_field=timepoint_field,
        specification=raw_values.get("contrast_id"),
        contrast_id=values.get("contrast_id") or None,
        row_number=row_number,
    )


def _build_binary_contrast(
    *,
    payload: str,
    kind: ContrastKind,
    sample_metadata: tuple[SampleMetadata, ...],
    pair_id_field: str | None = None,
    timepoint_field: str | None = None,
    specification: str | None = None,
    contrast_id: str | None = None,
    row_number: int | None = None,
) -> tuple[tuple[Contrast, ...], tuple[StudyContrastIssue, ...]]:
    split_pair = _split_two_conditions(payload)
    if split_pair is None:
        return (), (
            _issue(
                code="invalid_contrast_specification",
                message=(
                    "binary contrast specifications must compare exactly two conditions using '-', ':', or ','"
                ),
                row_number=row_number,
                specification=specification,
            ),
        )
    left_condition, right_condition = split_pair
    condition_issues = _validate_conditions(
        left_condition,
        right_condition,
        sample_metadata=sample_metadata,
        row_number=row_number,
        specification=specification,
    )
    if condition_issues:
        return (), condition_issues
    semantic_issues = _validate_kind_specific_semantics(
        kind=kind,
        left_condition=left_condition,
        right_condition=right_condition,
        sample_metadata=sample_metadata,
        pair_id_field=pair_id_field,
        timepoint_field=timepoint_field,
        row_number=row_number,
        specification=specification,
    )
    if semantic_issues:
        return (), semantic_issues

    metadata = {}
    if specification:
        metadata["source_specification"] = specification
    if kind is ContrastKind.CASE_CONTROL:
        contrast = build_case_control_contrast(
            case_condition=left_condition,
            control_condition=right_condition,
            contrast_id=contrast_id,
            metadata=metadata,
        )
    elif kind is ContrastKind.PAIRED:
        contrast = build_paired_contrast(
            left_condition=left_condition,
            right_condition=right_condition,
            pair_id_field=pair_id_field or "pair_id",
            contrast_id=contrast_id,
            metadata=metadata,
        )
    elif kind is ContrastKind.TIME_COURSE:
        contrast = build_time_course_contrast(
            left_condition=left_condition,
            right_condition=right_condition,
            timepoint_field=timepoint_field or "timepoint",
            contrast_id=contrast_id,
            metadata=metadata,
        )
    else:
        contrast = build_pairwise_contrast(
            left_condition=left_condition,
            right_condition=right_condition,
            contrast_id=contrast_id,
            metadata=metadata,
        )
    return (contrast,), ()


def _build_multi_condition_contrasts(
    *,
    payload: str,
    sample_metadata: tuple[SampleMetadata, ...],
    specification: str | None = None,
    contrast_id_prefix: str | None = None,
    row_number: int | None = None,
) -> tuple[tuple[Contrast, ...], tuple[StudyContrastIssue, ...]]:
    conditions = tuple(
        dict.fromkeys(
            item.strip() for item in payload.split(",") if item and item.strip()
        )
    )
    if len(conditions) < 3:
        return (), (
            _issue(
                code="invalid_multi_condition_specification",
                message=(
                    "multi-condition comparisons require at least three comma-separated conditions"
                ),
                row_number=row_number,
                column="condition_set",
                specification=specification,
            ),
        )
    known_conditions = {entry.condition for entry in sample_metadata if entry.condition}
    issues: list[StudyContrastIssue] = []
    for condition in conditions:
        if condition not in known_conditions:
            issues.append(
                _issue(
                    code="unknown_condition",
                    message=f"contrast references unknown condition {condition!r}",
                    row_number=row_number,
                    column="condition_set",
                    specification=specification,
                )
            )
    if issues:
        return (), tuple(issues)
    contrasts: list[Contrast] = []
    for left_condition, right_condition in combinations(conditions, 2):
        contrast_metadata = {}
        if specification:
            contrast_metadata["source_specification"] = specification
        contrasts.append(
            Contrast(
                contrast_id=(
                    f"{contrast_id_prefix}__{left_condition}__vs__{right_condition}"
                    if contrast_id_prefix
                    else f"multi_condition__{left_condition}__vs__{right_condition}"
                ),
                left_condition=left_condition,
                right_condition=right_condition,
                kind=ContrastKind.MULTI_CONDITION,
                condition_set=conditions,
                metadata=contrast_metadata,
            )
        )
    return tuple(contrasts), ()


def _validate_conditions(
    left_condition: str,
    right_condition: str,
    *,
    sample_metadata: tuple[SampleMetadata, ...],
    row_number: int | None,
    specification: str | None,
) -> tuple[StudyContrastIssue, ...]:
    issues: list[StudyContrastIssue] = []
    if left_condition == right_condition:
        issues.append(
            _issue(
                code="impossible_contrast",
                message="contrast must compare two distinct conditions",
                row_number=row_number,
                specification=specification,
            )
        )
    known_conditions = {entry.condition for entry in sample_metadata if entry.condition}
    if left_condition not in known_conditions:
        issues.append(
            _issue(
                code="unknown_condition",
                message=f"contrast references unknown condition {left_condition!r}",
                row_number=row_number,
                column="left_condition",
                specification=specification,
            )
        )
    if right_condition not in known_conditions:
        issues.append(
            _issue(
                code="unknown_condition",
                message=f"contrast references unknown condition {right_condition!r}",
                row_number=row_number,
                column="right_condition",
                specification=specification,
            )
        )
    return tuple(issues)


def _validate_kind_specific_semantics(
    *,
    kind: ContrastKind,
    left_condition: str,
    right_condition: str,
    sample_metadata: tuple[SampleMetadata, ...],
    pair_id_field: str | None,
    timepoint_field: str | None,
    row_number: int | None,
    specification: str | None,
) -> tuple[StudyContrastIssue, ...]:
    relevant_entries = tuple(
        entry
        for entry in sample_metadata
        if entry.condition in {left_condition, right_condition}
    )
    if kind is ContrastKind.PAIRED:
        if any(entry.pair_id in (None, "") for entry in relevant_entries):
            return (
                _issue(
                    code="missing_pair_id",
                    message="paired contrasts require pair_id values for every compared sample",
                    row_number=row_number,
                    column=pair_id_field or "pair_id",
                    specification=specification,
                ),
            )
        pair_conditions: dict[str, set[str]] = {}
        for entry in relevant_entries:
            pair_conditions.setdefault(str(entry.pair_id), set()).add(entry.condition)
        matched_pair_count = sum(
            1
            for conditions in pair_conditions.values()
            if {left_condition, right_condition}.issubset(conditions)
        )
        if matched_pair_count == 0:
            return (
                _issue(
                    code="missing_paired_comparison",
                    message="paired contrasts require at least one pair_id shared across both compared conditions",
                    row_number=row_number,
                    column=pair_id_field or "pair_id",
                    specification=specification,
                ),
            )
    if kind is ContrastKind.TIME_COURSE and any(
        entry.timepoint in (None, "") for entry in relevant_entries
    ):
        return (
            _issue(
                code="missing_timepoint",
                message="time-course contrasts require timepoint values for every compared sample",
                row_number=row_number,
                column=timepoint_field or "timepoint",
                specification=specification,
            ),
        )
    return ()


def _split_two_conditions(payload: str) -> tuple[str, str] | None:
    for separator in ("-", ":", ","):
        if separator not in payload:
            continue
        left, right = payload.split(separator, maxsplit=1)
        left_condition = left.strip()
        right_condition = right.strip()
        if left_condition and right_condition:
            return left_condition, right_condition
    return None


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text or None


def _issue(
    *,
    code: str,
    message: str,
    row_number: int | None = None,
    column: str | None = None,
    specification: str | None = None,
) -> StudyContrastIssue:
    return StudyContrastIssue(
        code=code,
        message=message,
        row_number=row_number,
        column=column,
        specification=specification,
    )


def _translate_scientific_issues(
    issues: tuple[ScientificTableValidationIssue, ...],
) -> tuple[StudyContrastIssue, ...]:
    translated: list[StudyContrastIssue] = []
    for issue in issues:
        if issue.code == "missing_column":
            translated.append(
                _issue(
                    code="missing_contrast_column",
                    message=f"contrast table is missing required column {issue.column!r}",
                    row_number=issue.row_number,
                    column=issue.column,
                )
            )
            continue
        if issue.code == "duplicate_identifier":
            translated.append(
                _issue(
                    code="duplicate_contrast_id",
                    message=issue.message,
                    row_number=issue.row_number,
                    column=issue.column,
                )
            )
            continue
        translated.append(
            _issue(
                code="invalid_contrast_row",
                message=issue.message,
                row_number=issue.row_number,
                column=issue.column,
            )
        )
    return tuple(translated)


def _contrast_id(left_condition: str, right_condition: str) -> str:
    return f"{left_condition}__vs__{right_condition}"


def _build_parse_report(
    *,
    requested_specification_count: int,
    contrasts: list[Contrast],
    rejected_specifications: list[StudyContrastRejectedSpecification],
) -> StudyContrastParseReport:
    summary = StudyContrastSummary(
        requested_specification_count=requested_specification_count,
        expanded_contrast_count=len(contrasts),
        rejected_specification_count=len(rejected_specifications),
        pairwise_count=sum(
            1 for contrast in contrasts if contrast.kind is ContrastKind.PAIRWISE
        ),
        case_control_count=sum(
            1
            for contrast in contrasts
            if contrast.kind is ContrastKind.CASE_CONTROL
        ),
        paired_count=sum(
            1 for contrast in contrasts if contrast.kind is ContrastKind.PAIRED
        ),
        time_course_count=sum(
            1 for contrast in contrasts if contrast.kind is ContrastKind.TIME_COURSE
        ),
        multi_condition_count=sum(
            1
            for contrast in contrasts
            if contrast.kind is ContrastKind.MULTI_CONDITION
        ),
    )
    return StudyContrastParseReport(
        contrasts=tuple(contrasts),
        rejected_specifications=tuple(
            sorted(
                rejected_specifications,
                key=lambda entry: (entry.row_number or 0, entry.specification or ""),
            )
        ),
        summary=summary,
    )
