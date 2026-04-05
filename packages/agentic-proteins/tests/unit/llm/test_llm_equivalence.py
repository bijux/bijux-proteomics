# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import random

from agentic_proteins.biology.pathway import PathwayContract, PathwayExecutor
from agentic_proteins.biology.protein_agent import ProteinAgent, ProteinConstraints, ProteinState
from agentic_proteins.biology.regulator import LLMRegulator
from agentic_proteins.biology.signals import SignalPayload, SignalType


def _constraints() -> ProteinConstraints:
    return ProteinConstraints(
        energy_cost=0.1,
        resource_dependency=("ATP",),
        inhibition_conditions=(SignalType.INHIBIT,),
        min_energy=0.0,
    )


def _agent(agent_id: str) -> ProteinAgent:
    return ProteinAgent(
        agent_id=agent_id,
        constraints=_constraints(),
        transitions={(ProteinState.INACTIVE, SignalType.ACTIVATE): ProteinState.ACTIVE},
        transition_probabilities={(ProteinState.INACTIVE, SignalType.ACTIVATE): 1.0},
        rng=random.Random(3),
        energy=1.0,
    )


def test_no_llm_equivalence_pathway_runs() -> None:
    agent = _agent("p1")
    executor = PathwayExecutor(
        agents=[agent],
        edges={"p1": ("p1",)},
        contract=PathwayContract(),
        seed=22,
    )
    signal = SignalPayload(source_id="p1", targets=("p1",), signal_type=SignalType.ACTIVATE)
    outputs = executor.step([signal])
    assert agent.internal_state is ProteinState.ACTIVE
    assert outputs == []


def test_agentic_claim_without_llm() -> None:
    agent = _agent("p1")
    signal = SignalPayload(source_id="p1", targets=("p1",), signal_type=SignalType.ACTIVATE)
    agent.apply_signal(signal)
    assert agent.internal_state is ProteinState.ACTIVE

    regulator = LLMRegulator(model_id="test")
    assert regulator is not None
