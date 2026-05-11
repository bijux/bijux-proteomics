# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Decision surfaces for the flagship workflow chain."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.review.flagship_kernel import FlagshipScientificKernelReport
from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_knowledge.reviews.flagship_evidence import (
    FlagshipEvidenceDecisionBrief,
    WorkflowClaimTier,
)


class FlagshipDecisionState(StrEnum):
    """Decision posture for the flagship workflow family."""

    READY_FOR_LAB = "ready_for_lab"
    HOLD_FOR_EVIDENCE = "hold_for_evidence"
    HOLD_FOR_SCIENTIFIC_CONFLICT = "hold_for_scientific_conflict"


class FlagshipDecisionReview(JsonModel):
    """Decision-decision brief for the flagship workflow family."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    workflow_family_id: str = Field(..., min_length=1)
    flagship: bool
    claim_tier: WorkflowClaimTier
    artifact_path: str = Field(..., min_length=1)
    decision_state: FlagshipDecisionState
    downgrade_chain: tuple[str, ...] = Field(default_factory=tuple)
    ranking_rationale: tuple[str, ...] = Field(default_factory=tuple)
    follow_up_required: bool
    note: str = Field(..., min_length=1)


def build_flagship_decision_review(
    evidence_review: FlagshipEvidenceDecisionBrief,
    scientific_kernel: FlagshipScientificKernelReport,
    *,
    artifact_path: str = "artifacts/workflows/flagship-workflow-chain/intelligence/decision_review.json",
) -> FlagshipDecisionReview:
    """Build the flagship decision review without flattening downgrade reasons."""

    if not artifact_path.startswith("artifacts/"):
        raise ValueError("artifact_path must live under artifacts/")

    downgrade_chain: list[str] = []
    ranking_rationale: list[str] = [
        f"evidence review accepted {evidence_review.accepted_claim_count} claims"
    ]
    if evidence_review.contested_claim_count > 0:
        downgrade_chain.append("evidence review still contains contested claims")
        ranking_rationale.append(
            f"contested claims remain visible: {evidence_review.contested_claim_count}"
        )
    if evidence_review.claim_tier is not WorkflowClaimTier.RUNTIME_PROVEN_WORKFLOW:
        downgrade_chain.append(
            f"evidence review claim tier is only {evidence_review.claim_tier.value}"
        )
    if scientific_kernel.blocked_reasons:
        downgrade_chain.extend(scientific_kernel.blocked_reasons)
        ranking_rationale.append("scientific kernel still has blocking reasons")

    if scientific_kernel.blocked_reasons:
        decision_state = FlagshipDecisionState.HOLD_FOR_SCIENTIFIC_CONFLICT
    elif (
        evidence_review.contested_claim_count > 0 or not evidence_review.review_complete
    ):
        decision_state = FlagshipDecisionState.HOLD_FOR_EVIDENCE
    else:
        decision_state = FlagshipDecisionState.READY_FOR_LAB
        ranking_rationale.append(
            "no contested claims or blocking kernel conflicts remain"
        )

    return FlagshipDecisionReview(
        workflow_id=evidence_review.workflow_id,
        workflow_family_id=evidence_review.flagship_family_id,
        flagship=True,
        claim_tier=WorkflowClaimTier.RUNTIME_PROVEN_WORKFLOW,
        artifact_path=artifact_path,
        decision_state=decision_state,
        downgrade_chain=tuple(dict.fromkeys(downgrade_chain)),
        ranking_rationale=tuple(ranking_rationale),
        follow_up_required=decision_state is not FlagshipDecisionState.READY_FOR_LAB,
        note=(
            "The flagship decision review keeps downgrade chains explicit so one "
            "workflow family does not get mistaken for broad ranking coverage."
        ),
    )
