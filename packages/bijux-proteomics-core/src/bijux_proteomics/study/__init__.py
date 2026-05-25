# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Study metadata, design, handoff, and laboratory-outcome contracts."""

from __future__ import annotations

from importlib import import_module

_STUDY_EXPORT_MODULES = (
    "bijux_proteomics.study.design",
    "bijux_proteomics.study.metadata",
    "bijux_proteomics.study.carryover",
    "bijux_proteomics.study.lc_drift",
    "bijux_proteomics.study.lab_protocol_context",
    "bijux_proteomics.study.protocol_consistency",
    "bijux_proteomics.study.laboratory_operations",
    "bijux_proteomics.study.laboratory_plans",
    "bijux_proteomics.study.qc",
    "bijux_proteomics.study.qc_benchmarks",
)


def __getattr__(name: str) -> object:
    for module_path in _STUDY_EXPORT_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
