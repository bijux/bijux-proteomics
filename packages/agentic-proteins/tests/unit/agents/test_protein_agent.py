# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any, cast

from pydantic import ValidationError
import pytest

from bijux_proteomics.biology.pathway import PathwayExecutor
from bijux_proteomics.biology.protein_agent import (
    ProteinAgent,
    ProteinConstraints,
    ProteinFailure,
    ProteinLifecycle,
    ProteinState,
)
from bijux_proteomics.biology.signals import SignalPayload, SignalScope, SignalType

if TYPE_CHECKING:
    from bijux_proteomics.biology.pathway import PathwayContract


def _constraints() -> ProteinConstraints:
    return ProteinConstraints(
        energy_cost=1.0,
        resource_dependency=("ATP",),
        inhibition_conditions=(SignalType.INHIBIT,),
    )


def _transitions() -> dict[tuple[ProteinState, SignalType], ProteinState]:
    return {
        (ProteinState.INACTIVE, SignalType.ACTIVATE): ProteinState.ACTIVE,
        (ProteinState.ACTIVE, SignalType.DEGRADE): ProteinState.DEGRADED,
        (ProteinState.INHIBITED, SignalType.ACTIVATE): ProteinState.ACTIVE,
    }


def test_deterministic_transition_with_seed() -> None:
    rng = random.Random(7)
    agent = ProteinAgent(
        agent_id="p1",
        constraints=_constraints(),
        transitions=_transitions(),
        transition_probabilities={(ProteinState.INACTIVE, SignalType.ACTIVATE): 1.0},
        rng=rng,
    )
    signal = SignalPayload(
        source_id="p1",
        targets=("p1",),
        scope=SignalScope.PATHWAY,
        signal_type=SignalType.ACTIVATE,
        magnitude=0.5,
    )
    assert agent.apply_signal(signal) is ProteinState.ACTIVE


def test_invalid_transition_disables_agent() -> None:
    agent = ProteinAgent(
        agent_id="p1",
        constraints=_constraints(),
        transitions=_transitions(),
        rng=random.Random(1),
    )
    signal = SignalPayload(
        source_id="p1", targets=("p1",), signal_type=SignalType.DEGRADE
    )
    assert agent.apply_signal(signal) is ProteinState.INACTIVE
    assert agent.disabled is True
    assert ProteinFailure.INVALID_TRANSITION in agent.failure_modes


def test_inhibition_condition_overrides_transition() -> None:
    agent = ProteinAgent(
        agent_id="p1",
        constraints=_constraints(),
        transitions=_transitions(),
        rng=random.Random(2),
    )
    signal = SignalPayload(
        source_id="p1", targets=("p1",), signal_type=SignalType.INHIBIT
    )
    assert agent.apply_signal(signal) is ProteinState.INHIBITED
    assert agent.lifecycle is ProteinLifecycle.INHIBITED


def test_misfold_disables_and_degrades() -> None:
    agent = ProteinAgent(
        agent_id="p1",
        constraints=_constraints(),
        transitions=_transitions(),
        rng=random.Random(3),
    )
    signal = SignalPayload(
        source_id="p1", targets=("p1",), signal_type=SignalType.MISFOLD
    )
    assert agent.apply_signal(signal) is ProteinState.DEGRADED
    assert agent.disabled is True
    assert ProteinFailure.MISFOLD in agent.failure_modes


def test_memory_decay_is_lossy() -> None:
    agent = ProteinAgent(
        agent_id="p1",
        constraints=_constraints(),
        transitions=_transitions(),
        rng=random.Random(4),
        memory_capacity=1,
    )
    agent.record_memory("token", "value", decay_steps=1)
    assert agent.get_memory("token") == "value"
    agent.decay_memory()
    assert agent.get_memory("token") is None


def test_direct_state_mutation_is_blocked() -> None:
    agent = ProteinAgent(
        agent_id="p1",
        constraints=_constraints(),
        transitions=_transitions(),
        rng=random.Random(6),
    )
    with pytest.raises(ValueError, match="Direct state mutation"):
        agent.internal_state = ProteinState.ACTIVE


def test_pathway_executor_propagates_outputs() -> None:
    agent = ProteinAgent(
        agent_id="p1",
        constraints=_constraints(),
        transitions=_transitions(),
        rng=random.Random(5),
    )
    agent.allow_direct_mutation()
    agent.internal_state = ProteinState.ACTIVE
    agent.deny_direct_mutation()
    agent.emit(
        SignalPayload(source_id="p1", targets=("p1",), signal_type=SignalType.ACTIVATE)
    )
    executor = PathwayExecutor(
        agents=[agent],
        edges={"p1": ("p1",)},
        contract=_contract(),
    )
    outputs = executor.step(
        [
            SignalPayload(
                source_id="p1", targets=("p1",), signal_type=SignalType.ACTIVATE
            )
        ]
    )
    assert len(outputs) == 1
    assert outputs[0].signal_type is SignalType.ACTIVATE


def test_signal_payload_rejects_non_string_metadata_keys() -> None:
    with pytest.raises(ValidationError):
        invalid_metadata = cast(dict[str, Any], {1: "bad"})
        SignalPayload(
            source_id="p1",
            targets=("p1",),
            signal_type=SignalType.ACTIVATE,
            metadata=invalid_metadata,
        )


def _contract() -> PathwayContract:
    from bijux_proteomics.biology.pathway import PathwayContract

    return PathwayContract(max_coupling=3, forbid_cycles=True)
