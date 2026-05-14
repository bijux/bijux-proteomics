# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.reviews.public_scrutiny import (
    build_public_artifact_index,
    build_public_artifact_role_matrix,
)


def test_public_artifact_index_covers_repository_and_all_five_workflow_surfaces() -> (
    None
):
    index = build_public_artifact_index()

    assert index.index_id == "flagship-public-artifact-index"
    assert index.artifact_budget == 20
    assert len(index.entries) == 20
    assert any(
        entry.locator.endswith("flagship-release-candidate.md")
        for entry in index.entries
    )
    assert any(
        entry.locator.endswith("why-this-repository-is-not-ready-yet.md")
        for entry in index.entries
    )
    assert any(
        entry.locator.endswith("targeted_external_review_kit.json")
        for entry in index.entries
    )
    assert any(
        entry.question_answered.startswith("What should an outsider open")
        for entry in index.entries
    )


def test_public_artifact_role_matrix_names_distinct_neighbors() -> None:
    matrix = build_public_artifact_role_matrix()

    assert matrix.matrix_id == "public-artifact-role-matrix"
    assert matrix.doc_path.endswith("public-artifact-role-matrix.md")
    assert len(matrix.rows) == 20
    assert any(
        row.workflow_family is None
        and row.decision_role == "repository-challenge-route"
        for row in matrix.rows
    )
    assert any(
        row.workflow_family is not None
        and row.decision_role == "workflow-rerun-challenge"
        and row.stronger_neighbor is not None
        for row in matrix.rows
    )
