#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Golden path example using the minimal public interface."""

from __future__ import annotations

from agentic_proteins.biology import PathwayExecutor, ProteinAgent, SignalPayload, SignalType
from agentic_proteins.biology.protein_agent import ProteinConstraints, ProteinState


def _agent(agent_id: str, *, energy: float) -> ProteinAgent:
    constraints = ProteinConstraints(
        energy_cost=0.6,
        resource_dependency=("atp",),
        inhibition_conditions=(),
        min_energy=0.0,
    )
    transitions = {
        (ProteinState.INACTIVE, SignalType.ACTIVATE): ProteinState.ACTIVE,
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
    agent_a = _agent("protein_a", energy=1.0)
    agent_b = _agent("protein_b", energy=0.4)
    executor = PathwayExecutor(
        agents=[agent_a, agent_b],
        edges={"protein_a": ("protein_b",), "protein_b": ()},
        seed=11,
    )

    activate = SignalPayload(
        source_id="system",
        targets=("protein_a", "protein_b"),
        signal_type=SignalType.ACTIVATE,
        magnitude=1.0,
    )
    executor.step([activate])
    print("Activation:", agent_a.internal_state.value, agent_b.internal_state.value)

    degrade = SignalPayload(
        source_id="system",
        targets=("protein_b",),
        signal_type=SignalType.MISFOLD,
        magnitude=1.0,
    )
    try:
        executor.step([degrade])
    except ValueError as exc:
        print("Failure:", exc)
    print("Post-failure:", agent_b.internal_state.value, agent_b.disabled)

    recovered = _agent("protein_b", energy=1.0)
    recovery_executor = PathwayExecutor(
        agents=[agent_a, recovered],
        edges={"protein_a": ("protein_b",), "protein_b": ()},
        seed=11,
    )
    recovery_executor.step([activate])
    print("Recovery:", recovered.internal_state.value)


if __name__ == "__main__":
    main()
