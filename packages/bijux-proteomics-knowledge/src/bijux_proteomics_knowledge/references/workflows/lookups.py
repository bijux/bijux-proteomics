# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Read-only query helpers over workflow benchmark and narrative surfaces."""

from __future__ import annotations

from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    DEFAULT_BENCHMARK_MANIFESTS,
    BenchmarkManifest,
    BenchmarkPackageArtifact,
    BenchmarkPackageArtifactKind,
    BenchmarkReproductionStep,
    KnowledgeWorkflowFamily,
    WorkflowBenchmarkPackage,
)
from bijux_proteomics_knowledge.references.workflows.comparator_failures import (
    BenchmarkComparatorFailureEntry,
    BenchmarkComparatorFailureReport,
    ComparatorClaimSupportState,
    ComparatorFailureSeverity,
    build_benchmark_comparator_failure_report,
)
from bijux_proteomics_knowledge.references.workflows.comparators import (
    WorkflowComparatorMatrixEntry,
    WorkflowComparatorMatrixReport,
    WorkflowComparatorPath,
    build_workflow_comparator_matrix,
    get_workflow_comparator_path,
    list_workflow_comparator_paths,
)
from bijux_proteomics_knowledge.references.workflows.narratives import (
    DEFAULT_WORKFLOW_NARRATIVES,
    WorkflowNarrative,
    WorkflowNarrativeKind,
)
from bijux_proteomics_knowledge.references.workflows.registry import (
    BenchmarkRegistryEntry,
    BenchmarkRegistryReport,
    build_benchmark_registry,
    build_benchmark_registry_entry,
)


def list_benchmark_manifests(
    *, workflow_family: KnowledgeWorkflowFamily | None = None
) -> tuple[BenchmarkManifest, ...]:
    """Return curated benchmark manifests, optionally filtered by workflow family."""

    if workflow_family is None:
        return DEFAULT_BENCHMARK_MANIFESTS
    return tuple(
        manifest
        for manifest in DEFAULT_BENCHMARK_MANIFESTS
        if manifest.workflow_family is workflow_family
    )


def get_benchmark_manifest(benchmark_id: str) -> BenchmarkManifest | None:
    """Return one benchmark manifest by stable identifier."""

    return next(
        (
            manifest
            for manifest in DEFAULT_BENCHMARK_MANIFESTS
            if manifest.benchmark_id == benchmark_id
        ),
        None,
    )


def get_benchmark_package(benchmark_id: str) -> WorkflowBenchmarkPackage | None:
    """Return the promoted benchmark package for one benchmark when available."""

    manifest = get_benchmark_manifest(benchmark_id)
    if manifest is None:
        return None
    return manifest.benchmark_package


def list_benchmark_comparator_failures(
    *,
    workflow_family: KnowledgeWorkflowFamily | None = None,
) -> tuple[BenchmarkComparatorFailureEntry, ...]:
    """Return benchmark comparator failures filtered by workflow family."""

    return build_benchmark_comparator_failure_report(
        workflow_family=workflow_family
    ).entries


def get_benchmark_comparator_failure(
    benchmark_id: str,
) -> BenchmarkComparatorFailureEntry | None:
    """Return one benchmark comparator failure dossier by benchmark identifier."""

    report = build_benchmark_comparator_failure_report(benchmark_id=benchmark_id)
    return report.entries[0] if report.entries else None


def list_benchmark_registry_entries(
    *, workflow_family: KnowledgeWorkflowFamily | None = None
) -> tuple[BenchmarkRegistryEntry, ...]:
    """Return public benchmark registry entries with authority posture."""

    return build_benchmark_registry(workflow_family=workflow_family).entries


def get_benchmark_registry_entry(benchmark_id: str) -> BenchmarkRegistryEntry | None:
    """Return one public benchmark registry entry by stable benchmark identifier."""

    manifest = get_benchmark_manifest(benchmark_id)
    if manifest is None:
        return None
    return build_benchmark_registry_entry(manifest)


def list_workflow_narratives(
    *,
    workflow_family: KnowledgeWorkflowFamily | None = None,
    narrative_kind: WorkflowNarrativeKind | None = None,
) -> tuple[WorkflowNarrative, ...]:
    """Return curated workflow narratives with optional workflow and kind filters."""

    return tuple(
        narrative
        for narrative in DEFAULT_WORKFLOW_NARRATIVES
        if (workflow_family is None or narrative.workflow_family is workflow_family)
        and (narrative_kind is None or narrative.narrative_kind is narrative_kind)
    )


def get_workflow_narrative(narrative_id: str) -> WorkflowNarrative | None:
    """Return one workflow narrative by stable identifier."""

    return next(
        (
            narrative
            for narrative in DEFAULT_WORKFLOW_NARRATIVES
            if narrative.narrative_id == narrative_id
        ),
        None,
    )


__all__ = [
    "BenchmarkPackageArtifact",
    "BenchmarkPackageArtifactKind",
    "BenchmarkReproductionStep",
    "BenchmarkComparatorFailureEntry",
    "BenchmarkComparatorFailureReport",
    "ComparatorClaimSupportState",
    "ComparatorFailureSeverity",
    "build_benchmark_comparator_failure_report",
    "get_benchmark_comparator_failure",
    "get_benchmark_manifest",
    "get_benchmark_package",
    "get_benchmark_registry_entry",
    "get_workflow_comparator_path",
    "get_workflow_narrative",
    "list_benchmark_comparator_failures",
    "list_workflow_comparator_paths",
    "build_workflow_comparator_matrix",
    "list_benchmark_registry_entries",
    "list_benchmark_manifests",
    "list_workflow_narratives",
    "BenchmarkRegistryEntry",
    "BenchmarkRegistryReport",
    "WorkflowBenchmarkPackage",
    "WorkflowComparatorMatrixEntry",
    "WorkflowComparatorMatrixReport",
    "WorkflowComparatorPath",
]
