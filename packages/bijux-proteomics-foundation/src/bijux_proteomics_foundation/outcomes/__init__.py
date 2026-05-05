# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owner paths for shared refusal and operation-result contracts."""

from __future__ import annotations

from importlib import import_module

__all__ = [
    "OperationDisposition",
    "OperationRefusal",
    "OperationResult",
    "RefusalKind",
]

_OWNER_MODULES = {
    "OperationDisposition": "bijux_proteomics_foundation.outcomes.results",
    "OperationRefusal": "bijux_proteomics_foundation.outcomes.refusals",
    "OperationResult": "bijux_proteomics_foundation.outcomes.results",
    "RefusalKind": "bijux_proteomics_foundation.outcomes.refusals",
}


def __getattr__(name: str) -> object:
    """Resolve outcome owner exports lazily to keep imports acyclic."""
    module_name = _OWNER_MODULES.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(module_name)
    return getattr(module, name)
