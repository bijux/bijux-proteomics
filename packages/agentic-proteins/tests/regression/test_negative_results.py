# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import random

import pytest

from agentic_proteins.biology.pathway import ExecutionMode, PathwayContract, PathwayExecutor
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
        energy_cost=1.0,
        resource_dependency=(),
        inhibition_conditions=(),
        min_energy=0.0,
    )


def test_cycle_pathway_fails_validation() -> None:
    agent = ProteinAgent(
        agent_id="p1",
        constraints=_constraints(),
        transitions={(ProteinState.INACTIVE, SignalType.ACTIVATE): ProteinState.ACTIVE},
        rng=random.Random(1),
        energy=1.0,
    )
    contract = PathwayContract(forbid_cycles=True)
    with pytest.raises(ValueError):
        PathwayExecutor(agents=[agent], edges={"p1": ("p1",)}, contract=contract)


def test_llm_makes_pathway_worse() -> None:
    agent = ProteinAgent(
        agent_id="p1",
        constraints=_constraints(),
        transitions={(ProteinState.INACTIVE, SignalType.ACTIVATE): ProteinState.ACTIVE},
        rng=random.Random(2),
        energy=0.5,
    )
    executor = PathwayExecutor(
        agents=[agent],
        edges={"p1": ("p1",)},
        contract=PathwayContract(min_total_energy=0.0),
        mode=ExecutionMode.INTERVENTION,
    )
    regulator = LLMRegulator(
        model_id="test",
        authority=LLMAuthorityBoundary(
            allowed_actions=(LLMAction.ADJUST_THRESHOLD,),
            forbidden_actions=(),
            permission=PermissionMode.WRITE_THROUGH,
        ),
        approval_mode=ApprovalMode.AUTO_APPROVE,
    )
    proposal = Proposal(
        target="p1",
        parameter="energy_cost",
        suggested_change=2.0,
        confidence=0.8,
        rationale="worse",
        action=LLMAction.ADJUST_THRESHOLD,
    )
    assert regulator.apply(proposal, agent=agent) is True
    signal = SignalPayload(source_id="p1", targets=("p1",), signal_type=SignalType.ACTIVATE)
    with pytest.raises(ValueError):
        executor.step([signal])


def test_recovery_impossible_from_degraded() -> None:
    agent = ProteinAgent(
        agent_id="p1",
        constraints=_constraints(),
        transitions={(ProteinState.INACTIVE, SignalType.ACTIVATE): ProteinState.ACTIVE},
        rng=random.Random(3),
        energy=1.0,
    )
    agent.allow_direct_mutation()
    agent.internal_state = ProteinState.DEGRADED
    agent.deny_direct_mutation()
    signal = SignalPayload(source_id="p1", targets=("p1",), signal_type=SignalType.ACTIVATE)
    with pytest.raises(ValueError):
        agent.apply_signal(signal)
