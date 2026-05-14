# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.literature_matrices import (
    build_workflow_literature_matrix,
    list_workflow_literature_matrices,
)


def test_workflow_literature_matrices_cover_each_family() -> None:
    matrices = list_workflow_literature_matrices()

    assert {matrix.workflow_family for matrix in matrices} == set(
        KnowledgeWorkflowFamily
    )


def test_workflow_literature_matrix_keeps_supported_and_bounded_claims_together() -> (
    None
):
    matrix = build_workflow_literature_matrix(KnowledgeWorkflowFamily.DIA)

    assert matrix.benchmark_id == "benchmark:dia_library_extraction_consistency"
    assert matrix.entries
    assert all(entry.citation_ids for entry in matrix.entries)
    assert all(entry.citation_titles for entry in matrix.entries)
    assert all(entry.supported_claims for entry in matrix.entries)
    assert all(entry.bounded_claims for entry in matrix.entries)
    assert all(entry.reviewer_questions for entry in matrix.entries)
    assert "bounded claim" in matrix.coverage_note.lower()


def test_workflow_literature_matrix_tracks_targeted_and_ptm_limitations_explicitly() -> (
    None
):
    targeted = build_workflow_literature_matrix(KnowledgeWorkflowFamily.TARGETED)
    ptm = build_workflow_literature_matrix(KnowledgeWorkflowFamily.PTM)

    assert any(
        "vendor-parity targeted biology" in claim
        for entry in targeted.entries
        for claim in entry.bounded_claims
    )
    assert any(
        "mechanistic" in claim
        for entry in ptm.entries
        for claim in entry.bounded_claims
    )
