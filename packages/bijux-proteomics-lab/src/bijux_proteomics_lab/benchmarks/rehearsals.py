# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Targeted benchmark rehearsal owners for operator and reviewer delivery."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel

from .claims import (
    TargetedBenchmarkClaimSupport,
    TargetedBenchmarkReport,
)


class TargetedOperatorRunReport(JsonModel):
    """Operator-facing rehearsal summary for a targeted benchmark run."""

    model_config = ConfigDict(extra="forbid")

    benchmark_id: str = Field(..., min_length=1)
    candidate_id: str = Field(..., min_length=1)
    ready_for_operator_review: bool
    artifact_ids: tuple[str, ...] = Field(default_factory=tuple)
    checklist: tuple[str, ...] = Field(default_factory=tuple)
    blocked_items: tuple[str, ...] = Field(default_factory=tuple)
    notes: tuple[str, ...] = Field(default_factory=tuple)


class TargetedFailureRehearsalReport(JsonModel):
    """Failure-path rehearsal that keeps downgrade and refusal diagnostics explicit."""

    model_config = ConfigDict(extra="forbid")

    benchmark_id: str = Field(..., min_length=1)
    overall_support: TargetedBenchmarkClaimSupport
    failure_codes: tuple[str, ...] = Field(default_factory=tuple)
    honest_summary: str = Field(..., min_length=1)
    next_actions: tuple[str, ...] = Field(default_factory=tuple)
    diagnostics: tuple[str, ...] = Field(default_factory=tuple)


class TargetedExternalReviewReport(JsonModel):
    """External-review rehearsal answers for targeted benchmark scrutiny."""

    model_config = ConfigDict(extra="forbid")

    benchmark_id: str = Field(..., min_length=1)
    ssot_answer: str = Field(..., min_length=1)
    compatibility_answer: str = Field(..., min_length=1)
    benchmarked_answer: str = Field(..., min_length=1)
    weak_answer: str = Field(..., min_length=1)


def build_targeted_operator_run_report(
    report: TargetedBenchmarkReport,
) -> TargetedOperatorRunReport:
    """Render a useful-run operator summary from a targeted benchmark report."""
    blocked_items = tuple(
        summary.summary
        for summary in report.claim_summaries
        if summary.support is TargetedBenchmarkClaimSupport.UNSUPPORTED
    )
    ready_for_operator_review = (
        report.overall_support is not TargetedBenchmarkClaimSupport.UNSUPPORTED
        and report.operational_path.refusal is None
        and bool(report.lims_export_bundle.records)
    )
    first_record = report.lims_export_bundle.records[0]
    checklist = (
        "review transition-level QC before protein rollup",
        f"confirm required controls for {first_record.protocol_id}: {', '.join(first_record.required_controls)}",
        f"review export field mapping for {report.lims_export_bundle.system_name}",
        f"confirm batch {report.operational_path.execution_request.batch_id} is aligned with the top candidate",
    )
    return TargetedOperatorRunReport(
        benchmark_id=report.benchmark_id,
        candidate_id=report.recommended_candidate_id,
        ready_for_operator_review=ready_for_operator_review,
        artifact_ids=(
            report.dataset_id,
            report.lims_export_bundle.bundle_id,
            report.operational_path.execution_request.batch_id,
        ),
        checklist=checklist,
        blocked_items=blocked_items,
        notes=(
            report.operational_path.explanation.summary,
            report.operational_path.reconciliation.intelligence_feedback.recommended_action,
        ),
    )


def build_targeted_failure_rehearsal(
    report: TargetedBenchmarkReport,
) -> TargetedFailureRehearsalReport:
    """Summarize why a targeted benchmark path must be downgraded or refused."""
    failing_claims = tuple(
        summary
        for summary in report.claim_summaries
        if summary.support is not TargetedBenchmarkClaimSupport.STRONG_SUPPORT
    )
    if not failing_claims:
        summary = "targeted benchmark path is strong enough that no failure rehearsal blockers remain"
    elif any(
        claim.support is TargetedBenchmarkClaimSupport.UNSUPPORTED
        for claim in failing_claims
    ):
        summary = "targeted benchmark signoff must be refused until unsupported claims are cleared"
    else:
        summary = "targeted benchmark signoff must stay downgraded until partial-support claims are strengthened"

    next_actions = tuple(
        diagnostic
        for claim in failing_claims
        for diagnostic in claim.diagnostics
        if diagnostic
    )
    return TargetedFailureRehearsalReport(
        benchmark_id=report.benchmark_id,
        overall_support=report.overall_support,
        failure_codes=tuple(claim.claim_id for claim in failing_claims),
        honest_summary=summary,
        next_actions=next_actions,
        diagnostics=tuple(claim.summary for claim in failing_claims),
    )


def build_targeted_external_review_report(
    report: TargetedBenchmarkReport,
) -> TargetedExternalReviewReport:
    """Answer the four review questions required for external benchmark scrutiny."""
    weak_claims = [
        claim.summary
        for claim in report.claim_summaries
        if claim.support is not TargetedBenchmarkClaimSupport.STRONG_SUPPORT
    ]
    weak_answer = (
        "Weak points remain: " + "; ".join(weak_claims)
        if weak_claims
        else "Weak points are currently limited to the explicit comparison scope notes in the benchmark manifest."
    )
    return TargetedExternalReviewReport(
        benchmark_id=report.benchmark_id,
        ssot_answer=(
            "Core owns targeted scientific parsing and optimization, intelligence owns ranked follow-up judgment, and lab owns execution handoff and observed-outcome reconciliation."
        ),
        compatibility_answer=(
            "Compatibility packages may consume these artifacts, but they do not own benchmark truth, recommendation law, or lab handoff semantics."
        ),
        benchmarked_answer=(
            f"Benchmarked scope is {report.dataset_id} under {report.benchmark_id}, with explicit comparison notes that limit claims to checked-in targeted evidence and reviewable lab outputs."
        ),
        weak_answer=weak_answer,
    )


__all__ = [
    "TargetedExternalReviewReport",
    "TargetedFailureRehearsalReport",
    "TargetedOperatorRunReport",
    "build_targeted_external_review_report",
    "build_targeted_failure_rehearsal",
    "build_targeted_operator_run_report",
]
