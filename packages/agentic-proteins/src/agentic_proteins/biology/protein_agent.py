"""Protein agent abstraction with explicit constraints and failures."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import random
from typing import Any

from agentic_proteins.biology.signals import SignalPayload, SignalScope, SignalType
from agentic_proteins.biology.validation import validate_transition


class ProteinState(str, Enum):
    """Finite protein state model."""

    INACTIVE = "inactive"
    ACTIVE = "active"
    INHIBITED = "inhibited"
    DEGRADED = "degraded"


class ProteinFailure(str, Enum):
    """Failure modes for protein agents."""

    INVALID_TRANSITION = "invalid_transition"
    MISFOLD = "misfold"
    DEGRADATION = "degradation"
    DISABLED = "disabled"


class ProteinLifecycle(str, Enum):
    """Lifecycle phases for protein agents."""

    CREATED = "created"
    ACTIVE = "active"
    INHIBITED = "inhibited"
    DEGRADED = "degraded"
    REMOVED = "removed"


@dataclass(frozen=True)
class FailureEvent:
    """Structured failure observability."""

    failure: ProteinFailure
    cause: str
    impact: str
    recovery_attempt: str


@dataclass(frozen=True)
class ProteinConstraints:
    """Explicit resource and inhibition constraints."""

    energy_cost: float
    resource_dependency: tuple[str, ...]
    inhibition_conditions: tuple[SignalType, ...]
    min_energy: float = 0.0


@dataclass
class _MemoryItem:
    value: Any
    remaining_steps: int


class ProteinAgent:
    """Stateful, rule-bounded protein agent."""

    def __init__(
        self,
        *,
        agent_id: str,
        internal_state: ProteinState = ProteinState.INACTIVE,
        constraints: ProteinConstraints,
        transitions: dict[tuple[ProteinState, SignalType], ProteinState],
        transition_probabilities: dict[tuple[ProteinState, SignalType], float]
        | None = None,
        noise_sigma: float = 0.0,
        rng: random.Random | None = None,
        memory_capacity: int = 16,
        energy: float = 1.0,
    ) -> None:
        if not agent_id.strip():
            raise ValueError("agent_id must be non-empty.")
        self.agent_id = agent_id
        self._allow_direct_mutation = False
        self._in_transition = False
        self._internal_state = internal_state
        self._initial_state = internal_state
        self._initial_energy = energy
        self.lifecycle = ProteinLifecycle.CREATED
        self.constraints = constraints
        self.transitions = transitions
        self.transition_probabilities = transition_probabilities or {}
        self.noise_sigma = noise_sigma
        self.rng = rng or random.Random()  # noqa: S311
        self.failure_modes: list[ProteinFailure] = []
        self.failure_events: list[FailureEvent] = []
        self.outputs: list[SignalPayload] = []
        self.inputs: list[SignalPayload] = []
        self._disabled = False
        self._memory_capacity = memory_capacity
        self._memory: dict[str, _MemoryItem] = {}
        self._step = 0
        self.energy = energy

    @property
    def internal_state(self) -> ProteinState:
        return self._internal_state

    @internal_state.setter
    def internal_state(self, value: ProteinState) -> None:
        if not self._allow_direct_mutation and not self._in_transition:
            raise ValueError("Direct state mutation is forbidden.")
        self._internal_state = value

    def allow_direct_mutation(self) -> None:
        self._allow_direct_mutation = True

    def deny_direct_mutation(self) -> None:
        self._allow_direct_mutation = False

    def clone(self) -> ProteinAgent:
        return ProteinAgent(
            agent_id=self.agent_id,
            internal_state=self._initial_state,
            constraints=self.constraints,
            transitions=self.transitions,
            transition_probabilities=self.transition_probabilities,
            noise_sigma=self.noise_sigma,
            rng=random.Random(),  # noqa: S311
            memory_capacity=self._memory_capacity,
            energy=self._initial_energy,
        )

    def tunable_parameters(self) -> set[str]:
        return {"transition_probabilities", "noise_sigma", "energy_cost"}

    @property
    def disabled(self) -> bool:
        return self._disabled

    def record_memory(self, key: str, value: Any, *, decay_steps: int) -> None:
        if decay_steps <= 0:
            return
        if len(self._memory) >= self._memory_capacity:
            oldest_key = min(
                self._memory, key=lambda k: self._memory[k].remaining_steps
            )
            self._memory.pop(oldest_key, None)
        self._memory[key] = _MemoryItem(value=value, remaining_steps=decay_steps)

    def get_memory(self, key: str) -> Any | None:
        item = self._memory.get(key)
        return None if item is None else item.value

    def decay_memory(self) -> None:
        expired = []
        for key, item in self._memory.items():
            item.remaining_steps -= 1
            if item.remaining_steps <= 0:
                expired.append(key)
        for key in expired:
            self._memory.pop(key, None)

    def _mark_failure(self, failure: ProteinFailure) -> None:
        if failure not in self.failure_modes:
            self.failure_modes.append(failure)

    def _record_failure(
        self,
        failure: ProteinFailure,
        *,
        cause: str,
        impact: str,
        recovery_attempt: str = "none",
    ) -> None:
        self._mark_failure(failure)
        self.failure_events.append(
            FailureEvent(
                failure=failure,
                cause=cause,
                impact=impact,
                recovery_attempt=recovery_attempt,
            )
        )

    def _check_invariants(self) -> None:
        if self.energy < self.constraints.min_energy:
            self._record_failure(
                ProteinFailure.DEGRADATION,
                cause="energy below minimum",
                impact="local",
            )
            self.disable()
            raise ValueError("Energy below minimum constraint.")
        if (
            self.internal_state is ProteinState.ACTIVE
            and self.lifecycle is ProteinLifecycle.CREATED
        ):
            self.lifecycle = ProteinLifecycle.ACTIVE
        if self.internal_state is ProteinState.INHIBITED:
            self.lifecycle = ProteinLifecycle.INHIBITED
        if self.internal_state is ProteinState.DEGRADED:
            self.lifecycle = ProteinLifecycle.DEGRADED

    def assert_invariants(self) -> None:
        self._check_invariants()

    def _transition_probability(
        self, state: ProteinState, signal: SignalPayload
    ) -> float:
        base = self.transition_probabilities.get((state, signal.signal_type), 1.0)
        magnitude_factor = 1.0 + min(signal.magnitude, 1.0) * 0.1
        noise = self.rng.gauss(0.0, self.noise_sigma) if self.noise_sigma > 0 else 0.0
        prob = base * magnitude_factor + noise
        return max(0.0, min(1.0, prob))

    def apply_signal(self, signal: SignalPayload) -> ProteinState:
        self._step += 1
        if self.internal_state is ProteinState.DEGRADED:
            self._record_failure(
                ProteinFailure.DEGRADATION,
                cause="degraded state blocks transitions",
                impact="local",
            )
            self.disable()
            raise ValueError("Degraded proteins cannot transition.")
        if signal.scope is SignalScope.LOCAL and signal.source_id != self.agent_id:
            return self.internal_state
        self.inputs.append(signal)
        self.decay_memory()
        if self._disabled:
            return self.internal_state

        if signal.signal_type in self.constraints.inhibition_conditions:
            self._in_transition = True
            try:
                self.internal_state = ProteinState.INHIBITED
            finally:
                self._in_transition = False
            self._check_invariants()
            return self.internal_state

        if signal.signal_type is SignalType.MISFOLD:
            return self.misfold()

        transition_key = (self.internal_state, signal.signal_type)
        new_state = self.transitions.get(transition_key)
        if new_state is None:
            self._record_failure(
                ProteinFailure.INVALID_TRANSITION,
                cause="missing transition rule",
                impact="local",
            )
            self.disable()
            return self.internal_state

        validate_transition(self.internal_state, signal, new_state)

        probability = self._transition_probability(self.internal_state, signal)
        if self.rng.random() > probability:
            return self.internal_state

        self.energy -= self.constraints.energy_cost
        self._in_transition = True
        try:
            self.internal_state = new_state
        finally:
            self._in_transition = False
        if new_state is ProteinState.DEGRADED:
            self._record_failure(
                ProteinFailure.DEGRADATION,
                cause="degraded state reached",
                impact="local",
            )
            self.disable()
        self._check_invariants()
        return self.internal_state

    def misfold(self) -> ProteinState:
        self._in_transition = True
        try:
            self.internal_state = ProteinState.DEGRADED
        finally:
            self._in_transition = False
        self._record_failure(
            ProteinFailure.MISFOLD,
            cause="misfold signal",
            impact="local",
        )
        self.disable()
        self._check_invariants()
        return self.internal_state

    def disable(self) -> None:
        self._disabled = True
        self._record_failure(
            ProteinFailure.DISABLED,
            cause="disabled after failure",
            impact="local",
        )

    def remove(self) -> None:
        self.lifecycle = ProteinLifecycle.REMOVED
        self._disabled = True

    def emit(self, signal: SignalPayload) -> None:
        if self.internal_state is not ProteinState.ACTIVE:
            raise ValueError("No output allowed without activation.")
        self.outputs.append(signal)
