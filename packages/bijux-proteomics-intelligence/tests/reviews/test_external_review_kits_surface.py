# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.reviews.external_review_kits import (
    build_workflow_external_review_kit,
    build_workflow_external_review_kit_family,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)


def test_external_review_kit_family_covers_all_five_flagship_workflows() -> None:
    family = build_workflow_external_review_kit_family()

    assert family.family_id == "flagship-external-review-kits"
    assert tuple(kit.workflow_family for kit in family.kits) == (
        KnowledgeWorkflowFamily.DDA,
        KnowledgeWorkflowFamily.DIA,
        KnowledgeWorkflowFamily.LFQ,
        KnowledgeWorkflowFamily.PTM,
        KnowledgeWorkflowFamily.TARGETED,
    )


def test_dda_external_review_kit_is_verifiable_and_ready() -> None:
    kit = build_workflow_external_review_kit(KnowledgeWorkflowFamily.DDA)

    assert kit.ready_for_outsider_review is True
    assert kit.reviewer_bundle.bundle_id == "external_review_kit:dda"
    assert kit.standalone_verifier_report.verified is True
    assert any(
        path.endswith("dda_reviewable_run/README.md")
        for path in kit.shipped_artifact_paths
    )
    assert any(
        "independent_rerun:dda" in entry
        for entry in kit.reviewer_bundle.hash_ledger_entries
    )


def test_non_dda_external_review_kits_keep_bounded_exclusions_visible() -> None:
    dia = build_workflow_external_review_kit(KnowledgeWorkflowFamily.DIA)
    lfq = build_workflow_external_review_kit(KnowledgeWorkflowFamily.LFQ)
    ptm = build_workflow_external_review_kit(KnowledgeWorkflowFamily.PTM)
    targeted = build_workflow_external_review_kit(KnowledgeWorkflowFamily.TARGETED)

    assert dia.ready_for_outsider_review is True
    assert "library-conditioned" in " ".join(dia.known_exclusions)
    assert lfq.ready_for_outsider_review is False
    assert "release language is ahead of the benchmark evidence" in " ".join(
        lfq.known_exclusions
    )
    assert "multi-cohort transfer authority" in " ".join(lfq.known_exclusions)
    assert ptm.ready_for_outsider_review is True
    assert "PTM-family coverage" in " ".join(ptm.known_exclusions)
    assert targeted.ready_for_outsider_review is True
    assert "vendor-parity proof" in " ".join(targeted.known_exclusions)
