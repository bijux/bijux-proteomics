#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Minimal reproducible example for agentic proteins."""

from __future__ import annotations

from agentic_proteins.biology.pathway import ExecutionMode, PathwayContract, PathwayExecutor
from agentic_proteins.biology.protein_agent import ProteinAgent, ProteinConstraints, ProteinState
from agentic_proteins.biology.signals import SignalPayload, SignalScope, SignalType


def build_agent(agent_id: str, *, energy: float) -> ProteinAgent:
    constraints = ProteinConstraints(
        energy_cost=0.6,
        resource_dependency=("atp",),
        inhibition_conditions=(),
        min_energy=0.0,
    )
    transitions = {
        (ProteinState.INACTIVE, SignalType.ACTIVATE): ProteinState.ACTIVE,
        (ProteinState.ACTIVE, SignalType.INHIBIT): ProteinState.INHIBITED,
        (ProteinState.ACTIVE, SignalType.DEGRADE): ProteinState.DEGRADED,
    }
    return ProteinAgent(
        agent_id=agent_id,
        internal_state=ProteinState.INACTIVE,
        constraints=constraints,
        transitions=transitions,
        energy=energy,
    )


def main() -> None:
    agent_a = build_agent("protein_a", energy=1.0)
    agent_b = build_agent("protein_b", energy=0.4)
    contract = PathwayContract(
        max_incoming_signals=4,
        max_outgoing_signals=4,
        max_dependency_depth=3,
        min_total_energy=0.0,
        activation_mass_limit=4,
        forbid_cycles=False,
    )
    executor = PathwayExecutor(
        agents=[agent_a, agent_b],
        edges={"protein_a": ("protein_b",), "protein_b": ()},
        contract=contract,
        mode=ExecutionMode.SIMULATION,
        seed=11,
    )

    activate = SignalPayload(
        signal_type=SignalType.ACTIVATE,
        magnitude=1.0,
        source_id="system",
        targets=("protein_a", "protein_b"),
        scope=SignalScope.GLOBAL,
    )
    executor.step([activate])
    print("After activation:", agent_a.internal_state.value, agent_b.internal_state.value)

    degrade = SignalPayload(
        signal_type=SignalType.MISFOLD,
        magnitude=1.0,
        source_id="system",
        targets=("protein_b",),
        scope=SignalScope.GLOBAL,
    )
    try:
        executor.step([degrade])
    except ValueError as exc:
        print("Failure observed:", exc)
    print("After failure:", agent_b.internal_state.value, agent_b.disabled)

    recovered_b = agent_b.clone()
    recovered_b.allow_direct_mutation()
    recovered_b.internal_state = ProteinState.INACTIVE
    recovered_b.deny_direct_mutation()
    recovered_executor = PathwayExecutor(
        agents=[agent_a, recovered_b],
        edges=executor.edges,
        contract=contract,
        mode=ExecutionMode.SIMULATION,
        seed=11,
    )
    recovered_executor.step([activate])
    print(
        "After recovery:",
        agent_a.internal_state.value,
        recovered_b.internal_state.value,
    )


if __name__ == "__main__":
    main()
