# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references.workflows.benchmarks import KnowledgeWorkflowFamily
from bijux_proteomics_knowledge.references.workflows.narratives import WorkflowNarrativeKind
from bijux_proteomics_knowledge.references.workflows.lookups import (
    get_benchmark_manifest,
    get_workflow_narrative,
    list_benchmark_manifests,
    list_workflow_narratives,
)


def test_workflow_queries_return_known_reference_entries() -> None:
    assert (
        get_benchmark_manifest("benchmark:dia_library_extraction_consistency")
        is not None
    )
    assert get_workflow_narrative("narrative:dia_evidence_claim") is not None


def test_workflow_queries_support_workflow_and_kind_filters() -> None:
    assert all(
        manifest.workflow_family is KnowledgeWorkflowFamily.DIA
        for manifest in list_benchmark_manifests(
            workflow_family=KnowledgeWorkflowFamily.DIA
        )
    )
    assert all(
        narrative.workflow_family is KnowledgeWorkflowFamily.DIA
        and narrative.narrative_kind is WorkflowNarrativeKind.LIMITATION
        for narrative in list_workflow_narratives(
            workflow_family=KnowledgeWorkflowFamily.DIA,
            narrative_kind=WorkflowNarrativeKind.LIMITATION,
        )
    )


def test_workflow_queries_return_none_for_unknown_entries() -> None:
    assert get_benchmark_manifest("benchmark:missing") is None
    assert get_workflow_narrative("narrative:missing") is None
