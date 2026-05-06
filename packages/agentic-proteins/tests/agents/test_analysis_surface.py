from __future__ import annotations

from agentic_proteins.agents.analysis.sequence_analysis import SequenceAnalysisAgent
from agentic_proteins.agents.analysis.structure import StructureAgent
from agentic_proteins.agents.schemas import (
    SequenceAnalysisAgentInput,
    StructureAgentInput,
)


def test_sequence_analysis_metadata_and_schemas() -> None:
    metadata = SequenceAnalysisAgent.metadata()
    assert metadata.agent_name == SequenceAnalysisAgent.name
    assert "sequence validation" in metadata.capabilities
    assert SequenceAnalysisAgent.input_schema()
    assert SequenceAnalysisAgent.output_schema()

    payload = SequenceAnalysisAgentInput(sequence="ACDE", sequence_id="seq-1")
    decision = SequenceAnalysisAgent().decide(payload)
    assert decision.agent_name == SequenceAnalysisAgent.name


def test_structure_agent_metadata_and_schemas() -> None:
    metadata = StructureAgent.metadata()
    assert metadata.agent_name == StructureAgent.name
    assert "structure request" in metadata.capabilities
    assert StructureAgent.input_schema()
    assert StructureAgent.output_schema()

    payload = StructureAgentInput(sequence="ACDE")
    decision = StructureAgent().decide(payload)
    assert decision.agent_name == StructureAgent.name
