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
    reviewed_inputs: list[str] = Field(
        default_factory=list,
        description="Artifacts and evidence explicitly reviewed during signoff.",
    )


class ReviewGateState(StrEnum):
    """Operational state for a review gate."""

    APPROVED = "approved"
    BLOCKED = "blocked"
    NEEDS_INPUT = "needs_input"
    NEEDS_OWNER = "needs_owner"
    OPEN = "open"


class ReviewGateEvaluation(JsonModel):
    """Explainable evaluation for one review gate."""

    model_config = ConfigDict(extra="forbid")

    gate_id: str = Field(..., min_length=1, description="Review gate identifier.")
    state: ReviewGateState = Field(..., description="Operational state of the gate.")
    missing_roles: list[str] = Field(
        default_factory=list,
        description="Roles still missing from the review setup or decision trail.",
    )
    missing_inputs: list[str] = Field(
        default_factory=list,
        description="Expected decision inputs that have not been reviewed yet.",
    )
    rationale: str = Field(..., min_length=1, description="Why the gate is in this state.")


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


def evaluate_review_gate(
    gate: ReviewGate,
    decisions: list[ReviewDecision],
) -> ReviewGateEvaluation:
    """Evaluate one review gate against the recorded decision trail."""
    relevant_decisions = [decision for decision in decisions if decision.gate_id == gate.gate_id]
    required_roles = set(gate.required_roles)
    covered_roles = {decision.decided_by for decision in relevant_decisions}
    missing_roles = sorted(required_roles - covered_roles)
    reviewed_inputs = {
        reviewed_input
        for decision in relevant_decisions
        for reviewed_input in decision.reviewed_inputs
    }
    missing_inputs = sorted(set(gate.decision_inputs) - reviewed_inputs)

    if any(decision.outcome is ReviewOutcome.REJECTED for decision in relevant_decisions):
        return ReviewGateEvaluation(
            gate_id=gate.gate_id,
            state=ReviewGateState.BLOCKED,
            missing_roles=missing_roles,
            missing_inputs=missing_inputs,
            rationale="a recorded rejection keeps the gate blocked until the program is revised",
        )
    if any(
        decision.outcome is ReviewOutcome.NEEDS_REVISION for decision in relevant_decisions
    ):
        return ReviewGateEvaluation(
            gate_id=gate.gate_id,
            state=ReviewGateState.BLOCKED,
            missing_roles=missing_roles,
            missing_inputs=missing_inputs,
            rationale="the latest review requested revision before progression",
        )
    if missing_roles:
        return ReviewGateEvaluation(
            gate_id=gate.gate_id,
            state=ReviewGateState.NEEDS_OWNER,
            missing_roles=missing_roles,
            missing_inputs=missing_inputs,
            rationale="required decision owners have not all signed off yet",
        )
    if missing_inputs:
        return ReviewGateEvaluation(
            gate_id=gate.gate_id,
            state=ReviewGateState.NEEDS_INPUT,
            missing_roles=missing_roles,
            missing_inputs=missing_inputs,
            rationale="the review gate still lacks one or more expected decision inputs",
        )
    if any(decision.outcome is ReviewOutcome.APPROVED for decision in relevant_decisions):
        return ReviewGateEvaluation(
            gate_id=gate.gate_id,
            state=ReviewGateState.APPROVED,
            rationale="all required owners and decision inputs are covered by approved reviews",
        )
    return ReviewGateEvaluation(
        gate_id=gate.gate_id,
        state=ReviewGateState.OPEN,
        missing_roles=sorted(required_roles),
        missing_inputs=sorted(gate.decision_inputs),
        rationale="the review gate has not received any qualifying decision yet",
    )


def evaluate_review_gates(
    program: ProgramSpec,
    decisions: list[ReviewDecision],
) -> list[ReviewGateEvaluation]:
    """Evaluate every gate declared on a program."""
    relevant_decisions = [
        decision for decision in decisions if decision.program_id == program.program_id
    ]
    return [
        evaluate_review_gate(gate, relevant_decisions) for gate in program.review_gates
    ]
