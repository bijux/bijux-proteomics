# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
from importlib import import_module
from pathlib import Path

from bijux_proteomics.identification.search_adapters.public_api import (
    SEARCH_ADAPTER_FACADE_BUDGET,
    build_search_adapter_export_owner_map,
    list_search_adapter_export_names,
)

_SEARCH_ADAPTER_ROOT = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "bijux_proteomics"
    / "identification"
    / "search_adapters"
)
_PYTHON_ROOT = Path(__file__).resolve().parents[2] / "src" / "bijux_proteomics"
_MAX_MODULE_LINES = 1000
_MODULE_EXPORTS = {
    "contracts": (
        "SearchAdapterManifest",
        "SearchAdapterNormalizationReport",
        "SearchParameterReport",
    ),
    "family_policy": ("build_search_result_family_policy",),
    "input_review": (
        "assess_search_result_input",
        "build_search_adapter_field_accounting",
    ),
    "normalization": ("normalize_search_results_with_adapter",),
    "conformance": (
        "build_search_adapter_conformance_report",
        "build_search_adapter_provenance_manifest",
    ),
    "parameter_review": (
        "parse_search_parameter_file",
        "validate_search_parameters",
        "compare_search_parameters",
    ),
    "comparison": (
        "compare_search_result_reports",
        "merge_search_result_reports",
        "build_external_engine_disagreement_report",
    ),
    "regression": ("build_search_adapter_regression_corpus_manifest",),
    "corpus": (
        "SearchCorpusInputSpecification",
        "build_search_engine_corpus_report",
    ),
    "corpus_matrix": ("build_search_adapter_corpus_conformance_matrix",),
    "registry": (
        "search_adapter_registry",
        "search_adapter_dialect_registry",
        "get_search_adapter_manifest",
    ),
    "engines.comet": (
        "COMET_MANIFEST",
        "parse_comet_parameters",
        "build_comet_output_corpus_report",
    ),
    "engines.msfragger": (
        "MSFRAGGER_MANIFEST",
        "parse_msfragger_parameters",
        "build_msfragger_output_corpus_report",
    ),
    "engines.sage": (
        "SAGE_MANIFEST",
        "parse_sage_parameters",
        "build_sage_output_corpus_report",
    ),
    "engines.maxquant": (
        "MAXQUANT_MANIFEST",
        "parse_maxquant_parameters",
        "build_maxquant_output_corpus_report",
    ),
    "engines.diann": (
        "DIANN_MANIFEST",
        "parse_diann_parameters",
        "build_diann_output_corpus_report",
    ),
    "engines.spectronaut": (
        "SPECTRONAUT_MANIFEST",
        "parse_spectronaut_parameters",
        "build_spectronaut_output_corpus_report",
    ),
    "engines.generic": ("GENERIC_MANIFEST",),
}
_FACADE_EXPORTS = (
    "SearchAdapterKind",
    "search_adapter_registry",
    "parse_search_parameter_file",
    "normalize_search_results_with_adapter",
    "compare_search_result_reports",
    "build_search_adapter_corpus_conformance_matrix",
    "build_comet_output_corpus_report",
    "build_spectronaut_output_corpus_report",
)


def test_search_adapter_modules_stay_within_line_ceiling() -> None:
    line_counts = {
        str(path.relative_to(_SEARCH_ADAPTER_ROOT)): sum(
            1 for _line in path.open(encoding="utf-8")
        )
        for path in sorted(_SEARCH_ADAPTER_ROOT.rglob("*.py"))
    }

    assert line_counts
    assert all(count <= _MAX_MODULE_LINES for count in line_counts.values()), (
        line_counts
    )


def test_search_adapter_modules_expose_owned_surfaces() -> None:
    for module_name, exports in _MODULE_EXPORTS.items():
        module = import_module(
            f"bijux_proteomics.identification.search_adapters.{module_name}"
        )
        for export_name in exports:
            assert hasattr(module, export_name), f"{module_name}.{export_name}"


def test_search_adapter_facade_preserves_representative_exports() -> None:
    facade = import_module("bijux_proteomics.identification.search_adapters")

    assert tuple(facade.__all__) == list_search_adapter_export_names()
    assert len(facade.__all__) <= SEARCH_ADAPTER_FACADE_BUDGET.max_public_symbols
    assert len(build_search_adapter_export_owner_map()) == len(facade.__all__)

    for export_name in _FACADE_EXPORTS:
        assert hasattr(facade, export_name), export_name


def test_search_adapter_facade_init_stays_within_budget() -> None:
    init_path = _SEARCH_ADAPTER_ROOT / "__init__.py"
    line_count = sum(1 for line in init_path.read_text(encoding="utf-8").splitlines() if line.strip())

    assert line_count <= SEARCH_ADAPTER_FACADE_BUDGET.max_init_lines


def test_internal_modules_import_search_adapter_owner_modules_directly() -> None:
    violations: list[str] = []
    for path in sorted(_PYTHON_ROOT.rglob("*.py")):
        if path == _SEARCH_ADAPTER_ROOT / "__init__.py":
            continue
        module = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(module):
            if isinstance(node, ast.ImportFrom):
                if node.module == "bijux_proteomics.identification.search_adapters":
                    violations.append(
                        f"{path.relative_to(_PYTHON_ROOT)} imports the search adapter root facade instead of an owner module"
                    )
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "bijux_proteomics.identification.search_adapters":
                        violations.append(
                            f"{path.relative_to(_PYTHON_ROOT)} imports the search adapter root facade instead of an owner module"
                        )
    assert not violations, "\n".join(violations)
