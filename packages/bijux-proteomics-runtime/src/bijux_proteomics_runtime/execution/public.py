"""Public execution import surface helpers."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from bijux_proteomics_runtime.execution.graph_validation import (
        validate_execution_graph,
        validate_state_snapshot,
    )

_EXECUTION_EXPORT_GROUPS = {
    "bijux_proteomics_runtime.execution.graph_validation": [
        "validate_execution_graph",
        "validate_state_snapshot",
    ],
}

_EXECUTION_EXPORTS = {
    name: (module_name, name)
    for module_name, names in _EXECUTION_EXPORT_GROUPS.items()
    for name in names
}

__all__ = (
    "validate_execution_graph",
    "validate_state_snapshot",
)


def __getattr__(name: str) -> Any:
    """Load execution exports lazily to avoid package-import cycles."""

    target = _EXECUTION_EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attribute_name = target
    module = import_module(module_name)
    return getattr(module, attribute_name)
