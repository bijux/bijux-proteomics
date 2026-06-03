# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owner paths for shared provenance and support-state contracts."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from bijux_proteomics_foundation.support.provenance import (
        ProvenancePointer,
        ProvenancePointerKind,
    )
    from bijux_proteomics_foundation.support.states import SupportState

__all__ = [
    "ProvenancePointer",
    "ProvenancePointerKind",
    "SupportState",
]

_SUPPORT_EXPORTS = {
    "ProvenancePointer": (
        "bijux_proteomics_foundation.support.provenance",
        "ProvenancePointer",
    ),
    "ProvenancePointerKind": (
        "bijux_proteomics_foundation.support.provenance",
        "ProvenancePointerKind",
    ),
    "SupportState": (
        "bijux_proteomics_foundation.support.states",
        "SupportState",
    ),
}


def __getattr__(name: str) -> Any:
    """Load support exports lazily to avoid foundation import cycles."""

    target = _SUPPORT_EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attribute_name = target
    module = import_module(module_name)
    return getattr(module, attribute_name)
