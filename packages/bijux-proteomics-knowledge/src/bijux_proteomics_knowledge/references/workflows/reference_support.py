# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Shared support helpers for composing workflow scientific reading surfaces."""

from __future__ import annotations

from bijux_proteomics_knowledge.references.grounding.citations import (
    DEFAULT_CITATION_REGISTRY,
    CitationRecord,
)
from bijux_proteomics_knowledge.references.grounding.literature import (
    DEFAULT_LITERATURE_GROUPS,
    LiteratureGroup,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    DEFAULT_BENCHMARK_MANIFESTS,
    BenchmarkManifest,
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.briefings import (
    WorkflowReferenceBriefing,
    build_workflow_reference_briefing,
)


def get_benchmark_manifest_for_family(
    workflow_family: KnowledgeWorkflowFamily,
) -> BenchmarkManifest:
    """Return the curated benchmark manifest for one workflow family."""

    return next(
        manifest
        for manifest in DEFAULT_BENCHMARK_MANIFESTS
        if manifest.workflow_family is workflow_family
    )


def get_workflow_reference_briefing_for_family(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowReferenceBriefing:
    """Return the curated reference briefing for one workflow family."""

    return build_workflow_reference_briefing(workflow_family)


def get_citation_record(citation_id: str) -> CitationRecord:
    """Return one curated citation record by stable identifier."""

    return next(
        record for record in DEFAULT_CITATION_REGISTRY if record.citation_id == citation_id
    )


def list_literature_groups_for_family(
    workflow_family: KnowledgeWorkflowFamily,
) -> tuple[LiteratureGroup, ...]:
    """Return literature groups that explicitly cover one workflow family."""

    benchmark_id = get_benchmark_manifest_for_family(workflow_family).benchmark_id
    return tuple(
        group for group in DEFAULT_LITERATURE_GROUPS if benchmark_id in group.benchmark_ids
    )


def get_literature_group(literature_group_id: str) -> LiteratureGroup:
    """Return one curated literature group by stable identifier."""

    return next(group for group in DEFAULT_LITERATURE_GROUPS if group.group_id == literature_group_id)


__all__ = [
    "get_benchmark_manifest_for_family",
    "get_citation_record",
    "get_literature_group",
    "get_workflow_reference_briefing_for_family",
    "list_literature_groups_for_family",
]
