# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references.problems import (
    DEFAULT_KNOWN_PROBLEM_REGISTRY,
    KnowledgeProblemKind,
)


def test_known_problem_registry_tracks_toy_corpora_and_shortcuts() -> None:
    problem_kinds = {entry.problem_kind for entry in DEFAULT_KNOWN_PROBLEM_REGISTRY}

    assert problem_kinds == {
        KnowledgeProblemKind.MISLEADING_TOY_CORPUS,
        KnowledgeProblemKind.WEAK_BENCHMARK_SHORTCUT,
    }


def test_known_problem_entries_link_workflows_and_mitigations() -> None:
    for entry in DEFAULT_KNOWN_PROBLEM_REGISTRY:
        assert entry.version_trace
        assert entry.retrieval_trace
        assert entry.affected_workflow_families
        assert entry.affected_benchmark_ids
        assert entry.problem_summary
        assert entry.mitigation_guidance
