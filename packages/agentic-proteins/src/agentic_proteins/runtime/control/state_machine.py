# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Run lifecycle state machine and transition rules."""

from __future__ import annotations

from dataclasses import dataclass

from agentic_proteins.runtime.context import RunLifecycleState

_TRANSITIONS: dict[tuple[RunLifecycleState, str], RunLifecycleState] = {
    (RunLifecycleState.PLANNED, "execute"): RunLifecycleState.EXECUTING,
    (RunLifecycleState.EXECUTING, "evaluate"): RunLifecycleState.EVALUATED,
    (RunLifecycleState.EVALUATED, "candidate_ready"): RunLifecycleState.CANDIDATE_READY,
    (RunLifecycleState.EVALUATED, "human_review"): RunLifecycleState.HUMAN_REVIEW,
    (RunLifecycleState.CANDIDATE_READY, "human_review"): RunLifecycleState.HUMAN_REVIEW,
    (RunLifecycleState.CANDIDATE_READY, "archive"): RunLifecycleState.ARCHIVED,
    (RunLifecycleState.HUMAN_REVIEW, "archive"): RunLifecycleState.ARCHIVED,
}


def next_state(state: RunLifecycleState, event: str) -> RunLifecycleState:
    """next_state."""
    return _TRANSITIONS.get((state, event), state)


def apply_transition(state: RunLifecycleState, event: str) -> RunLifecycleState:
    """apply_transition."""
    return next_state(state, event)


@dataclass
class RunStateMachine:
    """RunStateMachine."""

    state: RunLifecycleState = RunLifecycleState.PLANNED

    def transition(self, event: str) -> RunLifecycleState:
        """transition."""
        self.state = next_state(self.state, event)
        return self.state
