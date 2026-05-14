# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Workflow evidence sufficiency rubrics for flagship benchmark families."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.serialization.json_contracts import JsonModel
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    BenchmarkEvidenceTier,
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.comparator_failures import (
    ComparatorClaimSupportState,
    build_benchmark_comparator_failure_report,
)
from bijux_proteomics_knowledge.references.workflows.contradiction_dossiers import (
    build_workflow_contradiction_dossier,
)
from bijux_proteomics_knowledge.references.workflows.reference_support import (
    get_benchmark_manifest_for_family,
    get_workflow_reference_briefing_for_family,
)
from bijux_proteomics_knowledge.references.workflows.scientific_release import (
    build_scientific_release_packet,
)


class WorkflowEvidenceTrustTier(StrEnum):
    """Trust tiers that a workflow family may or may not have earned."""

    INTERNALLY_COHERENT = "internally_coherent"
    BENCHMARK_BACKED = "benchmark_backed"
    EXTERNALLY_CROSS_CHECKED = "externally_cross_checked"
    DECISION_GRADE = "decision_grade"


class WorkflowEvidenceSufficiencyCheck(JsonModel):
    """One trust tier check with explicit current blockers."""

    model_config = ConfigDict(extra="forbid")

    tier: WorkflowEvidenceTrustTier
    satisfied: bool
    current_ceiling: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=1)
    supporting_refs: tuple[str, ...] = Field(default_factory=tuple)
    missing_requirements: tuple[str, ...] = Field(default_factory=tuple)


class WorkflowEvidenceSufficiencyRubric(JsonModel):
    """Evidence sufficiency rubric for one flagship workflow family."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    benchmark_id: str = Field(..., min_length=1)
    checks: tuple[WorkflowEvidenceSufficiencyCheck, ...] = Field(default_factory=tuple)
    current_authorized_tier: WorkflowEvidenceTrustTier
    note: str = Field(..., min_length=1)


def _internal_coherence_check(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowEvidenceSufficiencyCheck:
    manifest = get_benchmark_manifest_for_family(workflow_family)
    briefing = get_workflow_reference_briefing_for_family(workflow_family)
    dossier = build_workflow_contradiction_dossier(workflow_family)
    return WorkflowEvidenceSufficiencyCheck(
        tier=WorkflowEvidenceTrustTier.INTERNALLY_COHERENT,
        satisfied=True,
        current_ceiling="The workflow family has a benchmark manifest, a reference briefing, and an explicit contradiction dossier, so the repo at least describes one bounded scientific story coherently.",
        rationale="Internal coherence is earned only when benchmark, reading, and contradiction surfaces all exist together for the same workflow family.",
        supporting_refs=(
            manifest.benchmark_id,
            *tuple(group.group_id for group in briefing.literature_groups),
            *tuple(scenario.scenario_id for scenario in dossier.scenarios),
        ),
        missing_requirements=(),
    )


def _benchmark_backed_check(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowEvidenceSufficiencyCheck:
    manifest = get_benchmark_manifest_for_family(workflow_family)
    satisfied = manifest.evidence_tier in {
        BenchmarkEvidenceTier.CURATED_MINI_STUDY,
        BenchmarkEvidenceTier.PUBLIC_TRUTH_SET,
        BenchmarkEvidenceTier.EXTERNAL_REPRODUCTION_PACKAGE,
    }
    missing_requirements: tuple[str, ...] = ()
    if manifest.evidence_tier is BenchmarkEvidenceTier.CURATED_MINI_STUDY:
        missing_requirements = (
            "replace the current curated mini-study benchmark with a flagship public package that carries harder raw-data and cohort realism",
        )
    return WorkflowEvidenceSufficiencyCheck(
        tier=WorkflowEvidenceTrustTier.BENCHMARK_BACKED,
        satisfied=satisfied,
        current_ceiling=(
            "The workflow has benchmark-backed behavior only inside the documented fixture scope."
        ),
        rationale="Benchmark-backed means the workflow has a governed benchmark package and bounded scientific outcomes, even if the package is still too small for broad trust.",
        supporting_refs=(manifest.benchmark_id, *manifest.supported_repo_claims),
        missing_requirements=missing_requirements,
    )


def _externally_cross_checked_check(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowEvidenceSufficiencyCheck:
    manifest = get_benchmark_manifest_for_family(workflow_family)
    failure_report = build_benchmark_comparator_failure_report(
        workflow_family=workflow_family
    )
    entry = failure_report.entries[0] if failure_report.entries else None
    satisfied = bool(
        manifest.comparator_path_ids
        and entry is not None
        and entry.public_claim_support_state is not ComparatorClaimSupportState.REFUSED
    )
    missing_requirements = (
        (
            entry.improvement_target,
            *entry.blocking_reasons,
        )
        if entry is not None and not satisfied
        else ()
    )
    return WorkflowEvidenceSufficiencyCheck(
        tier=WorkflowEvidenceTrustTier.EXTERNALLY_CROSS_CHECKED,
        satisfied=satisfied,
        current_ceiling=(
            "External cross-checking only counts when a named comparator path exists and the comparison still leaves the workflow above a refused public-claim state."
        ),
        rationale="External confrontation must be visible enough that the workflow family can survive an outside-tool comparison without hiding known losses.",
        supporting_refs=(
            manifest.benchmark_id,
            *manifest.comparator_path_ids,
        ),
        missing_requirements=missing_requirements,
    )


def _decision_grade_check(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowEvidenceSufficiencyCheck:
    manifest = get_benchmark_manifest_for_family(workflow_family)
    briefing = get_workflow_reference_briefing_for_family(workflow_family)
    release_packet = build_scientific_release_packet(manifest)
    missing_requirements: tuple[str, ...] = ()
    if not release_packet.evidence_quality_gate_passed:
        missing_requirements = tuple(
            criterion.summary
            for criterion in briefing.decision_grade_framework.criteria
        )
    return WorkflowEvidenceSufficiencyCheck(
        tier=WorkflowEvidenceTrustTier.DECISION_GRADE,
        satisfied=release_packet.evidence_quality_gate_passed,
        current_ceiling=(
            "Decision-grade is earned only when the hostile-review gate, threshold anchors, outcome audits, and workflow-specific criteria all survive together."
        ),
        rationale=briefing.decision_grade_framework.decision_grade_definition,
        supporting_refs=(
            manifest.benchmark_id,
            *tuple(
                entry.threshold_id
                for entry in release_packet.threshold_evidence.entries
            ),
        ),
        missing_requirements=missing_requirements,
    )


def build_workflow_evidence_sufficiency_rubric(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowEvidenceSufficiencyRubric:
    """Build the workflow evidence sufficiency rubric for one family."""

    manifest = get_benchmark_manifest_for_family(workflow_family)
    checks = (
        _internal_coherence_check(workflow_family),
        _benchmark_backed_check(workflow_family),
        _externally_cross_checked_check(workflow_family),
        _decision_grade_check(workflow_family),
    )
    current_authorized_tier = next(
        check.tier for check in reversed(checks) if check.satisfied
    )
    return WorkflowEvidenceSufficiencyRubric(
        workflow_family=workflow_family,
        benchmark_id=manifest.benchmark_id,
        checks=checks,
        current_authorized_tier=current_authorized_tier,
        note=(
            "The rubric exists to stop stronger release wording from outrunning the exact tier of evidence the current benchmark family has actually earned."
        ),
    )


def list_workflow_evidence_sufficiency_rubrics() -> tuple[
    WorkflowEvidenceSufficiencyRubric, ...
]:
    """Return evidence sufficiency rubrics across workflow families."""

    return tuple(
        build_workflow_evidence_sufficiency_rubric(workflow_family)
        for workflow_family in KnowledgeWorkflowFamily
    )


__all__ = [
    "WorkflowEvidenceSufficiencyCheck",
    "WorkflowEvidenceSufficiencyRubric",
    "WorkflowEvidenceTrustTier",
    "build_workflow_evidence_sufficiency_rubric",
    "list_workflow_evidence_sufficiency_rubrics",
]
