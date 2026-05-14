# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.judgment.benchmark_regret import (
    BenchmarkRecommendationRegretKind,
    build_benchmark_recommendation_regret_ledger,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)


def test_recommendation_regret_ledger_covers_five_flagship_families() -> None:
    ledger = build_benchmark_recommendation_regret_ledger()

    assert ledger.ledger_id == "flagship-benchmark-recommendation-regret"
    assert ledger.artifact_path.startswith("artifacts/")
    assert [entry.workflow_family for entry in ledger.entries] == [
        KnowledgeWorkflowFamily.DDA,
        KnowledgeWorkflowFamily.DIA,
        KnowledgeWorkflowFamily.LFQ,
        KnowledgeWorkflowFamily.PTM,
        KnowledgeWorkflowFamily.TARGETED,
    ]


def test_recommendation_regret_ledger_prioritizes_hidden_miss_when_present() -> None:
    ledger = build_benchmark_recommendation_regret_ledger()

    targeted = next(
        entry
        for entry in ledger.entries
        if entry.workflow_family is KnowledgeWorkflowFamily.TARGETED
    )
    assert targeted.regret_kind is BenchmarkRecommendationRegretKind.HIDDEN_REVEAL_MISS
    assert any(
        ref.endswith("interference-carryover-follow-up")
        for ref in targeted.evidence_refs
    )
