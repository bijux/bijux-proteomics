from __future__ import annotations

import pytest

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


def _agent() -> ProteinAgent:
    return ProteinAgent(
        agent_id="p1",
        internal_state=ProteinState.INACTIVE,
        constraints=ProteinConstraints(
            energy_cost=0.1,
            resource_dependency=(),
            inhibition_conditions=(),
            min_energy=0.0,
        ),
        transitions={(ProteinState.INACTIVE, SignalType.ACTIVATE): ProteinState.ACTIVE},
    )


def test_propose_records_observation_on_none() -> None:
    regulator = LLMRegulator(model_id="test")
    proposal = regulator.propose("prompt", None)
    assert proposal is None
    assert regulator.observations


def test_validate_proposal_rejects_invalid_fields() -> None:
    regulator = LLMRegulator(model_id="test")
    agent = _agent()
    proposal = Proposal(
        target="p1",
        parameter="invalid",
        suggested_change=1.0,
        confidence=0.5,
        rationale="test",
        action=LLMAction.TUNE_PROBABILITY,
    )
    assert not regulator.validate_proposal(proposal, agent=agent, contract=object())

    proposal = Proposal(
        target="p1",
        parameter="noise_sigma",
        suggested_change=1.0,
        confidence=2.0,
        rationale="test",
        action=LLMAction.TUNE_PROBABILITY,
    )
    assert not regulator.validate_proposal(proposal, agent=agent, contract=object())


def test_approve_manual_requires_hook() -> None:
    regulator = LLMRegulator(model_id="test", approval_mode=ApprovalMode.MANUAL_APPROVE)
    proposal = Proposal(
        target="p1",
        parameter="noise_sigma",
        suggested_change=1.0,
        confidence=0.5,
        rationale="test",
        action=LLMAction.TUNE_PROBABILITY,
    )
    with pytest.raises(ValueError, match="requires a hook"):
        regulator.approve(proposal)


def test_apply_respects_permission_and_parameters() -> None:
    agent = _agent()
    read_only = LLMRegulator(model_id="test")
    proposal = Proposal(
        target="p1",
        parameter="noise_sigma",
        suggested_change=0.2,
        confidence=0.5,
        rationale="test",
        action=LLMAction.TUNE_PROBABILITY,
    )
    with pytest.raises(ValueError, match="forbidden"):
        read_only.apply(proposal, agent=agent)

    boundary = LLMAuthorityBoundary(
        allowed_actions=(LLMAction.TUNE_PROBABILITY,),
        forbidden_actions=(),
        permission=PermissionMode.WRITE_THROUGH,
    )
    regulator = LLMRegulator(model_id="test", authority=boundary)
    agent.inputs.append(
        SignalPayload(source_id="p1", targets=("p1",), signal_type=SignalType.ACTIVATE)
    )
    proposal = Proposal(
        target="p1",
        parameter="transition_probabilities",
        suggested_change=0.7,
        confidence=0.5,
        rationale="test",
        action=LLMAction.TUNE_PROBABILITY,
    )
    assert regulator.apply(proposal, agent=agent)
    proposal = Proposal(
        target="p1",
        parameter="energy_cost",
        suggested_change=0.5,
        confidence=0.5,
        rationale="test",
        action=LLMAction.TUNE_PROBABILITY,
    )
    assert regulator.apply(proposal, agent=agent)
    proposal = Proposal(
        target="p1",
        parameter="unknown",
        suggested_change=0.5,
        confidence=0.5,
        rationale="test",
        action=LLMAction.TUNE_PROBABILITY,
    )
    assert not regulator.apply(proposal, agent=agent)
