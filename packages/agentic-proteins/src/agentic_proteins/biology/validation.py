"""Validation rules for protein transitions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from agentic_proteins.biology.signals import SignalPayload, SignalType

if TYPE_CHECKING:
    from agentic_proteins.biology.protein_agent import ProteinState


def validate_transition(
    old_state: ProteinState, signal: SignalPayload, new_state: ProteinState
) -> None:
    """Validate state transitions with hard rules."""
    from agentic_proteins.biology.protein_agent import ProteinState

    if old_state is ProteinState.DEGRADED and new_state is not ProteinState.DEGRADED:
        raise ValueError("Degraded proteins cannot recover.")
    if (
        signal.signal_type is SignalType.DEGRADE
        and new_state is not ProteinState.DEGRADED
    ):
        raise ValueError("Degrade signal must result in degraded state.")
