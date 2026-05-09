# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Curated review owner bands for knowledge-facing decision surfaces."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType

__all__ = [
    "decision_briefs",
    "explanations",
    "flagship_evidence",
    "provenance",
    "trends",
]

_REVIEW_OWNER_MODULES = {name: f"{__name__}.{name}" for name in __all__}


def __getattr__(name: str) -> ModuleType:
    """Load curated review owner modules lazily."""

    module_name = _REVIEW_OWNER_MODULES.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return import_module(module_name)
