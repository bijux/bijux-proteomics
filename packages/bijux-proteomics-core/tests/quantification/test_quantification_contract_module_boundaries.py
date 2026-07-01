# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
from importlib import import_module
from pathlib import Path

from bijux_proteomics.quantification.public_api import (
    CONTRACTS_FACADE_BUDGET,
    CONTRACTS_FACADE_OWNERS,
    build_lazy_export_index,
    facade_owner_modules,
)

_CONTRACT_ROOT = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "bijux_proteomics"
    / "quantification"
    / "contracts"
)
_MAX_CONTRACT_LINES = 1000
_MODULE_EXPORTS = {
    "artifact_bundle": (
        "QuantArtifactBundle",
        "build_quant_artifact_bundle",
        "build_quant_reproducibility_manifest",
    ),
    "design": (
        "QuantDesignMatrixReport",
        "fit_quant_design_matrix_model",
        "render_quant_design_contrast_estimates_tsv",
    ),
    "differential": (
        "DifferentialAbundanceReport",
        "build_differential_abundance_report",
        "build_time_course_differential_report",
    ),
    "input_models": (
        "Ms1FeatureRecord",
        "QuantRollupMethod",
        "PrecursorIntensityParseReport",
    ),
    "input_parsing": (
        "parse_ms1_feature_table",
        "parse_ms1_feature_table_chunked",
        "parse_precursor_intensity_table",
        "parse_precursor_intensity_table_chunked",
    ),
    "label_based": (
        "LabelBasedQuantBundle",
        "build_label_based_quant_bundle",
        "build_multiplex_channel_balance_report",
    ),
    "matrix_building": (
        "coerce_label_free_quant_table",
        "build_quant_matrix_export",
        "build_spectral_count_table",
    ),
    "matrix_models": (
        "LabelFreeQuantTable",
        "QuantValueProvenance",
        "QuantMatrixExport",
    ),
    "missingness": (
        "MissingnessClassifierReport",
        "summarize_missing_values",
        "build_missingness_classifier_report",
    ),
    "normalization_imputation": (
        "NormalizationComparisonReport",
        "build_normalization_strategy_comparison_report",
        "ImputationSensitivityReport",
    ),
    "protein_rollup": (
        "ProteinQuantRollupEvidenceEntry",
        "build_protein_quant_policy_comparison_report",
        "build_label_free_provenance_bundle",
    ),
    "study_qc": (
        "ReplicateAndBatchQcReport",
        "build_batch_effect_estimator_report",
        "build_replicate_correlation_report",
    ),
}
_FACADE_EXPORTS = (
    "Ms1FeatureRecord",
    "parse_ms1_feature_table",
    "parse_ms1_feature_table_chunked",
    "LabelFreeQuantTable",
    "build_quant_matrix_export",
    "build_label_based_quant_bundle",
    "build_protein_quant_rollup_evidence",
    "build_quant_artifact_bundle",
    "summarize_missing_values",
    "build_normalization_comparison_report",
    "build_differential_abundance_report",
    "build_quant_design_matrix_report",
)
_PRIVATE_HELPERS = (
    "_condition_lookup",
    "_effect_size_and_uncertainty",
    "_log2_values",
    "_matrix_value_index",
    "_rebuild_table_from_matrix",
    "_student_t_two_sided_p_value",
    "_table_matrix",
    "_welch_t_test",
)
_FORBIDDEN_QUANTIFICATION_PACKAGE_IMPORT_ROOTS = (
    "benchmarks",
    "dia",
    "interpretation",
    "lab",
    "multiplex",
    "ptm",
    "quantification",
    "workflow",
)


def test_quantification_contract_modules_stay_within_line_ceiling() -> None:
    line_counts = {
        path.name: sum(1 for _line in path.open(encoding="utf-8"))
        for path in sorted(_CONTRACT_ROOT.glob("*.py"))
    }

    assert line_counts
    assert all(count <= _MAX_CONTRACT_LINES for count in line_counts.values()), (
        line_counts
    )


def test_quantification_contract_modules_expose_owned_surfaces() -> None:
    for module_name, exports in _MODULE_EXPORTS.items():
        module = import_module(
            f"bijux_proteomics.quantification.contracts.{module_name}"
        )
        for export_name in exports:
            assert hasattr(module, export_name), f"{module_name}.{export_name}"


def test_quantification_contract_facade_preserves_representative_exports() -> None:
    facade = import_module("bijux_proteomics.quantification.contracts")

    for export_name in _FACADE_EXPORTS:
        assert hasattr(facade, export_name), export_name


def test_quantification_contract_facade_matches_governed_owner_ledger() -> None:
    facade = import_module("bijux_proteomics.quantification.contracts")
    expected_exports, _ = build_lazy_export_index(
        facade_owner_modules(CONTRACTS_FACADE_OWNERS)
    )

    assert tuple(facade.__all__) == expected_exports


def test_quantification_contract_facade_init_stays_within_budget() -> None:
    init_lines = sum(
        1 for _line in (_CONTRACT_ROOT / "__init__.py").open(encoding="utf-8")
    )

    assert init_lines <= CONTRACTS_FACADE_BUDGET.max_init_lines


def test_quantification_contract_facade_excludes_private_helpers() -> None:
    facade = import_module("bijux_proteomics.quantification.contracts")

    for export_name in _PRIVATE_HELPERS:
        assert not hasattr(facade, export_name), export_name


def test_quantification_package_root_rejects_private_helper_lookups() -> None:
    quantification = import_module("bijux_proteomics.quantification")

    for export_name in _PRIVATE_HELPERS:
        assert not hasattr(quantification, export_name), export_name


def test_core_source_avoids_root_quantification_package_barrel_imports() -> None:
    src_root = Path(__file__).resolve().parents[2] / "src" / "bijux_proteomics"
    violations: list[str] = []

    for root_name in _FORBIDDEN_QUANTIFICATION_PACKAGE_IMPORT_ROOTS:
        for path in sorted((src_root / root_name).rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in tree.body:
                if not isinstance(node, ast.ImportFrom):
                    continue
                if node.module == "bijux_proteomics.quantification":
                    violations.append(str(path.relative_to(src_root)))
                    break

    assert not violations, "\n".join(violations)
