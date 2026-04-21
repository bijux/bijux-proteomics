from __future__ import annotations

from bijux_proteomics.biology import ProteinConstraints, ProteinState, SignalPayload, SignalType
from bijux_proteomics.biology.protein_agent import ProteinAgent


def test_biology_surface_smoke() -> None:
    constraints = ProteinConstraints(
        energy_cost=1.0,
        resource_dependency=("atp",),
        inhibition_conditions=(SignalType.INHIBIT,),
    )
    agent = ProteinAgent(
        agent_id="p53",
        constraints=constraints,
        transitions={(ProteinState.INACTIVE, SignalType.ACTIVATE): ProteinState.ACTIVE},
    )
    signal = SignalPayload(source_id="kinase", signal_type=SignalType.ACTIVATE)
    out = agent.receive(signal)
    assert out is not None
    assert out.signal_type is SignalType.ACTIVATE
