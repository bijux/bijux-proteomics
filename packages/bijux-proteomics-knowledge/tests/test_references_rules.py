# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references import (
    DEFAULT_SCIENTIFIC_RULE_REFERENCES,
    KnowledgeRuleDomain,
)


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
        assert rule.citation_ids
        assert rule.benchmark_ids
        assert rule.benchmark_rationale
        assert rule.rule_statement
