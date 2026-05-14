# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Follow-up packets for the flagship workflow chain."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_intelligence.judgment.flagship_decisions import (
    FlagshipDecisionReview,
    FlagshipDecisionState,
)


class FlagshipFollowUpAction(JsonModel):
    """One operator-facing action in the flagship follow-up packet."""

    model_config = ConfigDict(extra="forbid")

    action_id: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    required_before_progression: bool


class FlagshipWorkflowFollowUpPacket(JsonModel):
    """Follow-up packet for the flagship workflow chain."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    next_cycle_artifact_path: str = Field(..., min_length=1)
    planned_assay_count: int = Field(..., ge=0)
    export_file_count: int = Field(..., ge=0)
    unresolved_risk_count: int = Field(..., ge=0)
    actions: tuple[FlagshipFollowUpAction, ...] = Field(default_factory=tuple)
    ready_for_progression: bool
    note: str = Field(..., min_length=1)


def build_flagship_workflow_follow_up_packet(
    decision_review: FlagshipDecisionReview,
    *,
    planned_assay_count: int,
    export_file_count: int,
    unresolved_risk_count: int,
    artifact_path: str = "artifacts/workflows/flagship-workflow-chain/lab/follow_up_packet.json",
    next_cycle_artifact_path: str = "artifacts/workflows/flagship-workflow-chain/lab/next_cycle_packet.json",
) -> FlagshipWorkflowFollowUpPacket:
    """Build the flagship follow-up packet without hiding progression blockers."""

    if not artifact_path.startswith("artifacts/"):
        raise ValueError("artifact_path must live under artifacts/")
    if not next_cycle_artifact_path.startswith("artifacts/"):
        raise ValueError("next_cycle_artifact_path must live under artifacts/")

    actions: list[FlagshipFollowUpAction] = []
    if (
        decision_review.decision_state
        is FlagshipDecisionState.HOLD_FOR_SCIENTIFIC_CONFLICT
    ):
        actions.append(
            FlagshipFollowUpAction(
                action_id="resolve-scientific-conflict",
                summary="return the workflow to scientific review before any new assay progression",
                required_before_progression=True,
            )
        )
    elif decision_review.decision_state is FlagshipDecisionState.HOLD_FOR_EVIDENCE:
        actions.append(
            FlagshipFollowUpAction(
                action_id="close-evidence-gaps",
                summary="gather additional evidence before downstream lab progression",
                required_before_progression=True,
            )
        )
    if unresolved_risk_count > 0:
        actions.append(
            FlagshipFollowUpAction(
                action_id="resolve-lab-risk",
                summary="address unresolved assay or export risks before progression",
                required_before_progression=True,
            )
        )
    if not actions:
        actions.append(
            FlagshipFollowUpAction(
                action_id="carry-plan-forward",
                summary="carry the reviewed lab plan into the next cycle without extra scientific hold",
                required_before_progression=False,
            )
        )

    return FlagshipWorkflowFollowUpPacket(
        workflow_id=decision_review.workflow_id,
        artifact_path=artifact_path,
        next_cycle_artifact_path=next_cycle_artifact_path,
        planned_assay_count=planned_assay_count,
        export_file_count=export_file_count,
        unresolved_risk_count=unresolved_risk_count,
        actions=tuple(actions),
        ready_for_progression=all(
            action.required_before_progression is False for action in actions
        ),
        note=(
            "The flagship follow-up packet keeps operator actions explicit so lab "
            "progression never hides scientific or operational blockers."
        ),
    )
