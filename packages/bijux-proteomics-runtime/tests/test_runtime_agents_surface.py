from __future__ import annotations

from bijux_proteomics_runtime.agents.schemas import CandidateAssessment


def test_runtime_agents_surface_smoke() -> None:
    assert CandidateAssessment is not None
