# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references import (
    BenchmarkComparatorFailureEntry,
    BenchmarkComparatorFailureReport,
    ComparatorClaimSupportState,
    ComparatorFailureSeverity,
    KnowledgeWorkflowFamily,
    build_benchmark_comparator_failure_report,
    get_benchmark_comparator_failure,
)


def test_comparator_failure_report_blocks_public_claims_without_external_comparison() -> (
    None
):
    report = build_benchmark_comparator_failure_report(
        workflow_family=KnowledgeWorkflowFamily.MULTIPLEX
    )

    assert isinstance(report, BenchmarkComparatorFailureReport)
    assert len(report.entries) == 1
    entry = report.entries[0]
    assert entry.workflow_family is KnowledgeWorkflowFamily.MULTIPLEX
    assert entry.public_claim_support_state is ComparatorClaimSupportState.REFUSED
    assert entry.severity is ComparatorFailureSeverity.RELEASE_BLOCKING
    assert "no external implementation or output-set comparison" in entry.blocking_reasons[0]


def test_comparator_failure_report_tracks_known_targeted_loss_dossier() -> None:
    entry = get_benchmark_comparator_failure(
        "benchmark:targeted_transition_quality_control"
    )

    assert isinstance(entry, BenchmarkComparatorFailureEntry)
    assert entry.known_loss_to_established_tool is True
    assert entry.public_claim_support_state is ComparatorClaimSupportState.ADVISORY
    assert "Skyline" in entry.improvement_target or "Skyline".lower() in entry.improvement_target.lower()


def test_comparator_failure_report_keeps_partial_external_paths_as_improvement_targets() -> (
    None
):
    entry = get_benchmark_comparator_failure("benchmark:dda_search_reproducibility")

    assert isinstance(entry, BenchmarkComparatorFailureEntry)
    assert entry.public_claim_support_state is ComparatorClaimSupportState.ADVISORY
    assert entry.severity is ComparatorFailureSeverity.IMPROVEMENT_TARGET
    assert entry.comparator_path_ids
