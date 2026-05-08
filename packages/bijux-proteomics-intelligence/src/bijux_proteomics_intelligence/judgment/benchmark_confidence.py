# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Confidence audits over blinded and counterfactual recommendation evidence."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_intelligence.judgment.benchmark_blinded_challenges import (
    BlindedRecommendationRevealState,
    list_workflow_blinded_recommendation_challenges,
)
from bijux_proteomics_intelligence.judgment.benchmark_counterfactuals import (
    CounterfactualRecommendationEntry,
    build_counterfactual_recommendation_report,
)
from bijux_proteomics_intelligence.judgment.benchmark_corpora import (
    BenchmarkDisposition,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)

__all__ = [
    "WorkflowOverconfidenceAudit",
    "WorkflowOverconfidenceAuditEntry",
    "WorkflowUnderconfidenceAudit",
    "WorkflowUnderconfidenceAuditEntry",
    "build_workflow_overconfidence_audit",
    "build_workflow_underconfidence_audit",
]


class WorkflowOverconfidenceAuditEntry(JsonModel):
    """One family-level overconfidence score tied to hidden evidence reveals."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    baseline_disposition: BenchmarkDisposition
    overconfidence_rate: float = Field(..., ge=0.0, le=1.0)
    overconfidence_finding_ids: tuple[str, ...] = Field(default_factory=tuple)
    counterfactual_refusal_count: int = Field(..., ge=0, le=3)
    certainty_ahead_of_evidence: bool
    note: str = Field(..., min_length=1)


class WorkflowOverconfidenceAudit(JsonModel):
    """Cross-family audit of stronger-than-earned intelligence certainty."""

    model_config = ConfigDict(extra="forbid")

    audit_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    entries: tuple[WorkflowOverconfidenceAuditEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class WorkflowUnderconfidenceAuditEntry(JsonModel):
    """One family-level score for unnecessary refusal or weakening."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    baseline_disposition: BenchmarkDisposition
    underconfidence_rate: float = Field(..., ge=0.0, le=1.0)
    underconfidence_finding_ids: tuple[str, ...] = Field(default_factory=tuple)
    unnecessarily_weakened: bool
    note: str = Field(..., min_length=1)


class WorkflowUnderconfidenceAudit(JsonModel):
    """Cross-family audit of caution that hindsight does not justify."""

    model_config = ConfigDict(extra="forbid")

    audit_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    entries: tuple[WorkflowUnderconfidenceAuditEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


def _counterfactuals_by_family() -> dict[KnowledgeWorkflowFamily, CounterfactualRecommendationEntry]:
    return {
        entry.workflow_family: entry
        for entry in build_counterfactual_recommendation_report().entries
    }


def _counterfactual_refusal_count(entry: CounterfactualRecommendationEntry) -> int:
    return sum(
        disposition is BenchmarkDisposition.DO_NOT_RECOMMEND
        for disposition in (
            entry.without_comparator_disposition,
            entry.without_literature_disposition,
            entry.doubled_lab_burden_disposition,
        )
    )


def build_workflow_overconfidence_audit() -> WorkflowOverconfidenceAudit:
    """Score how often current intelligence certainty still runs ahead of evidence."""

    counterfactuals = _counterfactuals_by_family()
    entries: list[WorkflowOverconfidenceAuditEntry] = []
    for report in list_workflow_blinded_recommendation_challenges():
        flagged = tuple(
            finding.finding_id
            for finding in report.findings
            if finding.revealed_outcome
            in {
                BlindedRecommendationRevealState.OVERCONFIDENT,
                BlindedRecommendationRevealState.MISS,
            }
        )
        total = max(len(report.findings), 1)
        counterfactual = counterfactuals[report.workflow_family]
        refusal_count = _counterfactual_refusal_count(counterfactual)
        entries.append(
            WorkflowOverconfidenceAuditEntry(
                workflow_family=report.workflow_family,
                baseline_disposition=next(
                    finding.chosen_disposition for finding in report.findings
                ),
                overconfidence_rate=len(flagged) / total,
                overconfidence_finding_ids=flagged,
                counterfactual_refusal_count=refusal_count,
                certainty_ahead_of_evidence=bool(flagged) or refusal_count >= 2,
                note=(
                    "Hidden evidence still shows confidence running ahead of proof for this family."
                    if flagged
                    else "No direct hidden-evidence overconfidence was observed for this family."
                ),
            )
        )
    return WorkflowOverconfidenceAudit(
        audit_id="flagship-workflow-overconfidence-audit",
        artifact_path="artifacts/intelligence/benchmark-decisions/workflow_overconfidence_audit.json",
        entries=tuple(entries),
        note=(
            "This audit scores how often the shipped intelligence posture sounds stronger "
            "than blinded challenge results and counterfactual evidence removal justify."
        ),
    )


def build_workflow_underconfidence_audit() -> WorkflowUnderconfidenceAudit:
    """Score how often hindsight shows the current posture was too cautious."""

    counterfactuals = _counterfactuals_by_family()
    entries: list[WorkflowUnderconfidenceAuditEntry] = []
    for report in list_workflow_blinded_recommendation_challenges():
        flagged = tuple(
            finding.finding_id
            for finding in report.findings
            if finding.revealed_outcome is BlindedRecommendationRevealState.UNDERCONFIDENT
        )
        total = max(len(report.findings), 1)
        counterfactual = counterfactuals[report.workflow_family]
        unnecessarily_weakened = (
            bool(flagged)
            or (
                next(finding.chosen_disposition for finding in report.findings)
                is BenchmarkDisposition.DO_NOT_RECOMMEND
                and report.hit_count == len(report.findings)
                and _counterfactual_refusal_count(counterfactual) == 0
            )
        )
        entries.append(
            WorkflowUnderconfidenceAuditEntry(
                workflow_family=report.workflow_family,
                baseline_disposition=next(
                    finding.chosen_disposition for finding in report.findings
                ),
                underconfidence_rate=len(flagged) / total,
                underconfidence_finding_ids=flagged,
                unnecessarily_weakened=unnecessarily_weakened,
                note=(
                    "No clear hindsight-backed underconfidence is visible because each family still carries open evidence debt that justifies caution."
                    if not unnecessarily_weakened
                    else "Hindsight shows this family was kept weaker than the evidence justified."
                ),
            )
        )
    return WorkflowUnderconfidenceAudit(
        audit_id="flagship-workflow-underconfidence-audit",
        artifact_path="artifacts/intelligence/benchmark-decisions/workflow_underconfidence_audit.json",
        entries=tuple(entries),
        note=(
            "This audit scores how often the shipped intelligence posture refuses or "
            "weakens recommendations that hidden evidence later shows were sufficiently supported."
        ),
    )
