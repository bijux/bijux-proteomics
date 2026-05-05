# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references.benchmarks import KnowledgeWorkflowFamily
from bijux_proteomics_knowledge.references.narratives import (
    DEFAULT_WORKFLOW_NARRATIVES,
    WorkflowNarrativeKind,
)


def test_workflow_narratives_cover_each_family_and_kind() -> None:
    coverage = {
        (narrative.workflow_family, narrative.narrative_kind)
        for narrative in DEFAULT_WORKFLOW_NARRATIVES
    }

    assert coverage == {
        (KnowledgeWorkflowFamily.DDA, WorkflowNarrativeKind.EVIDENCE_CLAIM),
        (KnowledgeWorkflowFamily.DDA, WorkflowNarrativeKind.LIMITATION),
        (KnowledgeWorkflowFamily.DIA, WorkflowNarrativeKind.EVIDENCE_CLAIM),
        (KnowledgeWorkflowFamily.DIA, WorkflowNarrativeKind.LIMITATION),
        (KnowledgeWorkflowFamily.PTM, WorkflowNarrativeKind.EVIDENCE_CLAIM),
        (KnowledgeWorkflowFamily.PTM, WorkflowNarrativeKind.LIMITATION),
        (KnowledgeWorkflowFamily.LFQ, WorkflowNarrativeKind.EVIDENCE_CLAIM),
        (KnowledgeWorkflowFamily.LFQ, WorkflowNarrativeKind.LIMITATION),
        (KnowledgeWorkflowFamily.MULTIPLEX, WorkflowNarrativeKind.EVIDENCE_CLAIM),
        (KnowledgeWorkflowFamily.MULTIPLEX, WorkflowNarrativeKind.LIMITATION),
        (KnowledgeWorkflowFamily.TARGETED, WorkflowNarrativeKind.EVIDENCE_CLAIM),
        (KnowledgeWorkflowFamily.TARGETED, WorkflowNarrativeKind.LIMITATION),
    }


def test_workflow_narratives_carry_benchmark_and_provenance_links() -> None:
    for narrative in DEFAULT_WORKFLOW_NARRATIVES:
        assert narrative.benchmark_ids
        assert narrative.citation_ids
        assert narrative.narrative_text
