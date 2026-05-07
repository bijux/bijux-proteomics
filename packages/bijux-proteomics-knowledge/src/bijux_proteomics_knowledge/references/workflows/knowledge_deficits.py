# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Workflow-family knowledge deficit reports for flagship benchmark packages."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.serialization.json_contracts import JsonModel
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    BenchmarkEvidenceTier,
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.comparator_failures import (
    ComparatorFailureSeverity,
    build_benchmark_comparator_failure_report,
)
from bijux_proteomics_knowledge.references.workflows.reference_support import (
    get_benchmark_manifest_for_family,
    get_workflow_reference_briefing_for_family,
)


class KnowledgeDeficitSeverity(StrEnum):
    """Severity for a remaining scientific-base gap."""

    MATERIAL = "material"
    HIGH = "high"
    RELEASE_BLOCKING = "release_blocking"


class WorkflowKnowledgeDeficitItem(JsonModel):
    """One explicit gap that still limits the current scientific base."""

    model_config = ConfigDict(extra="forbid")

    deficit_id: str = Field(..., min_length=1)
    severity: KnowledgeDeficitSeverity
    summary: str = Field(..., min_length=1)
    why_it_matters: str = Field(..., min_length=1)
    closure_condition: str = Field(..., min_length=1)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)


class WorkflowKnowledgeDeficitReport(JsonModel):
    """Current knowledge deficits for one flagship workflow family."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    benchmark_id: str = Field(..., min_length=1)
    public_data_gaps: tuple[WorkflowKnowledgeDeficitItem, ...] = Field(
        default_factory=tuple
    )
    comparator_gaps: tuple[WorkflowKnowledgeDeficitItem, ...] = Field(
        default_factory=tuple
    )
    literature_gaps: tuple[WorkflowKnowledgeDeficitItem, ...] = Field(
        default_factory=tuple
    )
    runtime_proof_gaps: tuple[WorkflowKnowledgeDeficitItem, ...] = Field(
        default_factory=tuple
    )
    highest_severity: KnowledgeDeficitSeverity
    note: str = Field(..., min_length=1)


def _public_data_gaps(
    workflow_family: KnowledgeWorkflowFamily,
) -> tuple[WorkflowKnowledgeDeficitItem, ...]:
    manifest = get_benchmark_manifest_for_family(workflow_family)
    if manifest.evidence_tier is not BenchmarkEvidenceTier.CURATED_MINI_STUDY:
        return ()
    return (
        WorkflowKnowledgeDeficitItem(
            deficit_id=f"knowledge_deficit:{workflow_family.value}:public_data",
            severity=KnowledgeDeficitSeverity.HIGH,
            summary="the current benchmark family is still anchored in a curated mini-study rather than a flagship public benchmark package",
            why_it_matters="The repo can describe bounded behavior, but it still cannot point to the harder raw-data identity and realism expected from an outsider-auditable flagship package.",
            closure_condition="Replace the current curated package with a flagship public benchmark package that carries real raw-data identity, richer sample structure, and harder scientific pressure.",
            evidence_refs=(manifest.benchmark_id, *manifest.fixture_realism_limits),
        ),
    )


def _comparator_gaps(
    workflow_family: KnowledgeWorkflowFamily,
) -> tuple[WorkflowKnowledgeDeficitItem, ...]:
    manifest = get_benchmark_manifest_for_family(workflow_family)
    report = build_benchmark_comparator_failure_report(workflow_family=workflow_family)
    if not report.entries:
        return ()
    entry = report.entries[0]
    severity = (
        KnowledgeDeficitSeverity.RELEASE_BLOCKING
        if entry.severity is ComparatorFailureSeverity.RELEASE_BLOCKING
        else KnowledgeDeficitSeverity.HIGH
    )
    return (
        WorkflowKnowledgeDeficitItem(
            deficit_id=f"knowledge_deficit:{workflow_family.value}:comparator",
            severity=severity,
            summary=entry.failure_summary,
            why_it_matters="Without visible comparator confrontation, the knowledge layer risks becoming a self-consistent explanation surface instead of an externally pressured scientific base.",
            closure_condition=entry.improvement_target,
            evidence_refs=(manifest.benchmark_id, *entry.comparator_path_ids, *entry.blocking_reasons),
        ),
    )


def _literature_gaps(
    workflow_family: KnowledgeWorkflowFamily,
) -> tuple[WorkflowKnowledgeDeficitItem, ...]:
    manifest = get_benchmark_manifest_for_family(workflow_family)
    briefing = get_workflow_reference_briefing_for_family(workflow_family)
    unique_citations = {
        citation_id
        for group in briefing.literature_groups
        for citation_id in group.citation_ids
    }
    if len(unique_citations) >= 4 and len(briefing.literature_groups) >= 3:
        return ()
    return (
        WorkflowKnowledgeDeficitItem(
            deficit_id=f"knowledge_deficit:{workflow_family.value}:literature",
            severity=KnowledgeDeficitSeverity.MATERIAL,
            summary="the curated literature base is still narrow relative to the scientific surface this workflow family wants to support",
            why_it_matters="A workflow can look well-explained in code while still being under-curated in the literature it claims to honor, especially when only one or two citation anchors dominate the whole family.",
            closure_condition="Add broader paper coverage, contradiction-specific citations, and workflow-specific reading anchors until the family is not leaning on one small citation cluster.",
            evidence_refs=(manifest.benchmark_id, *tuple(group.group_id for group in briefing.literature_groups), *tuple(sorted(unique_citations))),
        ),
    )


def _runtime_proof_gaps(
    workflow_family: KnowledgeWorkflowFamily,
) -> tuple[WorkflowKnowledgeDeficitItem, ...]:
    manifest = get_benchmark_manifest_for_family(workflow_family)
    package = manifest.benchmark_package
    if package is None:
        return (
            WorkflowKnowledgeDeficitItem(
                deficit_id=f"knowledge_deficit:{workflow_family.value}:runtime_proof",
                severity=KnowledgeDeficitSeverity.RELEASE_BLOCKING,
                summary="the workflow family still lacks a benchmark package with explicit reproduction steps",
                why_it_matters="Without a real benchmark package, the knowledge surface cannot point to a runtime-shaped proof path at all.",
                closure_condition="Create a benchmark package with governed artifacts and reviewable reproduction steps.",
                evidence_refs=(manifest.benchmark_id,),
            ),
        )
    outside_repo_steps = tuple(
        step.step_id for step in package.reproduction_steps if step.outside_repo_execution
    )
    if not outside_repo_steps:
        return ()
    return (
        WorkflowKnowledgeDeficitItem(
            deficit_id=f"knowledge_deficit:{workflow_family.value}:runtime_proof",
            severity=KnowledgeDeficitSeverity.HIGH,
            summary="the current reproduction story still depends on execution steps that remain outside the repository proof boundary",
            why_it_matters="The knowledge layer can describe the workflow precisely, but it still cannot claim fully repo-contained runtime proof while key reproduction steps live elsewhere.",
            closure_condition="Replace the outside-repo execution steps with a tracked in-repo run or a stronger governed import bundle that outsiders can inspect as real proof.",
            evidence_refs=(manifest.benchmark_id, *outside_repo_steps),
        ),
    )


def _highest_severity(
    report: WorkflowKnowledgeDeficitReport,
) -> KnowledgeDeficitSeverity:
    severities = {
        item.severity
        for items in (
            report.public_data_gaps,
            report.comparator_gaps,
            report.literature_gaps,
            report.runtime_proof_gaps,
        )
        for item in items
    }
    if KnowledgeDeficitSeverity.RELEASE_BLOCKING in severities:
        return KnowledgeDeficitSeverity.RELEASE_BLOCKING
    if KnowledgeDeficitSeverity.HIGH in severities:
        return KnowledgeDeficitSeverity.HIGH
    return KnowledgeDeficitSeverity.MATERIAL


def build_workflow_knowledge_deficit_report(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowKnowledgeDeficitReport:
    """Build the workflow knowledge deficit report for one family."""

    manifest = get_benchmark_manifest_for_family(workflow_family)
    draft = WorkflowKnowledgeDeficitReport(
        workflow_family=workflow_family,
        benchmark_id=manifest.benchmark_id,
        public_data_gaps=_public_data_gaps(workflow_family),
        comparator_gaps=_comparator_gaps(workflow_family),
        literature_gaps=_literature_gaps(workflow_family),
        runtime_proof_gaps=_runtime_proof_gaps(workflow_family),
        highest_severity=KnowledgeDeficitSeverity.MATERIAL,
        note=(
            "The deficit report exists to keep every workflow family honest about the scientific base it still lacks, not just the positive evidence it already has."
        ),
    )
    return draft.model_copy(update={"highest_severity": _highest_severity(draft)})


def list_workflow_knowledge_deficit_reports() -> (
    tuple[WorkflowKnowledgeDeficitReport, ...]
):
    """Return knowledge deficit reports across workflow families."""

    return tuple(
        build_workflow_knowledge_deficit_report(workflow_family)
        for workflow_family in KnowledgeWorkflowFamily
    )


__all__ = [
    "KnowledgeDeficitSeverity",
    "WorkflowKnowledgeDeficitItem",
    "WorkflowKnowledgeDeficitReport",
    "build_workflow_knowledge_deficit_report",
    "list_workflow_knowledge_deficit_reports",
]
