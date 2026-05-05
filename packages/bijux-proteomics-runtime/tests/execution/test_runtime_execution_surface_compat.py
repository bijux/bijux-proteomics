from __future__ import annotations

from bijux_proteomics_runtime.execution.schemas import ExecutionTrace


def test_runtime_execution_surface_smoke() -> None:
    assert ExecutionTrace is not None
