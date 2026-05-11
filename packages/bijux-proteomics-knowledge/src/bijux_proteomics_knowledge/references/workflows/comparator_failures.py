# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Failure and improvement-target surfaces for external comparator pressure."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.serialization.json_contracts import JsonModel
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    DEFAULT_BENCHMARK_MANIFESTS,
    BenchmarkCrossCheckStatus,
    BenchmarkManifest,
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.comparators import (
    ComparatorBehaviorStatus,
    ProteomicsComparatorTool,
    list_workflow_comparator_paths,
)


class ComparatorClaimSupportState(StrEnum):
    """Release-facing workflow-claim posture under comparator pressure."""

    ADVISORY = "advisory"
    REFUSED = "refused"
    SUPPORTED = "supported"


class ComparatorFailureSeverity(StrEnum):
    """Severity for comparator failures and improvement targets."""

    IMPROVEMENT_TARGET = "improvement_target"
    RELEASE_BLOCKING = "release_blocking"


class BenchmarkComparatorFailureEntry(JsonModel):
    """One benchmark-facing comparator failure or known weakness dossier."""

    model_config = ConfigDict(extra="forbid")

    benchmark_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    comparator_tool: ProteomicsComparatorTool
    severity: ComparatorFailureSeverity
    public_claim_support_state: ComparatorClaimSupportState
    comparator_path_ids: tuple[str, ...] = Field(default_factory=tuple)
    known_loss_to_established_tool: bool = False
    failure_summary: str = Field(..., min_length=1)
    blocking_reasons: tuple[str, ...] = Field(default_factory=tuple)
    improvement_target: str = Field(..., min_length=1)


class BenchmarkComparatorFailureReport(JsonModel):
    """Comparator failure dossier across benchmark families."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[BenchmarkComparatorFailureEntry, ...] = Field(default_factory=tuple)


def _default_comparator_tool(
    workflow_family: KnowledgeWorkflowFamily,
) -> ProteomicsComparatorTool:
    if workflow_family is KnowledgeWorkflowFamily.DDA:
        return ProteomicsComparatorTool.MSFRAGGER
    if workflow_family is KnowledgeWorkflowFamily.DIA:
        return ProteomicsComparatorTool.SPECTRONAUT
    if workflow_family in {
        KnowledgeWorkflowFamily.LFQ,
        KnowledgeWorkflowFamily.MULTIPLEX,
        KnowledgeWorkflowFamily.PTM,
    }:
        return ProteomicsComparatorTool.MAXQUANT
    return ProteomicsComparatorTool.SKYLINE


def _improvement_target_for_manifest(manifest: BenchmarkManifest) -> str:
    targets = {
        KnowledgeWorkflowFamily.DDA: "add live-engine replay or stronger external DDA output comparison so claim trust does not stop at pinned export normalization",
        KnowledgeWorkflowFamily.DIA: "expand DIA comparator pressure beyond checked-in reports so library and vendor drift can change release posture explicitly",
        KnowledgeWorkflowFamily.PTM: "add stronger rescoring or external PTM comparator evidence so localization trust is not limited to imported tables",
        KnowledgeWorkflowFamily.LFQ: "add stronger external quant comparator pressure so repeatability and effect-size claims are not inferred from fixture stability alone",
        KnowledgeWorkflowFamily.MULTIPLEX: "add an external multiplex comparator path with vendor-grade interference and reference-channel pressure",
        KnowledgeWorkflowFamily.TARGETED: "build a raw-to-reviewed targeted comparator against Skyline-class chromatogram workflows so targeted support stops losing on calibration and interference realism",
    }
    return targets[manifest.workflow_family]


def _entry_for_missing_external_comparison(
    manifest: BenchmarkManifest,
) -> BenchmarkComparatorFailureEntry:
    return BenchmarkComparatorFailureEntry(
        benchmark_id=manifest.benchmark_id,
        workflow_family=manifest.workflow_family,
        comparator_tool=_default_comparator_tool(manifest.workflow_family),
        severity=ComparatorFailureSeverity.RELEASE_BLOCKING,
        public_claim_support_state=ComparatorClaimSupportState.REFUSED,
        comparator_path_ids=(),
        known_loss_to_established_tool=(
            manifest.workflow_family is KnowledgeWorkflowFamily.TARGETED
        ),
        failure_summary=(
            "this benchmark has no external comparator path, so release-facing workflow support claims stay refused"
        ),
        blocking_reasons=(
            "no external implementation or output-set comparison is linked to this workflow family",
            "public claim trust would otherwise depend only on internal self-consistency",
        ),
        improvement_target=_improvement_target_for_manifest(manifest),
    )


def _entry_for_comparator_drift(
    manifest: BenchmarkManifest,
) -> BenchmarkComparatorFailureEntry | None:
    paths = list_workflow_comparator_paths(benchmark_id=manifest.benchmark_id)
    if not paths:
        return _entry_for_missing_external_comparison(manifest)
    partial = tuple(
        claim.summary
        for path in paths
        for claim in path.comparison_behaviors
        if claim.status is ComparatorBehaviorStatus.PARTIAL
    )
    refused = tuple(
        claim.summary
        for path in paths
        for claim in path.comparison_behaviors
        if claim.status is ComparatorBehaviorStatus.REFUSES
    )
    not_attempted = tuple(
        claim.summary
        for path in paths
        for claim in path.comparison_behaviors
        if claim.status is ComparatorBehaviorStatus.DOES_NOT_ATTEMPT
    )
    if not (partial or refused or not_attempted):
        return None
    blocking_reasons = (*partial, *refused, *not_attempted)
    severity = (
        ComparatorFailureSeverity.RELEASE_BLOCKING
        if manifest.cross_check_status is BenchmarkCrossCheckStatus.INTERNAL_ONLY
        else ComparatorFailureSeverity.IMPROVEMENT_TARGET
    )
    claim_state = (
        ComparatorClaimSupportState.REFUSED
        if severity is ComparatorFailureSeverity.RELEASE_BLOCKING
        else ComparatorClaimSupportState.ADVISORY
    )
    return BenchmarkComparatorFailureEntry(
        benchmark_id=manifest.benchmark_id,
        workflow_family=manifest.workflow_family,
        comparator_tool=paths[0].comparator_tool,
        severity=severity,
        public_claim_support_state=claim_state,
        comparator_path_ids=tuple(path.comparator_path_id for path in paths),
        known_loss_to_established_tool=(
            manifest.workflow_family is KnowledgeWorkflowFamily.TARGETED
        ),
        failure_summary=(
            "comparator drift or missing external execution parity still materially limits this public workflow claim"
        ),
        blocking_reasons=blocking_reasons,
        improvement_target=_improvement_target_for_manifest(manifest),
    )


def build_benchmark_comparator_failure_report(
    *,
    workflow_family: KnowledgeWorkflowFamily | None = None,
    benchmark_id: str | None = None,
) -> BenchmarkComparatorFailureReport:
    """Build the comparator-failure dossier for benchmark-backed workflow claims."""

    manifests = tuple(
        manifest
        for manifest in DEFAULT_BENCHMARK_MANIFESTS
        if (workflow_family is None or manifest.workflow_family is workflow_family)
        and (benchmark_id is None or manifest.benchmark_id == benchmark_id)
    )
    entries = tuple(
        entry
        for entry in (_entry_for_comparator_drift(manifest) for manifest in manifests)
        if entry is not None
    )
    return BenchmarkComparatorFailureReport(entries=entries)


__all__ = [
    "BenchmarkComparatorFailureEntry",
    "BenchmarkComparatorFailureReport",
    "ComparatorClaimSupportState",
    "ComparatorFailureSeverity",
    "build_benchmark_comparator_failure_report",
]
