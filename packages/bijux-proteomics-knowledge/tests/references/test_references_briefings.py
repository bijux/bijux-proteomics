# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references.workflows.benchmarks import KnowledgeWorkflowFamily
from bijux_proteomics_knowledge.references.workflows.briefings import (
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
    assert briefing.scope_limit_notes
    assert set(briefing.evidence_claim.scope_limit_notes).issubset(
        briefing.scope_limit_notes
    )
    assert set(briefing.limitation.scope_limit_notes).issubset(
        briefing.scope_limit_notes
    )
