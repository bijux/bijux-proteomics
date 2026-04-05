# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import random

from agentic_proteins.biology.pathway import PathwayContract, PathwayExecutor
from agentic_proteins.biology.protein_agent import ProteinAgent, ProteinConstraints, ProteinState
from agentic_proteins.biology.signals import SignalPayload, SignalType


def test_execution_cost_records_tick_metrics() -> None:
    agent = ProteinAgent(
        agent_id="p1",
        constraints=ProteinConstraints(
            energy_cost=0.0,
            resource_dependency=(),
            inhibition_conditions=(),
            min_energy=0.0,
        ),
        transitions={(ProteinState.INACTIVE, SignalType.ACTIVATE): ProteinState.ACTIVE},
        transition_probabilities={(ProteinState.INACTIVE, SignalType.ACTIVATE): 1.0},
        rng=random.Random(2),
        energy=1.0,
    )
    executor = PathwayExecutor(
        agents=[agent],
        edges={"p1": ("p1",)},
        contract=PathwayContract(),
        seed=4,
        measure_costs=True,
    )
    signal = SignalPayload(source_id="p1", targets=("p1",), signal_type=SignalType.ACTIVATE)
    executor.step([signal])
    cost = executor.cost_log[-1]
    assert cost.agent_count == 1
    assert cost.signal_volume == 1
