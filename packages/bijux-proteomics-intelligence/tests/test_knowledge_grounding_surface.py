# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references import (
    KnowledgeWorkflowFamily,
    WorkflowNarrativeKind,
    build_workflow_reference_briefing,
)
from bijux_proteomics_intelligence import build_ranking_rule_grounding_ledger


def test_intelligence_can_consume_knowledge_briefing_with_limitations() -> None:
    briefing = build_workflow_reference_briefing(KnowledgeWorkflowFamily.DIA)

    assert (
        briefing.evidence_claim.narrative_kind is WorkflowNarrativeKind.EVIDENCE_CLAIM
    )
    assert briefing.limitation.narrative_kind is WorkflowNarrativeKind.LIMITATION
    assert briefing.known_problems
    assert briefing.scientific_rules
    assert briefing.scientific_context


def test_intelligence_grounding_ledger_stays_tied_to_knowledge_briefings() -> None:
    ledger = build_ranking_rule_grounding_ledger(KnowledgeWorkflowFamily.DIA)

    assert ledger.workflow_family is KnowledgeWorkflowFamily.DIA
    assert ledger.rules
    assert all(rule.citation_ids for rule in ledger.rules)
    assert all(rule.benchmark_ids for rule in ledger.rules)
    assert any(rule.known_problem_ids for rule in ledger.rules)
