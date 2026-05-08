# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.scientific_reading_packs import (
    build_workflow_scientific_reading_pack,
    list_workflow_scientific_reading_packs,
)


def test_workflow_scientific_reading_packs_cover_each_family() -> None:
    packs = list_workflow_scientific_reading_packs()

    assert {pack.workflow_family for pack in packs} == set(KnowledgeWorkflowFamily)


def test_workflow_scientific_reading_pack_composes_all_scientific_base_surfaces() -> (
    None
):
    pack = build_workflow_scientific_reading_pack(KnowledgeWorkflowFamily.PTM)

    assert pack.claim_citation_table.entries
    assert pack.literature_matrix.entries
    assert pack.literature_freshness_audit.entries
    assert pack.bibliography_export.entries
    assert pack.contradiction_dossier.scenarios
    assert pack.contradiction_triage.entries
    assert pack.evidence_sufficiency_rubric.checks
    assert pack.deficit_report.literature_gaps
    assert pack.unsupported_claim_ledger.entries
    assert pack.reading_sequence
    assert pack.citation_digest


def test_workflow_scientific_reading_pack_keeps_outsider_questions_visible() -> None:
    pack = build_workflow_scientific_reading_pack(KnowledgeWorkflowFamily.TARGETED)

    assert pack.outsider_questions
    assert any("calibration" in question or "Decision-facing targeted support" in question for question in pack.outsider_questions)
    assert "public scientific base" in pack.note
