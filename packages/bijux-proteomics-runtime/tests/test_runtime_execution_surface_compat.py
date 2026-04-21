from __future__ import annotations

from bijux_proteomics_runtime.execution.schemas import ExecutionState


def test_runtime_execution_surface_smoke() -> None:
    assert ExecutionState is not None
