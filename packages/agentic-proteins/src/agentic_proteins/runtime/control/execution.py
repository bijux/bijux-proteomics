"""Compatibility forwarding module for canonical runtime ownership."""

from bijux_proteomics_runtime.runtime.control import execution as _runtime_execution
from bijux_proteomics_runtime.runtime.control.execution import *  # noqa: F401,F403
from bijux_proteomics_runtime.runtime.control.execution import (
    _ensure_telemetry_costs,
    _select_structure_tool,
)

__all__ = [
    *getattr(_runtime_execution, "__all__", []),
    "_ensure_telemetry_costs",
    "_select_structure_tool",
]
