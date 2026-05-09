# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review.flagship_kernel import (
    build_flagship_scientific_kernel_report,
)
from bijux_proteomics.review.scientific_story import WorkflowScientificSnapshot
from bijux_proteomics_intelligence.judgment.flagship_decisions import (
    FlagshipDecisionState,
    build_flagship_decision_review,
)
from bijux_proteomics_knowledge.reviews.flagship_evidence import (
    build_flagship_evidence_decision_brief,
)


def test_build_flagship_decision_review_allows_lab_when_kernel_and_review_are_clean() -> (
    None
):
    kernel = build_flagship_scientific_kernel_report(
        WorkflowScientificSnapshot(
            workflow_id="flagship-a",
            digested_peptide_count=18,
            identified_protein_ids=("P11111",),
            shared_peptide_group_count=0,
            quant_support_protein_ids=("P11111",),
            quant_missingness_fraction=0.1,
            quant_readiness_state="decision_ready",
            ptm_protein_ids=("P11111",),
            ambiguous_ptm_site_count=0,
            review_candidate_ids=("candidate-1",),
            target_decoy_collision_count=0,
            external_engine_disagreement_count=0,
        )
    )
    packet = build_flagship_evidence_decision_brief(
        workflow_id="flagship-a",
        artifact_path="artifacts/workflows/flagship-workflow-chain/knowledge/decision_brief.json",
        evidence_pointers=("knowledge.decision_brief",),
        accepted_claim_count=2,
        contested_claim_count=0,
    )

    review = build_flagship_decision_review(packet, kernel)

    assert review.flagship is True
    assert review.decision_state is FlagshipDecisionState.READY_FOR_LAB
    assert review.follow_up_required is False


def test_build_flagship_decision_review_keeps_downgrade_chain_visible() -> None:
    kernel = build_flagship_scientific_kernel_report(
        WorkflowScientificSnapshot(
            workflow_id="flagship-b",
            digested_peptide_count=0,
            identified_protein_ids=("P11111",),
            shared_peptide_group_count=0,
            quant_support_protein_ids=("P11111",),
            quant_missingness_fraction=0.0,
            quant_readiness_state="review_only",
            ptm_protein_ids=("P11111",),
            ambiguous_ptm_site_count=0,
            target_decoy_collision_count=0,
            external_engine_disagreement_count=0,
        )
    )
    packet = build_flagship_evidence_decision_brief(
        workflow_id="flagship-b",
        artifact_path="artifacts/workflows/flagship-workflow-chain/knowledge/decision_brief.json",
        evidence_pointers=("knowledge.decision_brief",),
        accepted_claim_count=1,
        contested_claim_count=2,
    )

    review = build_flagship_decision_review(packet, kernel)

    assert review.decision_state is FlagshipDecisionState.HOLD_FOR_SCIENTIFIC_CONFLICT
    assert "empty_digestion_space" in review.downgrade_chain
    assert "evidence review still contains contested claims" in review.downgrade_chain
