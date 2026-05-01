# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Lab planning capability surfaces for iteration 10."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class AssayProgressionState(StrEnum):
    """Lifecycle states for assay progression planning."""

    DISCOVERY = "discovery"
    VERIFICATION = "verification"
    VALIDATION = "validation"
    TARGETED_FOLLOW_UP = "targeted_follow_up"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class AssayProgressionTransition(JsonModel):
    """One progression transition with deterministic rationale."""

    model_config = ConfigDict(extra="forbid")

    from_state: AssayProgressionState
    to_state: AssayProgressionState
    rationale: str = Field(..., min_length=1)


class AssayProgressionModel(JsonModel):
    """Assay progression record with auditable transitions."""

    model_config = ConfigDict(extra="forbid")

    assay_id: str = Field(..., min_length=1)
    current_state: AssayProgressionState
    transitions: tuple[AssayProgressionTransition, ...] = Field(default_factory=tuple)


_ALLOWED_NEXT_STATES: dict[AssayProgressionState, set[AssayProgressionState]] = {
    AssayProgressionState.DISCOVERY: {
        AssayProgressionState.VERIFICATION,
        AssayProgressionState.BLOCKED,
    },
    AssayProgressionState.VERIFICATION: {
        AssayProgressionState.VALIDATION,
        AssayProgressionState.TARGETED_FOLLOW_UP,
        AssayProgressionState.BLOCKED,
    },
    AssayProgressionState.VALIDATION: {
        AssayProgressionState.TARGETED_FOLLOW_UP,
        AssayProgressionState.COMPLETED,
        AssayProgressionState.BLOCKED,
    },
    AssayProgressionState.TARGETED_FOLLOW_UP: {
        AssayProgressionState.VALIDATION,
        AssayProgressionState.COMPLETED,
        AssayProgressionState.BLOCKED,
    },
    AssayProgressionState.COMPLETED: set(),
    AssayProgressionState.BLOCKED: {
        AssayProgressionState.DISCOVERY,
        AssayProgressionState.VERIFICATION,
        AssayProgressionState.VALIDATION,
        AssayProgressionState.TARGETED_FOLLOW_UP,
    },
}


def transition_assay_progression(
    model: AssayProgressionModel,
    *,
    to_state: AssayProgressionState,
    rationale: str,
) -> AssayProgressionModel:
    """Move assay progression state while enforcing explicit planning boundaries."""

    allowed = _ALLOWED_NEXT_STATES[model.current_state]
    if to_state not in allowed:
        raise ValueError(
            f"cannot move assay from {model.current_state.value!r} to {to_state.value!r}"
        )
    transitions = list(model.transitions)
    transitions.append(
        AssayProgressionTransition(
            from_state=model.current_state,
            to_state=to_state,
            rationale=rationale,
        )
    )
    return model.model_copy(
        update={
            "current_state": to_state,
            "transitions": tuple(transitions),
        }
    )
