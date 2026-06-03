# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
from pathlib import Path

from bijux_proteomics.quantification import (
    matrix,
    missingness,
    normalization,
    provenance,
    rollup,
    statistics,
)

_WRAPPER_MODULES = (
    "quantification/core_matrix.py",
    "quantification/design_matrix.py",
    "quantification/matrix_archive.py",
    "quantification/peptide_intensity_matrix.py",
    "quantification/protein_intensity_matrix.py",
    "quantification/model_rollup.py",
    "quantification/protein_lfq.py",
    "quantification/batch_effect.py",
    "quantification/composition.py",
    "quantification/imputation.py",
    "quantification/normalization.py",
    "quantification/missingness.py",
    "quantification/readiness.py",
    "quantification/peptide_profile_inconsistency.py",
    "quantification/censored_differential.py",
    "quantification/differential_abundance.py",
    "quantification/differential_imputation_dependence.py",
    "quantification/differential_result_robustness.py",
    "quantification/method_agreement.py",
    "quantification/multi_contrast_consistency.py",
    "quantification/peptide_level_differential.py",
    "quantification/power_estimation.py",
    "quantification/statistical_backend.py",
    "quantification/time_course_differential.py",
    "quantification/uncertainty.py",
    "quantification/variance_model.py",
    "quantification/benchmarks.py",
    "quantification/heatmap_preparation.py",
    "quantification/replicate_qc.py",
    "quantification/review.py",
    "quantification/sample_exploration.py",
    "quantification/value_provenance.py",
)


def _core_src_root() -> Path:
    return Path(__file__).resolve().parents[2] / "src" / "bijux_proteomics"


def test_quantification_subpackages_export_representative_owner_surfaces() -> None:
    assert hasattr(matrix, "build_numeric_quant_matrix")
    assert hasattr(matrix, "render_quant_design_matrix_tsv")
    assert hasattr(rollup, "fit_peptide_bias_model")
    assert hasattr(rollup, "build_protein_lfq_report_from_features")
    assert hasattr(normalization, "normalize_label_free_table")
    assert hasattr(normalization, "build_batch_effect_estimator_report")
    assert hasattr(missingness, "build_missingness_classifier_report")
    assert hasattr(missingness, "build_quant_decision_readiness_report")
    assert hasattr(statistics, "build_differential_abundance_report")
    assert hasattr(statistics, "build_time_course_differential_report")
    assert hasattr(statistics, "estimate_protein_uncertainty")
    assert hasattr(provenance, "build_quant_review_bundle")
    assert hasattr(provenance, "build_sample_exploration_report")
    assert hasattr(provenance, "build_quant_truth_package_benchmark_report")


def test_quantification_root_wrappers_stay_compatibility_only() -> None:
    root = _core_src_root()
    for relative_path in _WRAPPER_MODULES:
        path = root / relative_path
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        body = tree.body
        assert body, f"{relative_path} should not be empty"
        assert isinstance(body[0], ast.Expr)
        for node in body[1:]:
            assert isinstance(
                node,
                ast.ImportFrom,
            ), f"{relative_path} should stay a thin compatibility facade"


def test_quantification_root_and_subpackage_surfaces_share_owner_functions() -> None:
    from bijux_proteomics import quantification

    assert (
        quantification.build_numeric_quant_matrix is matrix.build_numeric_quant_matrix
    )
    assert quantification.fit_peptide_bias_model is rollup.fit_peptide_bias_model
    assert (
        quantification.build_quant_review_bundle is provenance.build_quant_review_bundle
    )
