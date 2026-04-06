#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Invariant visualization for pathway execution."""

from __future__ import annotations

from agentic_proteins.biology import PathwayExecutor, ProteinAgent, SignalPayload, SignalType
from agentic_proteins.biology.protein_agent import ProteinConstraints, ProteinState


def _agent(agent_id: str, *, energy: float) -> ProteinAgent:
    constraints = ProteinConstraints(
        energy_cost=0.4,
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
    agent = _agent("protein_a", energy=0.5)
    executor = PathwayExecutor(
        agents=[agent],
        edges={"protein_a": ()},
        seed=5,
    )
    activate = SignalPayload(
        source_id="system",
        targets=("protein_a",),
        signal_type=SignalType.ACTIVATE,
        magnitude=1.0,
    )
    executor.step([activate])
    for record in executor.invariant_log:
        print(
            f"tick={record.tick} energy={record.total_energy:.2f} "
            f"active={record.active_count} violations={record.violations}"
        )


if __name__ == "__main__":
    main()
