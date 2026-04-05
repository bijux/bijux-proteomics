# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import random

import pytest

from agentic_proteins.biology.pathway import ExecutionMode, PathwayContract, PathwayExecutor
from agentic_proteins.biology.protein_agent import (
    ProteinAgent,
    ProteinConstraints,
    ProteinFailure,
    ProteinState,
)
from agentic_proteins.biology.signals import SignalPayload, SignalScope, SignalType
from agentic_proteins.biology.validation import validate_transition


def _constraints(energy: float = 1.0) -> ProteinConstraints:
    return ProteinConstraints(
        energy_cost=1.0,
        resource_dependency=("ATP",),
        inhibition_conditions=(SignalType.INHIBIT,),
        min_energy=0.0,
    )


def _transitions() -> dict[tuple[ProteinState, SignalType], ProteinState]:
    return {
        (ProteinState.INACTIVE, SignalType.ACTIVATE): ProteinState.ACTIVE,
        (ProteinState.ACTIVE, SignalType.DEGRADE): ProteinState.DEGRADED,
    }


def test_transition_validator_blocks_invalid_recovery() -> None:
    signal = SignalPayload(source_id="p1", targets=("p1",), signal_type=SignalType.ACTIVATE)
    with pytest.raises(ValueError):
        validate_transition(ProteinState.DEGRADED, signal, ProteinState.ACTIVE)


def test_invariants_fail_fast_on_negative_energy() -> None:
    agent = ProteinAgent(
        agent_id="p1",
        constraints=_constraints(),
        transitions=_transitions(),
        rng=random.Random(1),
        energy=0.5,
    )
    signal = SignalPayload(source_id="p1", targets=("p1",), signal_type=SignalType.ACTIVATE)
    with pytest.raises(ValueError):
        agent.apply_signal(signal)


def test_no_output_without_activation() -> None:
    agent = ProteinAgent(
        agent_id="p1",
        constraints=_constraints(),
        transitions=_transitions(),
        rng=random.Random(2),
    )
    with pytest.raises(ValueError):
        agent.emit(SignalPayload(source_id="p1", targets=("p1",), signal_type=SignalType.ACTIVATE))


def test_directional_signal_routing() -> None:
    agent = ProteinAgent(
        agent_id="p1",
        constraints=_constraints(),
        transitions=_transitions(),
        rng=random.Random(3),
    )
    executor = PathwayExecutor(
        agents=[agent],
        edges={"p1": ()},
        contract=PathwayContract(),
    )
    signal = SignalPayload(
        source_id="p1",
        targets=("missing",),
        scope=SignalScope.PATHWAY,
        signal_type=SignalType.ACTIVATE,
    )
    outputs = executor.step([signal])
    assert outputs == []


def test_deterministic_replay_event_log() -> None:
    agent = ProteinAgent(
        agent_id="p1",
        constraints=_constraints(),
        transitions=_transitions(),
        transition_probabilities={(ProteinState.INACTIVE, SignalType.ACTIVATE): 1.0},
        rng=random.Random(4),
    )
    executor = PathwayExecutor(
        agents=[agent],
        edges={"p1": ("p1",)},
        contract=PathwayContract(),
        seed=17,
    )
    signal = SignalPayload(source_id="p1", targets=("p1",), signal_type=SignalType.ACTIVATE)
    executor.step([signal])
    replay_log = executor.replay([signal])
    assert executor.event_log == replay_log


def test_lifecycle_management_degrades_and_removes() -> None:
    agent = ProteinAgent(
        agent_id="p1",
        constraints=_constraints(),
        transitions=_transitions(),
        transition_probabilities={(ProteinState.ACTIVE, SignalType.DEGRADE): 1.0},
        rng=random.Random(5),
    )
    agent.allow_direct_mutation()
    agent.internal_state = ProteinState.ACTIVE
    agent.deny_direct_mutation()
    signal = SignalPayload(source_id="p1", targets=("p1",), signal_type=SignalType.DEGRADE)
    assert agent.apply_signal(signal) is ProteinState.DEGRADED
    agent.remove()
    assert agent.disabled is True


def test_simulation_blocks_intervention() -> None:
    agent = ProteinAgent(
        agent_id="p1",
        constraints=_constraints(),
        transitions=_transitions(),
        rng=random.Random(6),
    )
    executor = PathwayExecutor(
        agents=[agent],
        edges={"p1": ()},
        contract=PathwayContract(),
        mode=ExecutionMode.SIMULATION,
    )
    with pytest.raises(ValueError):
        executor.intervene({"p1": 1.0})


def test_failure_observability_records_cause() -> None:
    agent = ProteinAgent(
        agent_id="p1",
        constraints=_constraints(),
        transitions=_transitions(),
        rng=random.Random(7),
    )
    signal = SignalPayload(source_id="p1", targets=("p1",), signal_type=SignalType.DEGRADE)
    agent.apply_signal(signal)
    assert agent.failure_events
    assert agent.failure_events[0].cause == "missing transition rule"


def test_brutal_extension_invariants_hold() -> None:
    constraints = ProteinConstraints(
        energy_cost=2.0,
        resource_dependency=("ATP", "NADH"),
        inhibition_conditions=(SignalType.INHIBIT,),
        min_energy=0.0,
    )
    transitions = {
        (ProteinState.INACTIVE, SignalType.ACTIVATE): ProteinState.ACTIVE,
    }
    agent = ProteinAgent(
        agent_id="pX",
        constraints=constraints,
        transitions=transitions,
        rng=random.Random(8),
        energy=1.0,
    )
    signal = SignalPayload(source_id="pX", targets=("pX",), signal_type=SignalType.ACTIVATE)
    with pytest.raises(ValueError):
        agent.apply_signal(signal)
    assert ProteinFailure.INVALID_TRANSITION in agent.failure_modes or agent.disabled is True
