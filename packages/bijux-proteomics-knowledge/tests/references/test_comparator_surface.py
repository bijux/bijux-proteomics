# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    DEFAULT_BENCHMARK_MANIFESTS,
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.comparators import (
    DEFAULT_WORKFLOW_COMPARATOR_PATHS,
    ComparatorBehaviorStatus,
    ProteomicsComparatorTool,
    build_workflow_comparator_matrix,
    get_workflow_comparator_path,
    list_workflow_comparator_paths,
)

REPO_ROOT = Path(__file__).resolve().parents[4]


def test_comparator_paths_keep_fixture_snapshots_and_link_known_benchmarks() -> None:
    benchmark_ids = {manifest.benchmark_id for manifest in DEFAULT_BENCHMARK_MANIFESTS}

    for path in DEFAULT_WORKFLOW_COMPARATOR_PATHS:
        assert set(path.benchmark_ids).issubset(benchmark_ids)
        assert path.workflow_families
        assert path.owned_surfaces
        assert len(path.comparison_behaviors) >= 3
        assert path.non_goals
        for fixture_path in path.fixture_paths:
            assert (REPO_ROOT / fixture_path).exists()


def test_comparator_path_lookup_filters_by_workflow_family_and_benchmark() -> None:
    dia_paths = list_workflow_comparator_paths(
        workflow_family=KnowledgeWorkflowFamily.DIA
    )
    maxquant_path = get_workflow_comparator_path(
        "comparator_path:maxquant_evidence_import_contracts"
    )

    assert {path.comparator_tool for path in dia_paths} == {
        ProteomicsComparatorTool.DIANN,
        ProteomicsComparatorTool.SPECTRONAUT,
    }
    assert maxquant_path is not None
    assert maxquant_path.benchmark_ids == (
        "benchmark:dda_search_reproducibility",
        "benchmark:lfq_quantification_repeatability",
        "benchmark:ptm_site_localization_confidence",
    )


def test_comparator_matrix_keeps_match_partial_refusal_and_non_attempt_scopes() -> None:
    matrix = build_workflow_comparator_matrix()

    assert len(matrix.entries) == len(KnowledgeWorkflowFamily)
    targeted_entry = next(
        entry
        for entry in matrix.entries
        if entry.workflow_family is KnowledgeWorkflowFamily.TARGETED
    )
    targeted_skyline = next(
        status
        for status in targeted_entry.tool_statuses
        if status.comparator_tool is ProteomicsComparatorTool.SKYLINE
    )
    assert targeted_skyline.matched_behaviors
    assert targeted_skyline.not_attempted_behaviors

    dia_entry = next(
        entry
        for entry in matrix.entries
        if entry.workflow_family is KnowledgeWorkflowFamily.DIA
    )
    assert any(
        status.matched_behaviors and status.partial_behaviors
        for status in dia_entry.tool_statuses
    )


def test_comparator_paths_keep_exact_behavior_status_values() -> None:
    valid_statuses = set(ComparatorBehaviorStatus)

    for path in DEFAULT_WORKFLOW_COMPARATOR_PATHS:
        assert {
            behavior.status for behavior in path.comparison_behaviors
        }.issubset(valid_statuses)
