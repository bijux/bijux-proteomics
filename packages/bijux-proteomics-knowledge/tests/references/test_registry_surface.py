# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from datetime import date

from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    BenchmarkManifest,
    DEFAULT_BENCHMARK_MANIFESTS,
)
from bijux_proteomics_knowledge.references.workflows.registry import (
    BenchmarkAuthorityStatus,
    assess_benchmark_authority,
    build_benchmark_registry_entry,
)


def test_build_benchmark_registry_entry_carries_dataset_shape_and_claims() -> None:
    manifest = DEFAULT_BENCHMARK_MANIFESTS[0]
    entry = build_benchmark_registry_entry(manifest, reviewed_on=date(2026, 5, 6))

    assert entry.benchmark_id == manifest.benchmark_id
    assert entry.dataset_id == manifest.dataset_id
    assert entry.sample_complexity == manifest.sample_complexity
    assert entry.organism == manifest.organism
    assert entry.label_strategy == manifest.label_strategy
    assert entry.supported_repo_claims == manifest.supported_repo_claims
    assert entry.realism_limits == manifest.fixture_realism_limits


def test_assess_benchmark_authority_marks_stale_fixture_reports_review_due() -> None:
    manifest = DEFAULT_BENCHMARK_MANIFESTS[0].model_copy(
        update={"last_reviewed_on": date(2025, 1, 1)}
    )

    authority = assess_benchmark_authority(manifest, reviewed_on=date(2026, 5, 6))

    assert authority.authority_status is BenchmarkAuthorityStatus.REVIEW_DUE
    assert authority.blocking_reasons


def test_assess_benchmark_authority_retirements_are_explicit() -> None:
    manifest = DEFAULT_BENCHMARK_MANIFESTS[0]

    authority = assess_benchmark_authority(
        manifest,
        reviewed_on=date(2026, 5, 6),
        triggered_retirement_conditions=(
            "adapter support widened beyond the curated fixture tier",
        ),
    )

    assert authority.authority_status is BenchmarkAuthorityStatus.RETIRED
    assert "adapter support widened" in authority.blocking_reasons[0]
