# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owner paths for shared provenance and support-state contracts."""

from __future__ import annotations

from importlib import import_module

__all__ = [
    "ProvenancePointer",
    "ProvenancePointerKind",
    "SupportState",
]

_OWNER_MODULES = {
    "ProvenancePointer": "bijux_proteomics_foundation.support.provenance",
    "ProvenancePointerKind": "bijux_proteomics_foundation.support.provenance",
    "SupportState": "bijux_proteomics_foundation.support.states",
}


def __getattr__(name: str) -> object:
    """Resolve support owner exports lazily to keep imports acyclic."""
    module_name = _OWNER_MODULES.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(module_name)
    return getattr(module, name)
