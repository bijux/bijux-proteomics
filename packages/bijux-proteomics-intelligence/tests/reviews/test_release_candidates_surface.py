# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.reviews.release_candidates import (
    build_elite_readiness_scorecard,
    build_flagship_release_candidate_bundle,
    build_flagship_workflow_distrust_pages,
    build_flagship_workflow_trust_pages,
)
from bijux_proteomics_intelligence.reviews.workflow_authority import (
    WorkflowAuthorityKind,
    build_workflow_authority_matrix,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)


def test_flagship_workflow_trust_pages_cover_all_five_flagship_families() -> None:
    pages = build_flagship_workflow_trust_pages()

    assert tuple(page.workflow_family for page in pages) == (
        KnowledgeWorkflowFamily.DDA,
        KnowledgeWorkflowFamily.DIA,
        KnowledgeWorkflowFamily.LFQ,
        KnowledgeWorkflowFamily.PTM,
        KnowledgeWorkflowFamily.TARGETED,
    )
    assert all(
        page.doc_path.endswith(f"why-trust-{page.workflow_family.value}.md")
        for page in pages
    )


def test_flagship_workflow_distrust_pages_cover_only_incomplete_families() -> None:
    pages = build_flagship_workflow_distrust_pages()

    assert pages == ()


def test_release_candidate_bundle_names_current_outsider_auditable_and_internal_support_families() -> (
    None
):
    bundle = build_flagship_release_candidate_bundle()

    assert bundle.bundle_id == "flagship-release-candidate-bundle"
    assert bundle.strongest_workflow_family is KnowledgeWorkflowFamily.DDA
    assert bundle.outsider_auditable_workflow_families == (
        KnowledgeWorkflowFamily.DDA,
        KnowledgeWorkflowFamily.DIA,
        KnowledgeWorkflowFamily.PTM,
        KnowledgeWorkflowFamily.TARGETED,
    )
    assert bundle.internal_support_workflow_families == (
        KnowledgeWorkflowFamily.MULTIPLEX,
    )
    assert bundle.blocked_workflow_families == ()
    assert bundle.workflow_authority_matrix_path.endswith(
        "workflow_authority_matrix.json"
    )
    assert "flagship_follow_up_outcome:dda" in bundle.lab_outcome_dossier_ids
    assert "flagship_follow_up_outcome:targeted" in bundle.lab_outcome_dossier_ids
    assert "independent_rerun:dda" in bundle.independent_rerun_dossier_ids
    assert "independent_rerun:targeted" in bundle.independent_rerun_dossier_ids
    assert any(
        path.endswith("dda_independent_rerun_dossier.json")
        for path in bundle.independent_rerun_dossier_paths
    )
    assert "external_review_kit:dda" in bundle.external_review_kit_ids
    assert "external_review_kit:targeted" in bundle.external_review_kit_ids
    assert any(
        path.endswith("dia_external_review_kit.json")
        for path in bundle.external_review_kit_paths
    )
    assert (
        "docs/01-bijux-proteomics/foundation/why-trust-dda.md"
        in bundle.trust_page_paths
    )
    assert (
        "docs/01-bijux-proteomics/foundation/why-trust-dia.md"
        in bundle.trust_page_paths
    )


def test_elite_readiness_scorecard_uses_public_substance_only_and_keeps_repo_language_blocked() -> (
    None
):
    scorecard = build_elite_readiness_scorecard()
    entries = {entry.workflow_family: entry for entry in scorecard.entries}

    assert scorecard.repository_elite_language_allowed is False
    assert "governance" not in " ".join(scorecard.scoring_basis).lower()
    assert "doc-count" in scorecard.note
    assert entries[KnowledgeWorkflowFamily.DDA].outsider_auditable_surface is True
    assert entries[KnowledgeWorkflowFamily.DIA].outsider_auditable_surface is True
    assert entries[KnowledgeWorkflowFamily.LFQ].outsider_auditable_surface is False
    assert entries[KnowledgeWorkflowFamily.PTM].outsider_auditable_surface is True
    assert entries[KnowledgeWorkflowFamily.TARGETED].outsider_auditable_surface is True
    assert (
        entries[KnowledgeWorkflowFamily.DDA].overall_score
        < entries[KnowledgeWorkflowFamily.DIA].overall_score
    )
    assert entries[KnowledgeWorkflowFamily.PTM].elite_language_allowed is False


def test_workflow_authority_matrix_covers_all_six_workflow_families() -> None:
    matrix = build_workflow_authority_matrix()
    rows = {row.workflow_family: row for row in matrix.rows}

    assert tuple(rows) == (
        KnowledgeWorkflowFamily.DDA,
        KnowledgeWorkflowFamily.DIA,
        KnowledgeWorkflowFamily.LFQ,
        KnowledgeWorkflowFamily.MULTIPLEX,
        KnowledgeWorkflowFamily.PTM,
        KnowledgeWorkflowFamily.TARGETED,
    )
    assert (
        rows[KnowledgeWorkflowFamily.MULTIPLEX].public_release_language
        == "internal_support_only"
    )
    assert (
        next(
            cell
            for cell in rows[KnowledgeWorkflowFamily.DIA].cells
            if cell.authority_kind == WorkflowAuthorityKind.RAW_EXECUTABLE
        ).earned
        is True
    )
    assert (
        next(
            cell
            for cell in rows[KnowledgeWorkflowFamily.TARGETED].cells
            if cell.authority_kind == WorkflowAuthorityKind.OUTSIDER_AUDITABLE
        ).earned
        is True
    )
    assert (
        next(
            cell
            for cell in rows[KnowledgeWorkflowFamily.PTM].cells
            if cell.authority_kind == WorkflowAuthorityKind.LAB_CONSEQUENTIAL
        ).earned
        is True
    )
    assert (
        next(
            cell
            for cell in rows[KnowledgeWorkflowFamily.MULTIPLEX].cells
            if cell.authority_kind == WorkflowAuthorityKind.OUTSIDER_AUDITABLE
        ).earned
        is False
    )
