# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references.workflows.benchmark_ledger import (
    build_workflow_benchmark_ledger,
    build_workflow_benchmark_ledger_entry,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    DEFAULT_BENCHMARK_MANIFESTS,
)


def test_benchmark_ledger_entry_keeps_provenance_truth_and_limits_together() -> None:
    manifest = DEFAULT_BENCHMARK_MANIFESTS[0]
    entry = build_workflow_benchmark_ledger_entry(manifest)

    assert entry.benchmark_id == manifest.benchmark_id
    assert entry.truth_surfaces == manifest.truth_surfaces
    assert entry.truth_assumptions == manifest.reproduction_requirements
    assert entry.provenance_trace
    assert entry.caveat_lines
    assert entry.consumer_facing_limits
    assert entry.supported_repo_claims == manifest.supported_repo_claims


def test_benchmark_ledger_covers_all_curated_benchmarks() -> None:
    ledger = build_workflow_benchmark_ledger()

    assert len(ledger.entries) == len(DEFAULT_BENCHMARK_MANIFESTS)
    assert {entry.benchmark_id for entry in ledger.entries} == {
        manifest.benchmark_id for manifest in DEFAULT_BENCHMARK_MANIFESTS
    }
