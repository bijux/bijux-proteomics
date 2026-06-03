# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Laboratory-facing diagnosis and action surfaces."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_LAB_EXPORT_MODULES = (
    "bijux_proteomics.lab.protocol_context",
    "bijux_proteomics.lab.qc",
    "bijux_proteomics.lab.qc_benchmarks",
    "bijux_proteomics.lab.carryover",
    "bijux_proteomics.lab.lc_drift",
    "bijux_proteomics.lab.protocol_consistency",
    "bijux_proteomics.lab.operations",
    "bijux_proteomics.lab.planning",
    "bijux_proteomics.lab.actions",
    "bijux_proteomics.lab.background",
    "bijux_proteomics.lab.cohort",
    "bijux_proteomics.lab.contamination",
    "bijux_proteomics.lab.digestion_diagnosis",
    "bijux_proteomics.lab.run_diagnosis",
    "bijux_proteomics.lab.sample_identity",
    "bijux_proteomics.lab.standards",
)


def __getattr__(name: str) -> Any:
    for module_path in _LAB_EXPORT_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
