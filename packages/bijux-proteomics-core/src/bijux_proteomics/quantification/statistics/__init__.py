# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical quantitative inference and robustness owners."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_STATISTICS_EXPORT_MODULES = (
    "bijux_proteomics.quantification.statistics.censored_differential",
    "bijux_proteomics.quantification.statistics.differential_abundance",
    "bijux_proteomics.quantification.statistics.differential_imputation_dependence",
    "bijux_proteomics.quantification.statistics.differential_result_robustness",
    "bijux_proteomics.quantification.statistics.method_agreement",
    "bijux_proteomics.quantification.statistics.multi_contrast_consistency",
    "bijux_proteomics.quantification.statistics.peptide_level_differential",
    "bijux_proteomics.quantification.statistics.power_estimation",
    "bijux_proteomics.quantification.statistics.statistical_backend",
    "bijux_proteomics.quantification.statistics.time_course_differential",
    "bijux_proteomics.quantification.statistics.uncertainty",
    "bijux_proteomics.quantification.statistics.variance_model",
)


def __getattr__(name: str) -> Any:
    for module_path in _STATISTICS_EXPORT_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
