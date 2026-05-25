# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical intelligence package for analytical owner families."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType

__all__ = [
    "candidates",
    "claims",
    "contradictions",
    "falsifiers",
    "governance",
    "interpretation",
    "judgment",
    "learning",
    "posture",
    "query",
    "refusal",
    "reviews",
]
_INTELLIGENCE_ROOT_MODULES = {name: f"{__name__}.{name}" for name in __all__}


def __getattr__(name: str) -> ModuleType:
    """Load curated intelligence owner modules lazily."""

    module_name = _INTELLIGENCE_ROOT_MODULES.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return import_module(module_name)
