# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Program lifecycle helpers."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.errors import InvalidLifecycleTransitionError
from bijux_proteomics.domain.program_spec import ProgramStage
from bijux_proteomics_foundation import JsonModel, ProgramId


class LifecycleTransition(JsonModel):
    """One lifecycle transition with audit context."""

    model_config = ConfigDict(extra="forbid")

    from_stage: ProgramStage = Field(..., description="Previous lifecycle stage.")
    to_stage: ProgramStage = Field(..., description="New lifecycle stage.")
    reason: str = Field(..., min_length=1, description="Why the transition happened.")
    actor: str = Field(
        ..., min_length=1, description="Who or what initiated the change."
    )
    changed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the transition was recorded.",
    )


class ProgramLifecycle(JsonModel):
    """Transition history for a protein program."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    current_stage: ProgramStage = Field(..., description="Current lifecycle stage.")
    visited_stages: list[ProgramStage] = Field(
        default_factory=list,
        description="Visited lifecycle stages in order.",
    )
    transitions: list[LifecycleTransition] = Field(
        default_factory=list,
        description="Audit trail for lifecycle transitions.",
    )


ALLOWED_STAGE_TRANSITIONS: dict[ProgramStage, set[ProgramStage]] = {
    ProgramStage.SCOPING: {ProgramStage.DESIGN},
    ProgramStage.DESIGN: {ProgramStage.REVIEW},
    ProgramStage.REVIEW: {ProgramStage.DESIGN, ProgramStage.LAB_READY},
    ProgramStage.LAB_READY: {ProgramStage.LEARNING},
    ProgramStage.LEARNING: {ProgramStage.DESIGN, ProgramStage.REVIEW},
}


def allowed_next_stages(stage: ProgramStage) -> set[ProgramStage]:
    """Return allowed next stages for the current lifecycle stage."""
    return set(ALLOWED_STAGE_TRANSITIONS.get(stage, set()))


def advance_stage(
    lifecycle: ProgramLifecycle,
    next_stage: ProgramStage,
    *,
    reason: str = "stage advancement recorded",
    actor: str = "system",
) -> ProgramLifecycle:
    """Advance to a new stage while preserving visit history and audit context."""
    if next_stage not in allowed_next_stages(lifecycle.current_stage):
        raise InvalidLifecycleTransitionError(
            f"cannot move from {lifecycle.current_stage.value} to {next_stage.value}"
        )
    visited = list(lifecycle.visited_stages)
    if not visited or visited[-1] is not lifecycle.current_stage:
        visited.append(lifecycle.current_stage)
    visited.append(next_stage)
    transitions = list(lifecycle.transitions)
    transitions.append(
        LifecycleTransition(
            from_stage=lifecycle.current_stage,
            to_stage=next_stage,
            reason=reason,
            actor=actor,
        )
    )
    return lifecycle.model_copy(
        update={
            "current_stage": next_stage,
            "visited_stages": visited,
            "transitions": transitions,
        }
    )
