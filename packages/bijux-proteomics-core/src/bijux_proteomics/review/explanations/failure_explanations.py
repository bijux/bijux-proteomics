# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Deterministic scientific failure explanations for governed workflow surfaces."""

from __future__ import annotations

from collections.abc import Callable
import csv
from enum import StrEnum
from io import StringIO
from typing import TypedDict

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class FailureExplanationCategory(StrEnum):
    """Stable categories for expected scientific workflow failures."""

    SCHEMA_ERROR = "schema_error"
    INVALID_DESIGN = "invalid_design"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    STATISTICAL_IMPOSSIBILITY = "statistical_impossibility"
    MISSING_ANNOTATION = "missing_annotation"


class FailureExplanationStatus(StrEnum):
    """Whether a failure text was classified confidently enough to explain."""

    EXPLAINED = "explained"
    UNCLASSIFIED = "unclassified"


class FailureExplanationRequest(JsonModel):
    """One deterministic scientific-failure explanation request."""

    model_config = ConfigDict(extra="forbid")

    failure_id: str = Field(..., min_length=1)
    failure_text: str = Field(..., min_length=1)
    workflow_name: str | None = None


class FailureExplanation(JsonModel):
    """One deterministic scientific failure explanation."""

    model_config = ConfigDict(extra="forbid")

    failure_id: str = Field(..., min_length=1)
    workflow_name: str | None = None
    status: FailureExplanationStatus
    failure_category: FailureExplanationCategory | None = None
    scientific_condition_code: str | None = None
    scientific_condition: str = Field(..., min_length=1)
    fix_recommendation: str = Field(..., min_length=1)
    raw_failure_text: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)


class FailureExplanationSummary(JsonModel):
    """Summary over one deterministic scientific-failure explanation pass."""

    model_config = ConfigDict(extra="forbid")

    explanation_count: int = Field(..., ge=0)
    explained_count: int = Field(..., ge=0)
    unclassified_count: int = Field(..., ge=0)
    schema_error_count: int = Field(..., ge=0)
    invalid_design_count: int = Field(..., ge=0)
    insufficient_evidence_count: int = Field(..., ge=0)
    statistical_impossibility_count: int = Field(..., ge=0)
    missing_annotation_count: int = Field(..., ge=0)


class FailureExplanationReport(JsonModel):
    """Deterministic scientific failure explanation report."""

    model_config = ConfigDict(extra="forbid")

    explanations: tuple[FailureExplanation, ...] = Field(default_factory=tuple)
    summary: FailureExplanationSummary
    note: str = Field(..., min_length=1)


class _FailureMatcher(TypedDict):
    category: FailureExplanationCategory
    condition_code: str
    condition: str
    fix: str
    note: str
    predicate: Callable[[str], bool]


def build_failure_explanation_report(
    requests: tuple[FailureExplanationRequest, ...],
) -> FailureExplanationReport:
    """Explain expected scientific workflow failures without free-text guessing."""

    explanations = tuple(_build_failure_explanation(request) for request in requests)
    return FailureExplanationReport(
        explanations=explanations,
        summary=FailureExplanationSummary(
            explanation_count=len(explanations),
            explained_count=sum(
                entry.status is FailureExplanationStatus.EXPLAINED
                for entry in explanations
            ),
            unclassified_count=sum(
                entry.status is FailureExplanationStatus.UNCLASSIFIED
                for entry in explanations
            ),
            schema_error_count=sum(
                entry.failure_category is FailureExplanationCategory.SCHEMA_ERROR
                for entry in explanations
            ),
            invalid_design_count=sum(
                entry.failure_category is FailureExplanationCategory.INVALID_DESIGN
                for entry in explanations
            ),
            insufficient_evidence_count=sum(
                entry.failure_category
                is FailureExplanationCategory.INSUFFICIENT_EVIDENCE
                for entry in explanations
            ),
            statistical_impossibility_count=sum(
                entry.failure_category
                is FailureExplanationCategory.STATISTICAL_IMPOSSIBILITY
                for entry in explanations
            ),
            missing_annotation_count=sum(
                entry.failure_category is FailureExplanationCategory.MISSING_ANNOTATION
                for entry in explanations
            ),
        ),
        note=(
            "failure explanations stay deterministic and classify only expected "
            "scientific workflow failures with explicit input-fix guidance"
        ),
    )


def render_failure_explanation_summary_tsv(report: FailureExplanationReport) -> str:
    """Render one-row scientific-failure summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "explanation_count",
            "explained_count",
            "unclassified_count",
            "schema_error_count",
            "invalid_design_count",
            "insufficient_evidence_count",
            "statistical_impossibility_count",
            "missing_annotation_count",
        )
    )
    writer.writerow(
        (
            report.summary.explanation_count,
            report.summary.explained_count,
            report.summary.unclassified_count,
            report.summary.schema_error_count,
            report.summary.invalid_design_count,
            report.summary.insufficient_evidence_count,
            report.summary.statistical_impossibility_count,
            report.summary.missing_annotation_count,
        )
    )
    return buffer.getvalue()


def render_failure_explanation_tsv(report: FailureExplanationReport) -> str:
    """Render deterministic scientific failure explanations as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "failure_id",
            "workflow_name",
            "status",
            "failure_category",
            "scientific_condition_code",
            "scientific_condition",
            "fix_recommendation",
            "raw_failure_text",
            "note",
        )
    )
    for explanation in report.explanations:
        writer.writerow(
            (
                explanation.failure_id,
                "" if explanation.workflow_name is None else explanation.workflow_name,
                explanation.status.value,
                (
                    ""
                    if explanation.failure_category is None
                    else explanation.failure_category.value
                ),
                (
                    ""
                    if explanation.scientific_condition_code is None
                    else explanation.scientific_condition_code
                ),
                explanation.scientific_condition,
                explanation.fix_recommendation,
                explanation.raw_failure_text,
                explanation.note,
            )
        )
    return buffer.getvalue()


def format_failure_explanation_for_cli(explanation: FailureExplanation) -> str:
    """Format one deterministic scientific failure explanation for operator output."""

    workflow_prefix = (
        "workflow failed"
        if explanation.workflow_name is None
        else f"workflow {explanation.workflow_name!r} failed"
    )
    if explanation.status is FailureExplanationStatus.UNCLASSIFIED:
        return (
            f"{workflow_prefix}: {explanation.raw_failure_text}. "
            "The failure did not match a known scientific category, so inspect the "
            "raw message and the governed inputs directly."
        )
    category = explanation.failure_category
    if category is None:
        raise ValueError(
            "classified failure explanations must carry a failure category"
        )
    return (
        f"{workflow_prefix} with {category.value}: "
        f"{explanation.scientific_condition}. "
        f"Fix input: {explanation.fix_recommendation}. "
        f"Raw failure: {explanation.raw_failure_text}."
    )


def _build_failure_explanation(
    request: FailureExplanationRequest,
) -> FailureExplanation:
    failure_text = request.failure_text.strip()
    lower_text = failure_text.lower()
    for matcher in _FAILURE_MATCHERS:
        if matcher["predicate"](lower_text):
            return FailureExplanation(
                failure_id=request.failure_id,
                workflow_name=request.workflow_name,
                status=FailureExplanationStatus.EXPLAINED,
                failure_category=matcher["category"],
                scientific_condition_code=matcher["condition_code"],
                scientific_condition=matcher["condition"],
                fix_recommendation=matcher["fix"],
                raw_failure_text=failure_text,
                note=matcher["note"],
            )
    return FailureExplanation(
        failure_id=request.failure_id,
        workflow_name=request.workflow_name,
        status=FailureExplanationStatus.UNCLASSIFIED,
        failure_category=None,
        scientific_condition_code=None,
        scientific_condition=(
            "the workflow failed with a message that does not yet map onto a governed "
            "scientific failure condition"
        ),
        fix_recommendation=(
            "inspect the raw failure text, confirm the failing workflow input, and add "
            "a governed scientific failure rule if this is an expected operator path"
        ),
        raw_failure_text=failure_text,
        note=(
            "the engine refused to invent a scientific category for an unrecognized "
            "failure string"
        ),
    )


def _contains_any(lower_text: str, patterns: tuple[str, ...]) -> bool:
    return any(pattern in lower_text for pattern in patterns)


_FAILURE_MATCHERS: tuple[_FailureMatcher, ...] = (
    {
        "category": FailureExplanationCategory.SCHEMA_ERROR,
        "condition_code": "input_schema_error",
        "condition": (
            "the supplied input file does not satisfy the governed schema expected by "
            "the scientific workflow"
        ),
        "fix": (
            "repair the failing input export so it includes a valid header row and all "
            "required columns before rerunning the workflow"
        ),
        "note": (
            "schema failures are reserved for governed input structure problems rather "
            "than downstream statistical or biological interpretation issues"
        ),
        "predicate": lambda lower_text: _contains_any(
            lower_text,
            (
                "schema error",
                "must include a header row",
                "missing required column",
                "missing required columns",
                "must be a design table",
            ),
        ),
    },
    {
        "category": FailureExplanationCategory.INVALID_DESIGN,
        "condition_code": "invalid_study_design",
        "condition": (
            "the supplied study design is invalid or inconsistent for the requested "
            "scientific comparison"
        ),
        "fix": (
            "repair rejected design rows and ensure samples, conditions, channels, and "
            "pairing fields are valid before rerunning the workflow"
        ),
        "note": (
            "design failures cover invalid contrast structure and broken sample "
            "metadata, not mere file-schema problems"
        ),
        "predicate": lambda lower_text: _contains_any(
            lower_text,
            (
                "design table contains rejected rows",
                "not present in the design table",
                "requires --sample-id when multiple rows are present",
                "must contain at least two distinct conditions",
                "requires unique multiplex channel",
                "invalid contrast",
            ),
        ),
    },
    {
        "category": FailureExplanationCategory.INSUFFICIENT_EVIDENCE,
        "condition_code": "insufficient_scientific_evidence",
        "condition": (
            "the requested scientific operation does not have enough accepted evidence "
            "to support a stable result"
        ),
        "fix": (
            "provide more accepted evidence rows, confirm the requested subject exists "
            "in the governed inputs, or rerun with an evidence surface that supports "
            "the requested question"
        ),
        "note": (
            "insufficient-evidence failures distinguish absent or too-thin evidence "
            "from invalid schema or impossible statistical models"
        ),
        "predicate": lambda lower_text: _contains_any(
            lower_text,
            (
                "insufficient evidence",
                "no ptm differential row matched",
                "no pathway activity row matched",
                "requires at least one candidate annotation",
                "requires reporter-matrix review",
                "requires protein-ratio review",
                "no matched",
            ),
        ),
    },
    {
        "category": FailureExplanationCategory.STATISTICAL_IMPOSSIBILITY,
        "condition_code": "statistical_model_impossible",
        "condition": (
            "the requested statistical model or correction is impossible under the "
            "supplied design and contrast structure"
        ),
        "fix": (
            "change the contrast, remove confounded or aliased covariates, avoid "
            "blocked batch correction, or add replication before rerunning"
        ),
        "note": (
            "statistical impossibility is reserved for confounded, rank-deficient, or "
            "otherwise non-estimable model states"
        ),
        "predicate": lambda lower_text: _contains_any(
            lower_text,
            (
                "fully confounded",
                "confounded with condition",
                "rank-deficient",
                "aliased columns",
                "impossible contrast",
                "cannot estimate",
                "blocks batch correction",
            ),
        ),
    },
    {
        "category": FailureExplanationCategory.MISSING_ANNOTATION,
        "condition_code": "required_annotation_missing",
        "condition": (
            "the workflow requires biological annotation or mapping that is missing or "
            "unresolved in the supplied inputs"
        ),
        "fix": (
            "provide the required annotation table or resolve unmapped protein, gene, "
            "or PTM-site identifiers before rerunning"
        ),
        "note": (
            "missing-annotation failures are reserved for absent or unresolved biology "
            "context rather than generic input-schema problems"
        ),
        "predicate": lambda lower_text: _contains_any(
            lower_text,
            (
                "could not be annotated",
                "lacks gene annotation required",
                "missing annotation",
                "required annotation",
                "unmapped annotation",
                "missing required ptm site annotation column",
            ),
        ),
    },
)


__all__ = [
    "FailureExplanation",
    "FailureExplanationCategory",
    "FailureExplanationReport",
    "FailureExplanationRequest",
    "FailureExplanationStatus",
    "FailureExplanationSummary",
    "build_failure_explanation_report",
    "format_failure_explanation_for_cli",
    "render_failure_explanation_summary_tsv",
    "render_failure_explanation_tsv",
]
