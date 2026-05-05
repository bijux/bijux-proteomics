# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_knowledge.references.benchmarks import (
    DEFAULT_BENCHMARK_MANIFESTS,
    KnowledgeWorkflowFamily,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


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
        assert manifest.dataset_id
        assert manifest.dataset_locator
        assert manifest.primary_citation_ids
        assert manifest.corpus_ids
        assert manifest.instrument_profiles
        assert len(manifest.reproduction_requirements) >= 3
        assert manifest.comparison_notes
        assert manifest.success_metric
        assert manifest.result_claim


def test_benchmark_manifests_choose_exact_repo_datasets() -> None:
    for manifest in DEFAULT_BENCHMARK_MANIFESTS:
        dataset_path = REPO_ROOT / manifest.dataset_locator
        assert dataset_path.exists()


def test_benchmark_manifests_carry_explicit_comparison_scope() -> None:
    for manifest in DEFAULT_BENCHMARK_MANIFESTS:
        assert len(manifest.comparison_notes) >= 2
        assert any(
            token in note.lower()
            for note in manifest.comparison_notes
            for token in ("compare", "parity", "published", "scope")
        )
