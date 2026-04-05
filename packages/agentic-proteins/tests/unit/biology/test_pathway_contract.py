from __future__ import annotations

import pytest

from agentic_proteins.biology.pathway import ExecutionMode, PathwayContract, PathwayExecutor
from agentic_proteins.biology.protein_agent import ProteinAgent, ProteinConstraints, ProteinState
from agentic_proteins.biology.regulator import Proposal, LLMAction
from agentic_proteins.biology.signals import SignalPayload, SignalScope, SignalType


def _agent(agent_id: str, state: ProteinState = ProteinState.INACTIVE) -> ProteinAgent:
    return ProteinAgent(
        agent_id=agent_id,
        internal_state=state,
        constraints=ProteinConstraints(
            energy_cost=0.1,
            resource_dependency=(),
            inhibition_conditions=(),
            min_energy=0.0,
        ),
        transitions={
            (ProteinState.INACTIVE, SignalType.ACTIVATE): ProteinState.ACTIVE,
            (ProteinState.ACTIVE, SignalType.INHIBIT): ProteinState.INHIBITED,
        },
    )


def test_contract_rejects_duplicate_agent_ids() -> None:
    agents = [_agent("p1"), _agent("p1")]
    contract = PathwayContract()
    with pytest.raises(ValueError, match="unique"):
        contract.validate(agents, {"p1": ("p1",)})


def test_contract_rejects_unknown_edges_and_coupling() -> None:
    agents = [_agent("p1"), _agent("p2")]
    contract = PathwayContract(max_coupling=0)
    with pytest.raises(ValueError, match="Unknown source"):
        contract.validate(agents, {"p3": ("p1",)})
    with pytest.raises(ValueError, match="max_coupling"):
        contract.validate(agents, {"p1": ("p2",)})
    contract = PathwayContract(max_coupling=1)
    with pytest.raises(ValueError, match="Unknown target"):
        contract.validate(agents, {"p1": ("p3",)})


def test_contract_rejects_cycles_and_depth() -> None:
    agents = [_agent("p1"), _agent("p2")]
    contract = PathwayContract(forbid_cycles=True, max_dependency_depth=1)
    with pytest.raises(ValueError, match="Cyclic"):
        contract.validate(agents, {"p1": ("p2",), "p2": ("p1",)})
    with pytest.raises(ValueError, match="dependency depth"):
        contract.validate(agents, {"p1": ("p2",)})


def test_executor_routes_scopes_and_caps() -> None:
    agents = [_agent("p1"), _agent("p2")]
    contract = PathwayContract(max_outgoing_signals=0, max_incoming_signals=5)
    executor = PathwayExecutor(agents=agents, edges={"p1": ("p2",)}, contract=contract)
    agents[0].outputs.append(
        SignalPayload(source_id="p1", targets=("p2",), signal_type=SignalType.ACTIVATE)
    )
    with pytest.raises(ValueError, match="Outgoing signal cap"):
        executor.step([])

    contract = PathwayContract(max_incoming_signals=1)
    executor = PathwayExecutor(agents=agents, edges={"p1": ("p2",)}, contract=contract)
    signals = [
        SignalPayload(source_id="p1", signal_type=SignalType.ACTIVATE),
        SignalPayload(source_id="p1", signal_type=SignalType.ACTIVATE),
    ]
    with pytest.raises(ValueError, match="Incoming signal cap"):
        executor.step(signals)


def test_executor_conservation_checks() -> None:
    agent = _agent("p1", state=ProteinState.ACTIVE)
    contract = PathwayContract(min_total_energy=10.0)
    executor = PathwayExecutor(agents=[agent], edges={}, contract=contract)
    with pytest.raises(ValueError, match="Total energy"):
        executor._check_conservation()

    contract = PathwayContract(activation_mass_limit=0)
    executor = PathwayExecutor(agents=[agent], edges={}, contract=contract)
    with pytest.raises(ValueError, match="Activation mass"):
        executor._check_conservation()

    agent.constraints = ProteinConstraints(
        energy_cost=0.1,
        resource_dependency=("water",),
        inhibition_conditions=(),
        min_energy=0.0,
    )
    executor = PathwayExecutor(agents=[agent], edges={}, contract=PathwayContract())
    executor.resource_pool = {"water": 0.0}
    with pytest.raises(ValueError, match="Resource dependency"):
        executor._check_conservation()


def test_executor_replay_and_intervention() -> None:
    agent = _agent("p1")
    contract = PathwayContract()
    executor = PathwayExecutor(agents=[agent], edges={}, contract=contract)
    signal = SignalPayload(
        source_id="p1",
        targets=("p1",),
        scope=SignalScope.LOCAL,
        signal_type=SignalType.ACTIVATE,
    )
    events = executor.replay([signal])
    assert events

    proposal = Proposal(
        target="p1",
        parameter="noise_sigma",
        suggested_change=0.5,
        confidence=0.9,
        rationale="test",
        action=LLMAction.TUNE_PROBABILITY,
    )
    adjusted = executor.replay_with_adjustments([signal], {"p1": proposal})
    assert adjusted

    with pytest.raises(ValueError, match="Intervention"):
        executor.intervene({"p1": 1.0})

    executor.mode = ExecutionMode.INTERVENTION
    with pytest.raises(ValueError, match="Unknown agent"):
        executor.intervene({"missing": 1.0})
