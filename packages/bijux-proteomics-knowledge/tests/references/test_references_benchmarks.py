# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    BenchmarkCrossCheckStatus,
    BenchmarkEvidenceTier,
    DEFAULT_BENCHMARK_MANIFESTS,
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.registry import (
    BenchmarkAuthorityStatus,
    build_benchmark_registry,
)

REPO_ROOT = Path(__file__).resolve().parents[4]


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
        assert manifest.evidence_tier in {
            BenchmarkEvidenceTier.SMOKE_FIXTURE,
            BenchmarkEvidenceTier.CURATED_MINI_STUDY,
            BenchmarkEvidenceTier.PUBLIC_TRUTH_SET,
            BenchmarkEvidenceTier.EXTERNAL_REPRODUCTION_PACKAGE,
        }
        assert manifest.dataset_id
        assert manifest.dataset_locator
        assert manifest.organism
        assert manifest.sample_complexity
        assert manifest.label_strategy
        assert manifest.sample_count >= 1
        assert manifest.replicate_count >= 1
        assert manifest.truth_surfaces
        assert manifest.primary_citation_ids
        assert manifest.corpus_ids
        assert manifest.cross_check_status in {
            BenchmarkCrossCheckStatus.INTERNAL_ONLY,
            BenchmarkCrossCheckStatus.EXTERNAL_OUTPUT_COMPARISON,
        }
        assert manifest.cross_check_note
        assert manifest.version_trace
        assert manifest.retrieval_trace
        assert manifest.dataset_license_and_reuse_note
        assert manifest.instrument_profiles
        assert len(manifest.reproduction_requirements) >= 3
        assert manifest.comparison_notes
        assert manifest.exclusion_notes
        assert manifest.weakness_notes
        assert manifest.fixture_realism_limits
        assert manifest.failure_mode_notes
        assert manifest.expected_failure_conditions
        assert manifest.non_transfer_zones
        assert manifest.supported_repo_claims
        assert manifest.last_reviewed_on.isoformat()
        assert manifest.freshness_window_days >= 1
        assert manifest.obsolescence_conditions
        assert manifest.retirement_conditions
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


def test_benchmark_manifests_carry_explicit_exclusions_weaknesses_and_failures() -> (
    None
):
    for manifest in DEFAULT_BENCHMARK_MANIFESTS:
        assert len(manifest.exclusion_notes) >= 2
        assert len(manifest.weakness_notes) >= 2
        assert len(manifest.failure_mode_notes) >= 2
        assert any("excludes" in note.lower() for note in manifest.exclusion_notes)
        assert any(
            "fixture" in note.lower() or "production" in note.lower()
            for note in manifest.weakness_notes
        )
        assert any("can" in note.lower() for note in manifest.failure_mode_notes)


def test_benchmark_manifests_carry_exact_scope_transfer_and_staleness_metadata() -> (
    None
):
    for manifest in DEFAULT_BENCHMARK_MANIFESTS:
        assert manifest.sample_count >= manifest.replicate_count
        assert len(manifest.supported_repo_claims) >= 2
        assert len(manifest.fixture_realism_limits) >= 2
        assert len(manifest.truth_surfaces) >= 3
        assert len(manifest.expected_failure_conditions) >= 2
        assert len(manifest.non_transfer_zones) >= 2
        assert len(manifest.obsolescence_conditions) >= 2
        assert len(manifest.retirement_conditions) >= 2
        assert any(
            token in note.lower()
            for note in manifest.non_transfer_zones
            for token in (
                "fixture",
                "outside",
                "vendor",
                "parity",
                "unseen",
                "cohort",
                "claims",
            )
        )


def test_benchmark_registry_reports_exact_claim_scope_and_bounded_authority() -> None:
    registry = build_benchmark_registry()

    assert len(registry.entries) == len(DEFAULT_BENCHMARK_MANIFESTS)
    for entry in registry.entries:
        assert entry.supported_repo_claims
        assert entry.authorized_claim_scope
        assert entry.realism_limits
        assert entry.authority_status in {
            BenchmarkAuthorityStatus.ACTIVE,
            BenchmarkAuthorityStatus.REVIEW_DUE,
            BenchmarkAuthorityStatus.RETIRED,
        }
        if entry.evidence_tier is BenchmarkEvidenceTier.CURATED_MINI_STUDY:
            assert any(
                "bounded workflow semantics" in line
                for line in entry.authorized_claim_scope
            )
