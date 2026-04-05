# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import random

import pytest

from agentic_proteins.biology.pathway import PathwayExecutor
from agentic_proteins.biology.protein_agent import ProteinAgent, ProteinConstraints, ProteinState
from agentic_proteins.biology.signals import SignalType


def test_invariant_bypass_is_blocked() -> None:
    constraints = ProteinConstraints(
        energy_cost=0.1,
        resource_dependency=("atp",),
        inhibition_conditions=(),
        min_energy=1.0,
    )
    agent = ProteinAgent(
        agent_id="p1",
        internal_state=ProteinState.INACTIVE,
        constraints=constraints,
        transitions={(ProteinState.INACTIVE, SignalType.ACTIVATE): ProteinState.ACTIVE},
        rng=random.Random(1),
        energy=0.0,
    )
    executor = PathwayExecutor(
        agents=[agent],
        edges={"p1": ()},
        seed=7,
    )
    with pytest.raises(ValueError, match="Energy below minimum"):
        executor.step([])
