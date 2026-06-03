# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical quantification review, QC, and provenance owners."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_PROVENANCE_EXPORT_MODULES = (
    "bijux_proteomics.quantification.provenance.benchmarks",
    "bijux_proteomics.quantification.provenance.heatmap_preparation",
    "bijux_proteomics.quantification.provenance.replicate_qc",
    "bijux_proteomics.quantification.provenance.review",
    "bijux_proteomics.quantification.provenance.sample_exploration",
    "bijux_proteomics.quantification.provenance.value_provenance",
)


def __getattr__(name: str) -> Any:
    for module_path in _PROVENANCE_EXPORT_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
