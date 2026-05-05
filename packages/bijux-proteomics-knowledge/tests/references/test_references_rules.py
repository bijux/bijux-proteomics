# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references.benchmarks import KnowledgeWorkflowFamily
from bijux_proteomics_knowledge.references.rules import (
    DEFAULT_SCIENTIFIC_RULE_REFERENCES,
    GroundedDecisionRule,
    build_ranking_rule_grounding_ledger,
    RankingRuleGroundingLedger,
)
from bijux_proteomics_knowledge.references.rules import KnowledgeRuleDomain


def test_scientific_rule_registry_covers_needed_domains() -> None:
    domains = {rule.domain for rule in DEFAULT_SCIENTIFIC_RULE_REFERENCES}

    assert domains == {
        KnowledgeRuleDomain.ENZYME,
        KnowledgeRuleDomain.PTM_ASSUMPTION,
        KnowledgeRuleDomain.LABEL_CHEMISTRY,
        KnowledgeRuleDomain.FDR_CAVEAT,
        KnowledgeRuleDomain.INFERENCE_CAUTION,
    }


def test_scientific_rules_carry_references_and_benchmark_context() -> None:
    for rule in DEFAULT_SCIENTIFIC_RULE_REFERENCES:
        assert rule.version_trace
        assert rule.retrieval_trace
        assert rule.citation_ids
        assert rule.benchmark_ids
        assert rule.benchmark_rationale
        assert rule.rule_statement


def test_grounded_decision_rules_are_owned_by_knowledge_references() -> None:
    ledger = build_ranking_rule_grounding_ledger(KnowledgeWorkflowFamily.DIA)

    assert isinstance(ledger, RankingRuleGroundingLedger)
    assert ledger.rules
    assert all(isinstance(rule, GroundedDecisionRule) for rule in ledger.rules)
    assert {rule.rule_id for rule in ledger.rules} == {
        "rule:evidence_strength_priority",
        "rule:reproducibility_priority",
        "rule:freshness_penalty",
        "rule:contradiction_penalty",
        "rule:assay_feasibility_and_operational_risk_balance",
    }
