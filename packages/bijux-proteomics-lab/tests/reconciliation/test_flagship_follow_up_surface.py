# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review.flagship_kernel import (
    build_flagship_scientific_kernel_report,
)
from bijux_proteomics.review.scientific_story import WorkflowScientificSnapshot
from bijux_proteomics_intelligence.judgment.flagship_decisions import (
    build_flagship_decision_review,
)
from bijux_proteomics_knowledge.reviews.flagship_evidence import (
    build_flagship_evidence_decision_brief,
)
from bijux_proteomics_lab.reconciliation.flagship_follow_up import (
    build_flagship_workflow_follow_up_packet,
)


def test_build_flagship_workflow_follow_up_packet_marks_ready_progression() -> None:
    kernel = build_flagship_scientific_kernel_report(
        WorkflowScientificSnapshot(
            workflow_id="flagship-a",
            digested_peptide_count=18,
            identified_protein_ids=("P11111",),
            shared_peptide_group_count=0,
            quant_support_protein_ids=("P11111",),
            quant_missingness_fraction=0.0,
            quant_readiness_state="decision_ready",
            ptm_protein_ids=("P11111",),
            ambiguous_ptm_site_count=0,
            review_candidate_ids=("candidate-1",),
            target_decoy_collision_count=0,
            external_engine_disagreement_count=0,
        )
    )
    evidence = build_flagship_evidence_decision_brief(
        workflow_id="flagship-a",
        artifact_path="artifacts/workflows/flagship-workflow-chain/knowledge/decision_brief.json",
        evidence_pointers=("knowledge.decision_brief",),
        accepted_claim_count=2,
        contested_claim_count=0,
    )
    review = build_flagship_decision_review(evidence, kernel)

    packet = build_flagship_workflow_follow_up_packet(
        review,
        planned_assay_count=2,
        export_file_count=3,
        unresolved_risk_count=0,
    )

    assert packet.ready_for_progression is True
    assert packet.actions[0].action_id == "carry-plan-forward"


def test_build_flagship_workflow_follow_up_packet_keeps_blockers_visible() -> None:
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
    evidence = build_flagship_evidence_decision_brief(
        workflow_id="flagship-b",
        artifact_path="artifacts/workflows/flagship-workflow-chain/knowledge/decision_brief.json",
        evidence_pointers=("knowledge.decision_brief",),
        accepted_claim_count=1,
        contested_claim_count=1,
    )
    review = build_flagship_decision_review(evidence, kernel)

    packet = build_flagship_workflow_follow_up_packet(
        review,
        planned_assay_count=1,
        export_file_count=3,
        unresolved_risk_count=1,
    )

    assert packet.ready_for_progression is False
    assert {action.action_id for action in packet.actions} == {
        "resolve-scientific-conflict",
        "resolve-lab-risk",
    }
