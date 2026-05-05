# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references import (
    KnowledgeWorkflowFamily,
    build_workflow_reference_briefing,
    list_workflow_reference_briefings,
)


def test_workflow_reference_briefings_cover_each_family() -> None:
    workflow_families = {
        briefing.workflow_family for briefing in list_workflow_reference_briefings()
    }

    assert workflow_families == set(KnowledgeWorkflowFamily)


def test_workflow_reference_briefing_keeps_provenance_visible() -> None:
    briefing = build_workflow_reference_briefing(KnowledgeWorkflowFamily.DIA)

    assert (
        briefing.benchmark_manifest.benchmark_id
        == "benchmark:dia_library_extraction_consistency"
    )
    assert briefing.evidence_claim.citation_ids
    assert briefing.limitation.citation_ids
    assert briefing.scientific_context
    assert briefing.literature_groups
    assert briefing.scientific_rules
