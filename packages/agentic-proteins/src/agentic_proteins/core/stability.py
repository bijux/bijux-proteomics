# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Module stability annotations for extension control."""

from __future__ import annotations

from enum import Enum
import inspect
import sys


class StabilityLevel(str, Enum):
    """Stability marker for module zones."""

    STABLE = "stable"
    EXPERIMENTAL = "experimental"
    SEALED = "sealed"


def _mark(level: StabilityLevel) -> None:
    frame = inspect.currentframe()
    if frame is None or frame.f_back is None:
        raise RuntimeError("Unable to resolve caller module for stability mark.")
    caller = frame.f_back.f_back if frame.f_back else None
    if caller is None:
        raise RuntimeError("Unable to resolve caller module for stability mark.")
    module_name = caller.f_globals.get("__name__")
    module = sys.modules.get(module_name)
    if module is None:
        raise RuntimeError("Unable to resolve caller module for stability mark.")
    module.__stability__ = level


def stable() -> None:
    _mark(StabilityLevel.STABLE)


def experimental() -> None:
    _mark(StabilityLevel.EXPERIMENTAL)


def sealed() -> None:
    _mark(StabilityLevel.SEALED)


STABILITY_EXPECTATIONS = {
    "agentic_proteins.api": StabilityLevel.STABLE,
    "agentic_proteins.interfaces": StabilityLevel.STABLE,
    "agentic_proteins.providers": StabilityLevel.EXPERIMENTAL,
    "agentic_proteins.providers.experimental": StabilityLevel.EXPERIMENTAL,
    "agentic_proteins.sandbox": StabilityLevel.EXPERIMENTAL,
    "agentic_proteins.biology": StabilityLevel.SEALED,
    "agentic_proteins.core": StabilityLevel.SEALED,
    "agentic_proteins.execution": StabilityLevel.SEALED,
    "agentic_proteins.runtime": StabilityLevel.SEALED,
}

__all__ = [
    "StabilityLevel",
    "STABILITY_EXPECTATIONS",
    "experimental",
    "sealed",
    "stable",
]
