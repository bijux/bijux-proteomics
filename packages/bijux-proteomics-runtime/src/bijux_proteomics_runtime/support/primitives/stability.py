# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Module stability annotations for extension control."""

from __future__ import annotations

from enum import StrEnum
import inspect
import sys


class StabilityLevel(StrEnum):
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
    module_name_obj = caller.f_globals.get("__name__")
    if not isinstance(module_name_obj, str):
        raise RuntimeError("Unable to resolve caller module name for stability mark.")
    module_name = module_name_obj
    module = sys.modules.get(module_name)
    if module is None:
        raise RuntimeError("Unable to resolve caller module for stability mark.")
    module.__dict__["__stability__"] = level


def stable() -> None:
    _mark(StabilityLevel.STABLE)


def experimental() -> None:
    _mark(StabilityLevel.EXPERIMENTAL)


def sealed() -> None:
    _mark(StabilityLevel.SEALED)


STABILITY_EXPECTATIONS = {
    "bijux_proteomics_runtime.api": StabilityLevel.STABLE,
    "bijux_proteomics_runtime.artifacts": StabilityLevel.SEALED,
    "bijux_proteomics_runtime.providers": StabilityLevel.EXPERIMENTAL,
    "bijux_proteomics_runtime.providers.remote": StabilityLevel.EXPERIMENTAL,
    "bijux_proteomics_runtime.execution": StabilityLevel.SEALED,
    "bijux_proteomics_runtime.parallel": StabilityLevel.SEALED,
    "bijux_proteomics_runtime.resume": StabilityLevel.SEALED,
    "bijux_proteomics_runtime.runs": StabilityLevel.SEALED,
    "bijux_proteomics_runtime.state": StabilityLevel.SEALED,
    "bijux_proteomics_runtime.streaming": StabilityLevel.SEALED,
    "bijux_proteomics_runtime.support": StabilityLevel.SEALED,
    "bijux_proteomics_runtime.workflows": StabilityLevel.SEALED,
}

__all__ = [
    "StabilityLevel",
    "STABILITY_EXPECTATIONS",
    "experimental",
    "sealed",
    "stable",
]
