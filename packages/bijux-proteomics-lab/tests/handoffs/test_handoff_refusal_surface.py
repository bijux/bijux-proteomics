# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_lab.handoffs import (
    HandoffAuthorityOwner,
    HandoffSupportLevel,
    TargetedTransitionReview,
    TargetedTransitionReviewEntry,
    TransitionReviewDisposition,
    build_handoff_explanation,
    refuse_irresponsible_assay_handoff,
)
from bijux_proteomics_lab.handoffs.risk import AssayRiskAssessment
from bijux_proteomics_lab.lifecycle import CandidateHandoffValidation
from bijux_proteomics_lab.planning import (
    AdvancementEvidencePacket,
    ExecutableAssayInstruction,
    ExecutableAssayPlan,
    ReviewPacket,
)


def _review_packet() -> ReviewPacket:
    return ReviewPacket(
        program_id="prog-handoff",
        ready_for_synthesis=False,
        blocking_findings=["review evidence is still incomplete"],
        recommended_actions=["collect one orthogonal confirmation assay"],
        advancement_evidence=AdvancementEvidencePacket(
            bundle_id="bundle-handoff",
            target_id="target-handoff",
            evidence_ids=["ev-1", "ev-2"],
            required_evidence_kinds=["assay"],
            missing_evidence_kinds=["orthogonal_assay"],
        ),
    )


def _executable_plan() -> ExecutableAssayPlan:
    return ExecutableAssayPlan(
        program_id="prog-handoff",
        batch_id="batch-handoff",
        instructions=[
            ExecutableAssayInstruction(
                instruction_id="batch-handoff:assay-a",
                assay_id="assay-a",
                batch_id="batch-handoff",
                sample_kind="targeted",
                objective="confirm the prioritized transition set",
                blocking=True,
            )
        ],
        blocked_by=["review gate pending: gate-a"],
        ready_for_execution=False,
    )


def test_build_handoff_explanation_separates_supported_exploratory_and_blocked() -> (
    None
):
    explanation = build_handoff_explanation(
        candidate_id="cand-1",
        handoff_validation=CandidateHandoffValidation(
            program_id="prog-handoff",
            candidate_id="cand-1",
            accepted=False,
            accepted_assay_ids=["assay-a"],
            blockers=["contradiction pressure is too high for lab handoff"],
            skepticism_notes=["refresh supporting evidence before irreversible spend"],
            required_next_actions=[
                "clear operational blockers before scheduling handoff"
            ],
        ),
        transition_review=TargetedTransitionReview(
            assay_id="assay-a",
            approved_transition_ids=("tr-good",),
            exploratory_transition_ids=("tr-watch",),
            refused_transition_ids=("tr-bad",),
            readiness_score=0.4,
            entries=(
                TargetedTransitionReviewEntry(
                    transition_id="tr-good",
                    disposition=TransitionReviewDisposition.APPROVED,
                    risk_assessment=AssayRiskAssessment(
                        assay_id="assay-a",
                        overall_risk_score=0.18,
                        supported_for_follow_up=True,
                    ),
                ),
            ),
        ),
        review_packet=_review_packet(),
        executable_plan=_executable_plan(),
    )

    assert any(
        item.level is HandoffSupportLevel.SUPPORTED for item in explanation.supported
    )
    assert any("exploratory" in item.summary for item in explanation.exploratory)
    assert any(
        "too high for lab handoff" in item.summary for item in explanation.blocked
    )
    assert explanation.authority_boundary is not None
    assert (
        explanation.authority_boundary.scientific_recommendation_owner
        is HandoffAuthorityOwner.UPSTREAM_REVIEW
    )
    assert (
        explanation.authority_boundary.operational_execution_owner
        is HandoffAuthorityOwner.LAB_EXECUTION
    )
    assert any(
        "does not decide whether the candidate is scientifically ready to advance"
        in claim
        for claim in explanation.authority_boundary.blocked_authority_claims
    )
    assert any(
        "execution honesty" in note for note in explanation.authority_boundary.notes
    )


def test_refuse_irresponsible_assay_handoff_emits_machine_readable_refusal() -> None:
    refusal = refuse_irresponsible_assay_handoff(
        candidate_id="cand-1",
        handoff_validation=CandidateHandoffValidation(
            program_id="prog-handoff",
            candidate_id="cand-1",
            accepted=False,
            accepted_assay_ids=["assay-a"],
            blockers=["contradiction pressure is too high for lab handoff"],
            skepticism_notes=[],
            required_next_actions=[
                "clear operational blockers before scheduling handoff"
            ],
        ),
        transition_review=TargetedTransitionReview(
            assay_id="assay-a",
            approved_transition_ids=(),
            exploratory_transition_ids=("tr-watch",),
            refused_transition_ids=("tr-bad",),
            readiness_score=0.0,
        ),
        review_packet=_review_packet(),
        executable_plan=_executable_plan(),
    )

    assert refusal is not None
    assert refusal.refusal_reason_codes == (
        "analytical_contradiction_pressure",
        "execution_plan_blocked",
        "refused_targeted_transition",
        "review_packet_blocked",
    )
    assert "lab scheduling must stop before irreversible spend" in (
        refusal.operational_consequences
    )
    assert refusal.result.disposition.value == "refused"
    assert refusal.result.refusal is not None
    assert refusal.result.refusal.code == "irresponsible_assay_handoff"
    assert "contradiction pressure is too high for lab handoff" in (
        refusal.result.refusal.reason_details
    )
    assert refusal.explanation.authority_boundary is not None
    assert any(
        "cannot convert unresolved scientific blockers into execution approval" in claim
        for claim in refusal.explanation.authority_boundary.blocked_authority_claims
    )
