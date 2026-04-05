# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import random

from agentic_proteins.biology.pathway import PathwayContract, PathwayExecutor
from agentic_proteins.biology.protein_agent import ProteinAgent, ProteinConstraints, ProteinState
from agentic_proteins.biology.signals import SignalPayload, SignalScope, SignalType


def _constraints() -> ProteinConstraints:
    return ProteinConstraints(
        energy_cost=0.0,
        resource_dependency=(),
        inhibition_conditions=(),
        min_energy=0.0,
    )


def _agent(agent_id: str) -> ProteinAgent:
    return ProteinAgent(
        agent_id=agent_id,
        constraints=_constraints(),
        transitions={(ProteinState.INACTIVE, SignalType.ACTIVATE): ProteinState.ACTIVE},
        transition_probabilities={(ProteinState.INACTIVE, SignalType.ACTIVATE): 1.0},
        rng=random.Random(1),
        energy=1.0,
    )


def _run_pathway(agent_count: int) -> None:
    agents = [_agent(f"p{idx}") for idx in range(agent_count)]
    edges = {agent.agent_id: tuple() for agent in agents}
    contract = PathwayContract(
        max_incoming_signals=agent_count,
        max_outgoing_signals=agent_count,
        max_dependency_depth=2,
        activation_mass_limit=agent_count + 1,
    )
    executor = PathwayExecutor(agents=agents, edges=edges, contract=contract, seed=13)
    signal = SignalPayload(
        source_id="p0",
        targets=tuple(agent.agent_id for agent in agents),
        scope=SignalScope.GLOBAL,
        signal_type=SignalType.ACTIVATE,
    )
    executor.step([signal])
    assert executor.cost_log
    assert executor.global_failures == []


def test_pathway_stress_10_agents() -> None:
    _run_pathway(10)


def test_pathway_stress_100_agents() -> None:
    _run_pathway(100)


def test_pathway_stress_1000_agents() -> None:
    _run_pathway(1000)
