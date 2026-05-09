# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Judgment, recommendation, and scenario-evaluation owners for intelligence."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_JUDGMENT_MODULES = (
    "bijux_proteomics_intelligence.judgment.benchmark_decisions",
    "bijux_proteomics_intelligence.judgment.flagship_decisions",
    "bijux_proteomics_intelligence.judgment.paths",
    "bijux_proteomics_intelligence.judgment.policies",
    "bijux_proteomics_intelligence.judgment.recommendations",
    "bijux_proteomics_intelligence.judgment.scenarios",
)

__all__: list[str] = []


def __getattr__(name: str) -> Any:
    """Load judgment exports lazily so package import stays cycle-safe."""

    for module_name in _JUDGMENT_MODULES:
        module = import_module(module_name)
        if hasattr(module, name):
            return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
