"""Pathway executor for multi-agent signal propagation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import random
import time
import tracemalloc
from typing import Any

from agentic_proteins.biology.protein_agent import ProteinAgent, ProteinState
from agentic_proteins.biology.signals import SignalPayload, SignalScope


class ExecutionMode(str, Enum):
    """Simulation versus intervention boundary."""

    SIMULATION = "simulation"
    INTERVENTION = "intervention"


@dataclass(frozen=True)
class TransitionEvent:
    """Deterministic event log entry."""

    tick: int
    agent_id: str
    old_state: str
    new_state: str
    signal: SignalPayload


@dataclass(frozen=True)
class ExecutionCost:
    """Per-tick execution cost."""

    tick: int
    cpu_seconds: float
    memory_kb: float
    agent_count: int
    signal_volume: int


@dataclass(frozen=True)
class InvariantRecord:
    """Per-tick invariant evaluation snapshot."""

    tick: int
    total_energy: float
    active_count: int
    violations: tuple[str, ...]


@dataclass(frozen=True)
class PathwayMetrics:
    """Minimal pathway metrics set."""

    throughput: float
    failure_rate: float
    recovery_success: float
    signal_entropy: float
    llm_intervention_delta: float


@dataclass(frozen=True)
class PathwayContract:
    """Contract for pathway composition."""

    max_coupling: int = 3
    max_incoming_signals: int = 100
    max_outgoing_signals: int = 100
    max_dependency_depth: int = 8
    activation_mass_limit: int = 10_000
    min_total_energy: float = 0.0
    forbid_cycles: bool = False

    def validate(
        self, agents: list[ProteinAgent], edges: dict[str, tuple[str, ...]]
    ) -> None:
        agent_ids = {agent.agent_id for agent in agents}
        if len(agent_ids) != len(agents):
            raise ValueError("Agent ids must be unique.")
        for source, targets in edges.items():
            if source not in agent_ids:
                raise ValueError("Unknown source in pathway edges.")
            if len(targets) > self.max_coupling:
                raise ValueError("Pathway coupling exceeds max_coupling.")
            for target in targets:
                if target not in agent_ids:
                    raise ValueError("Unknown target in pathway edges.")
        if (
            self.forbid_cycles
            and _has_cycle(edges)
            and not _self_loop_allowed(agents, edges)
        ):
            raise ValueError("Cyclic dependencies are forbidden.")
        depth = _max_depth(edges)
        if depth > self.max_dependency_depth:
            raise ValueError("Pathway dependency depth exceeds max_dependency_depth.")


def _has_cycle(edges: dict[str, tuple[str, ...]]) -> bool:
    visited: set[str] = set()
    stack: set[str] = set()

    def _visit(node: str) -> bool:
        if node in stack:
            return True
        if node in visited:
            return False
        visited.add(node)
        stack.add(node)
        for nxt in edges.get(node, ()):
            if _visit(nxt):
                return True
        stack.remove(node)
        return False

    return any(_visit(node) for node in edges)


def _self_loop_allowed(
    agents: list[ProteinAgent], edges: dict[str, tuple[str, ...]]
) -> bool:
    for source, targets in edges.items():
        for target in targets:
            if target != source:
                return False
    active_agents = {
        agent.agent_id
        for agent in agents
        if agent.internal_state is ProteinState.ACTIVE
    }
    for source, targets in edges.items():
        if source in targets and source not in active_agents:
            return False
    return True


def _max_depth(edges: dict[str, tuple[str, ...]]) -> int:
    memo: dict[str, int] = {}
    visiting: set[str] = set()

    def _depth(node: str) -> int:
        if node in memo:
            return memo[node]
        if node in visiting:
            return 0
        visiting.add(node)
        children = edges.get(node, ())
        if not children:
            memo[node] = 1
            visiting.remove(node)
            return 1
        depth = 1 + max((_depth(child) for child in children), default=0)
        memo[node] = depth
        visiting.remove(node)
        return depth

    return max((_depth(node) for node in edges), default=0)


@dataclass
class PathwayExecutor:
    """Step-based pathway executor without a manager agent."""

    agents: list[ProteinAgent]
    edges: dict[str, tuple[str, ...]]
    contract: PathwayContract = field(default_factory=PathwayContract)
    mode: ExecutionMode = ExecutionMode.SIMULATION
    seed: int = 0
    measure_costs: bool = True

    def __post_init__(self) -> None:
        self.contract.validate(self.agents, self.edges)
        self._agent_map = {agent.agent_id: agent for agent in self.agents}
        rng = random.Random(self.seed)  # noqa: S311
        for agent in self.agents:
            agent.rng = random.Random(rng.randint(0, 1_000_000))  # noqa: S311
        self._tick = 0
        self.event_log: list[TransitionEvent] = []
        self.cost_log: list[ExecutionCost] = []
        self.invariant_log: list[InvariantRecord] = []
        self.global_failures: list[str] = []
        self.resource_pool: dict[str, float] = {}

    def step(self, signals: list[SignalPayload]) -> list[SignalPayload]:
        self._tick += 1
        start_time = time.perf_counter()
        if self.measure_costs:
            tracemalloc.start()
        for agent in self.agents:
            agent.assert_invariants()
        ordered = sorted(
            signals,
            key=lambda s: (s.scope.value, s.source_id, s.targets),
        )
        delivered = self._route_signals(ordered)
        next_signals: list[SignalPayload] = []
        for agent in self.agents:
            for signal in delivered.get(agent.agent_id, ()):
                old = agent.internal_state
                new = agent.apply_signal(signal)
                self.event_log.append(
                    TransitionEvent(
                        tick=self._tick,
                        agent_id=agent.agent_id,
                        old_state=old.value,
                        new_state=new.value,
                        signal=signal,
                    )
                )
            next_signals.extend(agent.outputs)
            agent.outputs.clear()
            if len(next_signals) > self.contract.max_outgoing_signals:
                raise ValueError("Outgoing signal cap exceeded.")
        for agent in self.agents:
            agent.assert_invariants()
        self._check_conservation()
        if self.measure_costs:
            current, _peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            elapsed = time.perf_counter() - start_time
            self.cost_log.append(
                ExecutionCost(
                    tick=self._tick,
                    cpu_seconds=elapsed,
                    memory_kb=current / 1024.0,
                    agent_count=len(self.agents),
                    signal_volume=len(signals),
                )
            )
        return next_signals

    def replay(self, signals: list[SignalPayload]) -> list[TransitionEvent]:
        replay_agents = [agent.clone() for agent in self.agents]
        replay_executor = PathwayExecutor(
            agents=replay_agents,
            edges=self.edges,
            contract=self.contract,
            mode=self.mode,
            seed=self.seed,
        )
        replay_executor.step(signals)
        return replay_executor.event_log

    def replay_with_adjustments(
        self, signals: list[SignalPayload], adjustments: dict[str, Any]
    ) -> list[TransitionEvent]:
        replay_agents = [agent.clone() for agent in self.agents]
        replay_executor = PathwayExecutor(
            agents=replay_agents,
            edges=self.edges,
            contract=self.contract,
            mode=self.mode,
            seed=self.seed,
        )
        for agent in replay_executor.agents:
            proposal = adjustments.get(agent.agent_id)
            if proposal is None:
                continue
            if proposal.parameter == "noise_sigma":
                agent.noise_sigma = proposal.suggested_change
            if proposal.parameter == "energy_cost":
                agent.constraints = agent.constraints.__class__(
                    energy_cost=proposal.suggested_change,
                    resource_dependency=agent.constraints.resource_dependency,
                    inhibition_conditions=agent.constraints.inhibition_conditions,
                    min_energy=agent.constraints.min_energy,
                )
        replay_executor.step(signals)
        return replay_executor.event_log

    def intervene(self, adjustments: dict[str, float]) -> None:
        if self.mode is not ExecutionMode.INTERVENTION:
            raise ValueError("Intervention is not allowed in simulation mode.")
        for agent_id, delta in adjustments.items():
            agent = self._agent_map.get(agent_id)
            if agent is None:
                raise ValueError("Unknown agent id for intervention.")
            agent.energy += delta

    def _route_signals(
        self, signals: list[SignalPayload]
    ) -> dict[str, tuple[SignalPayload, ...]]:
        routed: dict[str, list[SignalPayload]] = {a.agent_id: [] for a in self.agents}
        for signal in signals:
            if signal.scope is SignalScope.LOCAL:
                if signal.source_id in routed:
                    routed[signal.source_id].append(signal)
                continue
            if signal.scope is SignalScope.GLOBAL:
                for agent_id in routed:
                    routed[agent_id].append(signal)
                continue
            targets = signal.targets or self.edges.get(signal.source_id, ())
            for target in targets:
                if target in routed:
                    routed[target].append(signal)
        for target_id, incoming in routed.items():
            if len(incoming) > self.contract.max_incoming_signals:
                raise ValueError(f"Incoming signal cap exceeded for {target_id}.")
        return {key: tuple(value) for key, value in routed.items()}

    def _check_conservation(self) -> None:
        total_energy = sum(agent.energy for agent in self.agents)
        active_count = sum(
            agent.internal_state.value == "active" for agent in self.agents
        )
        violations: list[str] = []
        if total_energy < self.contract.min_total_energy:
            violations.append("energy_violation")
        if active_count > self.contract.activation_mass_limit:
            violations.append("activation_mass_violation")
        resource_violation = any(
            self.resource_pool and self.resource_pool.get(resource, 0.0) <= 0.0
            for agent in self.agents
            for resource in agent.constraints.resource_dependency
        )
        if resource_violation:
            violations.append("resource_violation")
        self.invariant_log.append(
            InvariantRecord(
                tick=self._tick,
                total_energy=total_energy,
                active_count=active_count,
                violations=tuple(sorted(set(violations))),
            )
        )
        if violations:
            self.global_failures.extend(violations)
            if "energy_violation" in violations:
                raise ValueError("Total energy below minimum.")
            if "activation_mass_violation" in violations:
                raise ValueError("Activation mass limit exceeded.")
            raise ValueError("Resource dependency violated.")

    def compute_metrics(self) -> PathwayMetrics:
        failure_events = sum(len(agent.failure_events) for agent in self.agents)
        total_events = max(len(self.event_log), 1)
        failure_rate = failure_events / float(total_events)
        throughput = total_events / max(self._tick, 1)
        recovery_success = 0.0
        signal_entropy = 0.0
        llm_intervention_delta = 0.0
        return PathwayMetrics(
            throughput=throughput,
            failure_rate=failure_rate,
            recovery_success=recovery_success,
            signal_entropy=signal_entropy,
            llm_intervention_delta=llm_intervention_delta,
        )
