# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Targeted proteomics selection, result import, coelution, QC, and matrix surfaces."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_TARGETED_EXPORT_MODULES = (
    "bijux_proteomics.targeted.assay_interference",
    "bijux_proteomics.targeted.assay_qc",
    "bijux_proteomics.targeted.biomarker_stability",
    "bijux_proteomics.targeted.carryover",
    "bijux_proteomics.targeted.discovery_peptide_selection",
    "bijux_proteomics.targeted.fragment_ratios",
    "bijux_proteomics.targeted.panel_design",
    "bijux_proteomics.targeted.panel_redundancy",
    "bijux_proteomics.targeted.result_validation",
    "bijux_proteomics.targeted.result_import",
    "bijux_proteomics.targeted.target_matrix",
    "bijux_proteomics.targeted.transition_coelution",
    "bijux_proteomics.targeted.transition_selection",
    "bijux_proteomics.targeted.validation_evidence_cards",
    "bijux_proteomics.targeted.validation_planning",
)


def __getattr__(name: str) -> Any:
    for module_path in _TARGETED_EXPORT_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
