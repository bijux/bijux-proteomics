# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Quantification matrices, provenance, and review-bundle surfaces."""

from __future__ import annotations

from importlib import import_module

_QUANTIFICATION_EXPORT_MODULES = (
    "bijux_proteomics.quantification.batch_effect",
    "bijux_proteomics.quantification.core_matrix",
    "bijux_proteomics.quantification.contracts",
    "bijux_proteomics.quantification.design_matrix",
    "bijux_proteomics.quantification.differential_abundance",
    "bijux_proteomics.quantification.differential_imputation_dependence",
    "bijux_proteomics.quantification.differential_result_robustness",
    "bijux_proteomics.quantification.heatmap_preparation",
    "bijux_proteomics.quantification.imputation",
    "bijux_proteomics.quantification.model_rollup",
    "bijux_proteomics.quantification.missingness",
    "bijux_proteomics.quantification.multi_contrast_consistency",
    "bijux_proteomics.quantification.normalization",
    "bijux_proteomics.quantification.peptide_level_differential",
    "bijux_proteomics.quantification.peptide_intensity_matrix",
    "bijux_proteomics.quantification.peptide_profile_inconsistency",
    "bijux_proteomics.quantification.power_estimation",
    "bijux_proteomics.quantification.protein_intensity_matrix",
    "bijux_proteomics.quantification.protein_lfq",
    "bijux_proteomics.quantification.readiness",
    "bijux_proteomics.quantification.replicate_qc",
    "bijux_proteomics.quantification.review",
    "bijux_proteomics.quantification.sample_exploration",
    "bijux_proteomics.quantification.statistical_backend",
    "bijux_proteomics.quantification.time_course_differential",
    "bijux_proteomics.quantification.uncertainty",
    "bijux_proteomics.quantification.variance_model",
    "bijux_proteomics.quantification.value_provenance",
)


def __getattr__(name: str) -> object:
    for module_path in _QUANTIFICATION_EXPORT_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
