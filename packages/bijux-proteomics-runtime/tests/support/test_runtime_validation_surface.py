from __future__ import annotations

from bijux_proteomics_runtime.execution.agents.contracts import (
    _minimal_payload,
    _placeholder_for_type,
    validate_agent,
)


def test_runtime_validation_surface_smoke() -> None:
    assert validate_agent is not None


def test_runtime_validation_surface_exports_payload_helpers() -> None:
    assert _minimal_payload is not None
    assert _placeholder_for_type is not None
