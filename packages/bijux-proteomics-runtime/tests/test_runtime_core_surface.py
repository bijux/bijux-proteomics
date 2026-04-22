from __future__ import annotations

from bijux_proteomics_runtime.core.execution import ExecutionContext
from bijux_proteomics_runtime.core.tooling import ToolInvocationSpec


def test_runtime_core_surface_smoke() -> None:
    _ = ExecutionContext
    _ = ToolInvocationSpec
