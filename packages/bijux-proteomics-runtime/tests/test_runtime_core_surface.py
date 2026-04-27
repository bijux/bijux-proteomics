from __future__ import annotations

from bijux_proteomics_runtime.core.surface_area import PUBLIC_ENTRYPOINTS
from bijux_proteomics_runtime.core.execution import ExecutionContext
from bijux_proteomics_runtime.core.tooling import ToolInvocationSpec


def test_runtime_core_surface_smoke() -> None:
    _ = ExecutionContext
    _ = ToolInvocationSpec


def test_runtime_surface_area_uses_canonical_cli_entrypoint() -> None:
    assert "bijux_proteomics_runtime.interfaces.cli.cli" in PUBLIC_ENTRYPOINTS


def test_runtime_surface_area_uses_canonical_run_manager_entrypoint() -> None:
    assert "bijux_proteomics_runtime.runtime.RunManager" in PUBLIC_ENTRYPOINTS
