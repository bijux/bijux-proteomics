# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.reviews.release_candidates import (
    build_elite_readiness_scorecard,
    build_flagship_release_candidate_bundle,
    build_flagship_workflow_distrust_pages,
    build_flagship_workflow_trust_pages,
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
    assert all(page.doc_path.endswith(f"why-trust-{page.workflow_family.value}.md") for page in pages)


def test_flagship_workflow_distrust_pages_cover_only_incomplete_families() -> None:
    pages = build_flagship_workflow_distrust_pages()

    assert {page.workflow_family for page in pages} == {
        KnowledgeWorkflowFamily.DIA,
        KnowledgeWorkflowFamily.LFQ,
        KnowledgeWorkflowFamily.PTM,
        KnowledgeWorkflowFamily.TARGETED,
    }
    assert all(page.missing_reasons for page in pages)
    assert all(page.closure_steps for page in pages)


def test_release_candidate_bundle_names_current_outsider_auditable_family() -> None:
    bundle = build_flagship_release_candidate_bundle()

    assert bundle.bundle_id == "flagship-release-candidate-bundle"
    assert bundle.strongest_workflow_family is KnowledgeWorkflowFamily.DDA
    assert bundle.outsider_auditable_workflow_families == (
        KnowledgeWorkflowFamily.DDA,
    )
    assert KnowledgeWorkflowFamily.DIA in bundle.blocked_workflow_families
    assert "docs/01-bijux-proteomics/foundation/why-trust-dda.md" in bundle.trust_page_paths
    assert "docs/01-bijux-proteomics/foundation/why-not-trust-dia-yet.md" in bundle.distrust_page_paths


def test_elite_readiness_scorecard_uses_public_substance_only_and_keeps_repo_language_blocked() -> None:
    scorecard = build_elite_readiness_scorecard()
    entries = {entry.workflow_family: entry for entry in scorecard.entries}

    assert scorecard.repository_elite_language_allowed is False
    assert "governance" not in " ".join(scorecard.scoring_basis).lower()
    assert "doc-count" in scorecard.note
    assert entries[KnowledgeWorkflowFamily.DDA].outsider_auditable_surface is True
    assert entries[KnowledgeWorkflowFamily.DDA].overall_score > entries[KnowledgeWorkflowFamily.DIA].overall_score
    assert entries[KnowledgeWorkflowFamily.PTM].elite_language_allowed is False
