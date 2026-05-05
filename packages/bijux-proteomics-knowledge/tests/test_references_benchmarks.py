# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references import (
    DEFAULT_BENCHMARK_MANIFESTS,
    KnowledgeWorkflowFamily,
)


def test_benchmark_manifests_cover_each_workflow_family() -> None:
    workflow_families = {
        manifest.workflow_family for manifest in DEFAULT_BENCHMARK_MANIFESTS
    }

    assert workflow_families == {
        KnowledgeWorkflowFamily.DDA,
        KnowledgeWorkflowFamily.DIA,
        KnowledgeWorkflowFamily.PTM,
        KnowledgeWorkflowFamily.LFQ,
        KnowledgeWorkflowFamily.MULTIPLEX,
        KnowledgeWorkflowFamily.TARGETED,
    }


def test_benchmark_manifests_carry_reproducibility_inputs() -> None:
    for manifest in DEFAULT_BENCHMARK_MANIFESTS:
        assert manifest.primary_citation_ids
        assert manifest.corpus_ids
        assert manifest.instrument_profiles
        assert len(manifest.reproduction_requirements) >= 3
        assert manifest.success_metric
        assert manifest.result_claim
