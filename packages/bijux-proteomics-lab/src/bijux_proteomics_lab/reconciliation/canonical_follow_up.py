# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical follow-up packets for the flagship workflow family."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_intelligence.judgment.canonical_reviews import (
    CanonicalDecisionReview,
    CanonicalDecisionState,
)


class CanonicalFollowUpAction(JsonModel):
    """One operator-facing action in the canonical follow-up packet."""

    model_config = ConfigDict(extra="forbid")

    action_id: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    required_before_progression: bool


class CanonicalWorkflowFollowUpPacket(JsonModel):
    """Follow-up packet for the flagship workflow family."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    next_cycle_artifact_path: str = Field(..., min_length=1)
    planned_assay_count: int = Field(..., ge=0)
    export_file_count: int = Field(..., ge=0)
    unresolved_risk_count: int = Field(..., ge=0)
    actions: tuple[CanonicalFollowUpAction, ...] = Field(default_factory=tuple)
    ready_for_progression: bool
    note: str = Field(..., min_length=1)


def build_canonical_workflow_follow_up_packet(
    decision_review: CanonicalDecisionReview,
    *,
    planned_assay_count: int,
    export_file_count: int,
    unresolved_risk_count: int,
    artifact_path: str = "artifacts/workflows/canonical-reviewable-proteomics/lab/follow_up_packet.json",
    next_cycle_artifact_path: str = "artifacts/workflows/canonical-reviewable-proteomics/lab/next_cycle_packet.json",
) -> CanonicalWorkflowFollowUpPacket:
    """Build the canonical follow-up packet without hiding progression blockers."""

    if not artifact_path.startswith("artifacts/"):
        raise ValueError("artifact_path must live under artifacts/")
    if not next_cycle_artifact_path.startswith("artifacts/"):
        raise ValueError("next_cycle_artifact_path must live under artifacts/")

    actions: list[CanonicalFollowUpAction] = []
    if decision_review.decision_state is CanonicalDecisionState.HOLD_FOR_SCIENTIFIC_CONFLICT:
        actions.append(
            CanonicalFollowUpAction(
                action_id="resolve-scientific-conflict",
                summary="return the workflow to scientific review before any new assay progression",
                required_before_progression=True,
            )
        )
    elif decision_review.decision_state is CanonicalDecisionState.HOLD_FOR_EVIDENCE:
        actions.append(
            CanonicalFollowUpAction(
                action_id="close-evidence-gaps",
                summary="gather additional evidence before downstream lab progression",
                required_before_progression=True,
            )
        )
    if unresolved_risk_count > 0:
        actions.append(
            CanonicalFollowUpAction(
                action_id="resolve-lab-risk",
                summary="address unresolved assay or export risks before progression",
                required_before_progression=True,
            )
        )
    if not actions:
        actions.append(
            CanonicalFollowUpAction(
                action_id="carry-plan-forward",
                summary="carry the reviewed lab plan into the next cycle without extra scientific hold",
                required_before_progression=False,
            )
        )

    return CanonicalWorkflowFollowUpPacket(
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
            "The canonical follow-up packet keeps operator actions explicit so lab "
            "progression never hides scientific or operational blockers."
        ),
    )
