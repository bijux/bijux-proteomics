# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import random

import pytest

from agentic_proteins.biology.pathway import PathwayContract, PathwayExecutor
from agentic_proteins.biology.protein_agent import ProteinAgent, ProteinConstraints, ProteinState
from agentic_proteins.biology.regulator import (
    ApprovalMode,
    LLMAuthorityBoundary,
    LLMAction,
    LLMRegulator,
    PermissionMode,
    Proposal,
)
from agentic_proteins.biology.signals import SignalPayload, SignalType


def _constraints() -> ProteinConstraints:
    return ProteinConstraints(
        energy_cost=0.1,
        resource_dependency=("ATP",),
        inhibition_conditions=(SignalType.INHIBIT,),
        min_energy=0.0,
    )


def _agent() -> ProteinAgent:
    return ProteinAgent(
        agent_id="p1",
        constraints=_constraints(),
        transitions={(ProteinState.INACTIVE, SignalType.ACTIVATE): ProteinState.ACTIVE},
        transition_probabilities={(ProteinState.INACTIVE, SignalType.ACTIVATE): 1.0},
        rng=random.Random(1),
        energy=1.0,
    )


def _executor(agent: ProteinAgent) -> PathwayExecutor:
    return PathwayExecutor(
        agents=[agent],
        edges={"p1": ("p1",)},
        contract=PathwayContract(),
        seed=11,
    )


def test_authority_boundary_blocks_forbidden_action() -> None:
    boundary = LLMAuthorityBoundary(
        allowed_actions=(LLMAction.TUNE_PROBABILITY,),
        forbidden_actions=(LLMAction.ADJUST_THRESHOLD,),
        permission=PermissionMode.READ_ONLY,
    )
    regulator = LLMRegulator(model_id="test", authority=boundary)
    proposal = Proposal(
        target="p1",
        parameter="noise_sigma",
        suggested_change=0.2,
        confidence=0.4,
        rationale="tune",
        action=LLMAction.ADJUST_THRESHOLD,
    )
    with pytest.raises(ValueError):
        regulator.propose("prompt", proposal)


def test_proposal_validator_rejects_unknown_parameter() -> None:
    regulator = LLMRegulator(model_id="test")
    agent = _agent()
    proposal = Proposal(
        target="p1",
        parameter="transitions",
        suggested_change=1.0,
        confidence=0.9,
        rationale="bad",
        action=LLMAction.TUNE_PROBABILITY,
    )
    assert regulator.validate_proposal(proposal, agent=agent, contract=PathwayContract()) is False


def test_manual_approval_requires_hook() -> None:
    regulator = LLMRegulator(model_id="test", approval_mode=ApprovalMode.MANUAL_APPROVE)
    proposal = Proposal(
        target="p1",
        parameter="noise_sigma",
        suggested_change=0.2,
        confidence=0.5,
        rationale="tune",
        action=LLMAction.ADJUST_THRESHOLD,
    )
    with pytest.raises(ValueError):
        regulator.approve(proposal)


def test_counterfactual_rejects_no_improvement() -> None:
    agent = _agent()
    executor = _executor(agent)
    regulator = LLMRegulator(model_id="test")
    proposal = Proposal(
        target="p1",
        parameter="noise_sigma",
        suggested_change=0.0,
        confidence=0.6,
        rationale="no change",
        action=LLMAction.ADJUST_THRESHOLD,
    )
    signal = SignalPayload(source_id="p1", targets=("p1",), signal_type=SignalType.ACTIVATE)

    def metric(events: list[object]) -> float:
        return float(len(events))

    assert (
        regulator.counterfactual_acceptance(
            proposal,
            executor=executor,
            signals=[signal],
            metric=metric,
        )
        is False
    )


def test_observability_records_outcome() -> None:
    regulator = LLMRegulator(model_id="test")
    proposal = Proposal(
        target="p1",
        parameter="noise_sigma",
        suggested_change=0.1,
        confidence=0.2,
        rationale="log",
        action=LLMAction.ADJUST_THRESHOLD,
    )
    regulator.observe(prompt="prompt", proposal=proposal, accepted=False)
    assert regulator.observations[-1].accepted is False


def test_read_only_apply_raises() -> None:
    boundary = LLMAuthorityBoundary(
        allowed_actions=(LLMAction.TUNE_PROBABILITY,),
        forbidden_actions=(),
        permission=PermissionMode.READ_ONLY,
    )
    regulator = LLMRegulator(model_id="test", authority=boundary)
    agent = _agent()
    proposal = Proposal(
        target="p1",
        parameter="noise_sigma",
        suggested_change=0.2,
        confidence=0.5,
        rationale="tune",
        action=LLMAction.TUNE_PROBABILITY,
    )
    with pytest.raises(ValueError, match="write-through"):
        regulator.apply(proposal, agent=agent)
