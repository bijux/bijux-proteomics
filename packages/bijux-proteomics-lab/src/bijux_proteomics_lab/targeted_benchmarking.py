# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Benchmark-backed targeted follow-up reports for operator-facing lab review."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.dia import (
    TargetedAssayOptimizationCandidate,
    TargetedAssayOptimizationReport,
    optimize_targeted_assay_candidates,
)
from bijux_proteomics.io.ingestion import ChromatogramQcIngestionReport
from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_intelligence.briefs import CandidateAssessment
from bijux_proteomics_intelligence.decision_paths import FollowUpCandidatePath
from bijux_proteomics_knowledge.references import (
    BenchmarkManifest,
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_lab.handoffs import LimsExportBundle, TargetedTransitionReview
from bijux_proteomics_lab.reconciliation import OperationalFollowUpPath


class TargetedBenchmarkClaimSupport(StrEnum):
    """Support tier for one benchmarked targeted-workflow claim."""

    STRONG_SUPPORT = "strong_support"
    PARTIAL_SUPPORT = "partial_support"
    UNSUPPORTED = "unsupported"


class TargetedBenchmarkClaimSummary(JsonModel):
    """One benchmark claim with explicit support posture and diagnostics."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(..., min_length=1)
    support: TargetedBenchmarkClaimSupport
    summary: str = Field(..., min_length=1)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    diagnostics: tuple[str, ...] = Field(default_factory=tuple)


class TargetedBenchmarkReport(JsonModel):
    """Benchmark-backed path from discovery evidence to lab-facing targeted outputs."""

    model_config = ConfigDict(extra="forbid")

    benchmark_id: str = Field(..., min_length=1)
    dataset_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    recommended_candidate_id: str = Field(..., min_length=1)
    optimization_report: TargetedAssayOptimizationReport
    follow_up_path: FollowUpCandidatePath
    transition_review: TargetedTransitionReview
    lims_export_bundle: LimsExportBundle
    operational_path: OperationalFollowUpPath
    claim_summaries: tuple[TargetedBenchmarkClaimSummary, ...] = Field(
        default_factory=tuple
    )
    overall_support: TargetedBenchmarkClaimSupport
    comparison_notes: tuple[str, ...] = Field(default_factory=tuple)
    diagnostics: tuple[str, ...] = Field(default_factory=tuple)


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


def _candidate_reference_set(
    assessments: tuple[CandidateAssessment, ...],
) -> tuple[TargetedAssayOptimizationCandidate, ...]:
    return tuple(
        TargetedAssayOptimizationCandidate(
            candidate_id=assessment.candidate_id,
            peptide_sequence=assessment.sequence,
            uniqueness_score=assessment.evidence_support,
            detectability_score=assessment.assay_feasibility_score,
            ptm_ambiguity_penalty=assessment.uncertainty,
            qc_score=assessment.reproducibility_score,
        )
        for assessment in assessments
    )


def _support_rank(support: TargetedBenchmarkClaimSupport) -> int:
    order = {
        TargetedBenchmarkClaimSupport.STRONG_SUPPORT: 0,
        TargetedBenchmarkClaimSupport.PARTIAL_SUPPORT: 1,
        TargetedBenchmarkClaimSupport.UNSUPPORTED: 2,
    }
    return order[support]


def _overall_support(
    claim_summaries: tuple[TargetedBenchmarkClaimSummary, ...],
) -> TargetedBenchmarkClaimSupport:
    if any(
        summary.support is TargetedBenchmarkClaimSupport.UNSUPPORTED
        for summary in claim_summaries
    ):
        return TargetedBenchmarkClaimSupport.UNSUPPORTED
    if any(
        summary.support is TargetedBenchmarkClaimSupport.PARTIAL_SUPPORT
        for summary in claim_summaries
    ):
        return TargetedBenchmarkClaimSupport.PARTIAL_SUPPORT
    return TargetedBenchmarkClaimSupport.STRONG_SUPPORT


def build_targeted_benchmark_report(
    *,
    benchmark_manifest: BenchmarkManifest,
    candidate_assessments: tuple[CandidateAssessment, ...],
    follow_up_path: FollowUpCandidatePath,
    chromatogram_report: ChromatogramQcIngestionReport,
    transition_review: TargetedTransitionReview,
    lims_export_bundle: LimsExportBundle,
    operational_path: OperationalFollowUpPath,
    cache_age_days: int | None = None,
    strong_cache_window_days: int = 30,
    degraded_cache_window_days: int = 90,
) -> TargetedBenchmarkReport:
    """Build a benchmark report from discovery evidence to lab-facing targeted outputs."""
    if benchmark_manifest.workflow_family is not KnowledgeWorkflowFamily.TARGETED:
        raise ValueError(
            "targeted benchmark reports require a targeted workflow manifest"
        )
    if not follow_up_path.recommendations:
        raise ValueError("follow-up path must include at least one recommendation")

    recommended_candidate_id = follow_up_path.recommendations[0].candidate_id
    optimization_report = optimize_targeted_assay_candidates(
        _candidate_reference_set(candidate_assessments)
    )

    if follow_up_path.decision_ready:
        discovery_claim = TargetedBenchmarkClaimSummary(
            claim_id="discovery_ranking",
            support=TargetedBenchmarkClaimSupport.STRONG_SUPPORT,
            summary="discovery evidence supports a ranked targeted follow-up candidate",
            evidence_refs=(follow_up_path.program_id, recommended_candidate_id),
            diagnostics=tuple(follow_up_path.unresolved_questions[:3]),
        )
    else:
        discovery_claim = TargetedBenchmarkClaimSummary(
            claim_id="discovery_ranking",
            support=TargetedBenchmarkClaimSupport.PARTIAL_SUPPORT,
            summary="discovery evidence ranks a targeted follow-up candidate but still carries explicit blockers",
            evidence_refs=(follow_up_path.program_id, recommended_candidate_id),
            diagnostics=tuple(follow_up_path.unresolved_questions[:3]),
        )

    if (
        chromatogram_report.accepted_points
        and chromatogram_report.failed_metric_rows == 0
    ):
        qc_support = (
            TargetedBenchmarkClaimSupport.STRONG_SUPPORT
            if chromatogram_report.unknown_metric_rows == 0
            else TargetedBenchmarkClaimSupport.PARTIAL_SUPPORT
        )
        qc_summary = (
            "chromatogram QC preserves transition-level evidence without malformed rows"
            if qc_support is TargetedBenchmarkClaimSupport.STRONG_SUPPORT
            else "chromatogram QC preserves usable transition-level evidence but still contains unknown metrics"
        )
    else:
        qc_support = TargetedBenchmarkClaimSupport.UNSUPPORTED
        qc_summary = "chromatogram QC cannot support a strong targeted claim because malformed rows remain"
    qc_claim = TargetedBenchmarkClaimSummary(
        claim_id="chromatogram_qc",
        support=qc_support,
        summary=qc_summary,
        evidence_refs=(benchmark_manifest.dataset_id,),
        diagnostics=(
            f"accepted_points={len(chromatogram_report.accepted_points)}",
            f"unknown_metric_rows={chromatogram_report.unknown_metric_rows}",
            f"failed_metric_rows={chromatogram_report.failed_metric_rows}",
        ),
    )

    if operational_path.refusal is not None:
        handoff_support = TargetedBenchmarkClaimSupport.UNSUPPORTED
        handoff_summary = "lab handoff is explicitly refused because the targeted follow-up is not responsible to run"
    elif (
        transition_review.approved_transition_ids
        and operational_path.execution_request.ready_for_lab_review
    ):
        handoff_support = TargetedBenchmarkClaimSupport.STRONG_SUPPORT
        handoff_summary = (
            "targeted transition evidence is strong enough for responsible lab handoff"
        )
    else:
        handoff_support = TargetedBenchmarkClaimSupport.PARTIAL_SUPPORT
        handoff_summary = "targeted transition evidence remains exploratory even though a handoff packet can be reviewed"
    handoff_claim = TargetedBenchmarkClaimSummary(
        claim_id="lab_handoff",
        support=handoff_support,
        summary=handoff_summary,
        evidence_refs=(
            lims_export_bundle.bundle_id,
            operational_path.execution_request.batch_id,
        ),
        diagnostics=(operational_path.explanation.summary,),
    )

    blocked_feedback = (
        operational_path.reconciliation.intelligence_feedback.blocked_assay_ids
    )
    weakened_feedback = (
        operational_path.reconciliation.intelligence_feedback.weakened_assay_ids
    )
    if not operational_path.reconciliation.ready_for_feedback:
        feedback_support = TargetedBenchmarkClaimSupport.UNSUPPORTED
        feedback_summary = "observed outcomes cannot feed back honestly because the reconciliation still has lineage or execution gaps"
    elif blocked_feedback or weakened_feedback:
        feedback_support = TargetedBenchmarkClaimSupport.PARTIAL_SUPPORT
        feedback_summary = "observed outcomes feed back into review, but they only support a downgraded or mixed targeted claim"
    else:
        feedback_support = TargetedBenchmarkClaimSupport.STRONG_SUPPORT
        feedback_summary = "observed outcomes feed back into downstream review without unresolved execution gaps"
    feedback_claim = TargetedBenchmarkClaimSummary(
        claim_id="observed_feedback",
        support=feedback_support,
        summary=feedback_summary,
        evidence_refs=(operational_path.reconciliation.batch_id,),
        diagnostics=(
            operational_path.reconciliation.intelligence_feedback.recommended_action,
        ),
    )

    if cache_age_days is None or cache_age_days <= strong_cache_window_days:
        cache_support = TargetedBenchmarkClaimSupport.STRONG_SUPPORT
        cache_summary = "cached benchmark inputs are fresh enough for strong support"
    elif cache_age_days <= degraded_cache_window_days:
        cache_support = TargetedBenchmarkClaimSupport.PARTIAL_SUPPORT
        cache_summary = "cached benchmark inputs remain usable but should be refreshed before stronger support is claimed"
    else:
        cache_support = TargetedBenchmarkClaimSupport.UNSUPPORTED
        cache_summary = (
            "cached benchmark inputs are too stale for a strong targeted claim"
        )
    cache_claim = TargetedBenchmarkClaimSummary(
        claim_id="cache_freshness",
        support=cache_support,
        summary=cache_summary,
        evidence_refs=(benchmark_manifest.dataset_id,),
        diagnostics=(f"cache_age_days={cache_age_days or 0}",),
    )

    claim_summaries = tuple(
        sorted(
            (
                discovery_claim,
                qc_claim,
                handoff_claim,
                feedback_claim,
                cache_claim,
            ),
            key=lambda summary: (_support_rank(summary.support), summary.claim_id),
        )
    )
    overall_support = _overall_support(claim_summaries)

    return TargetedBenchmarkReport(
        benchmark_id=benchmark_manifest.benchmark_id,
        dataset_id=benchmark_manifest.dataset_id,
        workflow_family=benchmark_manifest.workflow_family,
        recommended_candidate_id=recommended_candidate_id,
        optimization_report=optimization_report,
        follow_up_path=follow_up_path,
        transition_review=transition_review,
        lims_export_bundle=lims_export_bundle,
        operational_path=operational_path,
        claim_summaries=claim_summaries,
        overall_support=overall_support,
        comparison_notes=benchmark_manifest.comparison_notes,
        diagnostics=(
            benchmark_manifest.result_claim,
            benchmark_manifest.success_metric,
            *benchmark_manifest.comparison_notes,
        ),
    )


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
    "TargetedBenchmarkClaimSupport",
    "TargetedBenchmarkClaimSummary",
    "TargetedExternalReviewReport",
    "TargetedFailureRehearsalReport",
    "TargetedBenchmarkReport",
    "TargetedOperatorRunReport",
    "build_targeted_benchmark_report",
    "build_targeted_external_review_report",
    "build_targeted_failure_rehearsal",
    "build_targeted_operator_run_report",
]
