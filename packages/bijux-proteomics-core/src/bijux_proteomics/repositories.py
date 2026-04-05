# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Repository and review contracts for protein programs."""

from __future__ import annotations

from enum import StrEnum
from typing import Protocol

from pydantic import ConfigDict, Field

from bijux_proteomics.program_spec import ProgramSpec
from bijux_proteomics.reviews import ReviewGate
from bijux_proteomics.serialization import JsonModel


class ReviewOutcome(StrEnum):
    """Possible outcomes for a human review gate."""

    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class ReviewDecision(JsonModel):
    """Recorded outcome for a specific review gate."""

    model_config = ConfigDict(extra="forbid")

    program_id: str = Field(..., min_length=1, description="Program identifier.")
    gate_id: str = Field(..., min_length=1, description="Review gate identifier.")
    outcome: ReviewOutcome = Field(..., description="Decision outcome.")
    decided_by: str = Field(..., min_length=1, description="Decision owner.")
    rationale: str = Field(..., min_length=1, description="Why the decision was made.")


class ProgramRepository(Protocol):
    """Persistence contract for stored program manifests."""

    def save_program(self, program: ProgramSpec) -> None:
        """Persist a program manifest."""

    def load_program(self, program_id: str) -> ProgramSpec:
        """Load a previously stored program manifest."""


class ReviewDecisionRepository(Protocol):
    """Persistence contract for review decisions."""

    def save_review_decision(self, decision: ReviewDecision) -> None:
        """Persist a review decision."""

    def list_review_decisions(self, program_id: str) -> list[ReviewDecision]:
        """List recorded review decisions for a program."""


def ensure_review_clearance(
    program: ProgramSpec,
    decisions: list[ReviewDecision],
) -> list[ReviewGate]:
    """Return blocking gates that still require human approval."""
    approved_gate_ids = {
        decision.gate_id
        for decision in decisions
        if decision.program_id == program.program_id
        and decision.outcome is ReviewOutcome.APPROVED
    }
    return [
        gate
        for gate in program.review_gates
        if gate.blocking and gate.gate_id not in approved_gate_ids
    ]
