# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Read-only query helpers over workflow benchmark and narrative surfaces."""

from __future__ import annotations

from bijux_proteomics_knowledge.references.benchmarks import (
    BenchmarkManifest,
    DEFAULT_BENCHMARK_MANIFESTS,
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.narratives import (
    DEFAULT_WORKFLOW_NARRATIVES,
    WorkflowNarrative,
    WorkflowNarrativeKind,
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
    "get_benchmark_manifest",
    "get_workflow_narrative",
    "list_benchmark_manifests",
    "list_workflow_narratives",
]
