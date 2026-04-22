from __future__ import annotations

from bijux_proteomics_runtime.validation.agents import validate_agent


def test_runtime_validation_surface_smoke() -> None:
    assert validate_agent is not None
