# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical experiment-design ownership surfaces for study semantics."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_STUDY_DESIGN_EXPORT_MODULES = (
    "bijux_proteomics.study.design.experiment_design",
    "bijux_proteomics.study.design.contrasts",
    "bijux_proteomics.study.design.design_diagnostics",
    "bijux_proteomics.study.design.design_validity",
    "bijux_proteomics.study.design.design_classification",
    "bijux_proteomics.study.design.replicate_structure",
    "bijux_proteomics.study.design.experiment_feasibility",
    "bijux_proteomics.study.design.experiment_confidence",
)


def __getattr__(name: str) -> Any:
    for module_path in _STUDY_DESIGN_EXPORT_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
