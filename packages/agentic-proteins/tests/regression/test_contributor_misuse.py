# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from agentic_proteins.biology.protein_agent import ProteinAgent, ProteinConstraints, ProteinState
from agentic_proteins.biology.signals import SignalPayload, SignalScope, SignalType


def test_contributor_misuse_invalid_transition_blocked() -> None:
    constraints = ProteinConstraints(
        energy_cost=0.1,
        resource_dependency=("atp",),
        inhibition_conditions=(),
    )
    transitions = {
        (ProteinState.DEGRADED, SignalType.ACTIVATE): ProteinState.ACTIVE,
    }
    agent = ProteinAgent(
        agent_id="p1",
        internal_state=ProteinState.DEGRADED,
        constraints=constraints,
        transitions=transitions,
    )
    signal = SignalPayload(
        signal_type=SignalType.ACTIVATE,
        magnitude=1.0,
        source_id="p1",
        targets=("p1",),
        scope=SignalScope.LOCAL,
    )
    with pytest.raises(
        ValueError, match="Degraded proteins cannot transition"
    ):
        agent.apply_signal(signal)
