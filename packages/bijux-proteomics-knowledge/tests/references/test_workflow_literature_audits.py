# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.literature_audits import (
    GapDirection,
    LiteratureFreshnessState,
    build_benchmark_literature_gap_matrix,
    build_comparator_literature_gap_matrix,
    build_workflow_bibliography_export,
    build_workflow_literature_freshness_audit,
    list_workflow_literature_freshness_audits,
)


def test_workflow_literature_freshness_audits_cover_each_family() -> None:
    audits = list_workflow_literature_freshness_audits()

    assert {audit.workflow_family for audit in audits} == set(KnowledgeWorkflowFamily)


def test_workflow_literature_freshness_audit_tracks_last_checked_and_summary_posture() -> (
    None
):
    audit = build_workflow_literature_freshness_audit(KnowledgeWorkflowFamily.DDA)

    assert audit.entries
    assert all(entry.last_checked_on.startswith("20") for entry in audit.entries)
    assert all(entry.resolves_in_curated_audit for entry in audit.entries)
    assert any(
        entry.freshness_state
        in {
            LiteratureFreshnessState.CURRENT,
            LiteratureFreshnessState.CURATED_BUT_AGING,
        }
        for entry in audit.entries
    )


def test_workflow_bibliography_export_is_machine_readable_and_tagged() -> None:
    export = build_workflow_bibliography_export(KnowledgeWorkflowFamily.PTM)

    assert export.export_id == "workflow_bibliography:ptm"
    assert export.entries
    assert all(entry.relevance_tags for entry in export.entries)
    assert all(
        entry.freshness_state in set(LiteratureFreshnessState)
        for entry in export.entries
    )


def test_gap_matrices_keep_benchmark_and_comparator_tension_explicit() -> None:
    benchmark_gap_matrix = build_benchmark_literature_gap_matrix()
    comparator_gap_matrix = build_comparator_literature_gap_matrix()

    assert any(
        entry.direction
        in {
            GapDirection.BENCHMARK_OUTRUNS_LITERATURE,
            GapDirection.LITERATURE_OUTRUNS_BENCHMARK,
        }
        for entry in benchmark_gap_matrix.entries
    )
    assert any(
        entry.direction
        in {
            GapDirection.COMPARATOR_OUTRUNS_LITERATURE,
            GapDirection.LITERATURE_OUTRUNS_COMPARATOR,
        }
        for entry in comparator_gap_matrix.entries
    )
    assert "cross-family" in benchmark_gap_matrix.note
    assert "confrontations" in comparator_gap_matrix.note
