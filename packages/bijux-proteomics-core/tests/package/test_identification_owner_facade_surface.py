# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import bijux_proteomics.identification as identification
from bijux_proteomics.identification import (
    adapters,
    contracts,
    fdr,
    peptide,
    protein,
    psm,
    search_adapters,
)
from bijux_proteomics.identification.public_api import (
    ADAPTERS_FACADE_BUDGET,
    CONTRACTS_FACADE_BUDGET,
    FDR_FACADE_BUDGET,
    PEPTIDE_FACADE_BUDGET,
    PROTEIN_FACADE_BUDGET,
    PSM_FACADE_BUDGET,
    list_identification_adapter_api_modules,
    list_identification_contract_api_modules,
    flatten_facade_exports,
    list_identification_fdr_api_modules,
    list_identification_peptide_api_modules,
    list_identification_protein_api_modules,
    list_identification_psm_api_modules,
)

REPO_ROOT = Path(__file__).resolve().parents[4]


def _non_empty_line_count(relative_path: str) -> int:
    content = (REPO_ROOT / relative_path).read_text(encoding="utf-8").splitlines()
    return sum(1 for line in content if line.strip())


def test_psm_facade_exports_match_governed_public_api() -> None:
    expected = flatten_facade_exports(list_identification_psm_api_modules())

    assert tuple(psm.__all__) == expected
    assert hasattr(psm, "extract_psm_features")
    assert hasattr(psm, "fit_target_decoy_logistic_model")
    assert _non_empty_line_count(
        "packages/bijux-proteomics-core/src/bijux_proteomics/identification/psm/__init__.py"
    ) <= PSM_FACADE_BUDGET.max_init_lines


def test_peptide_facade_exports_match_governed_public_api() -> None:
    expected = flatten_facade_exports(list_identification_peptide_api_modules())

    assert tuple(peptide.__all__) == expected
    assert hasattr(peptide, "build_peptide_evidence_report")
    assert hasattr(peptide, "build_peptide_cross_run_reproducibility_report")
    assert _non_empty_line_count(
        "packages/bijux-proteomics-core/src/bijux_proteomics/identification/peptide/__init__.py"
    ) <= PEPTIDE_FACADE_BUDGET.max_init_lines


def test_protein_facade_exports_match_governed_public_api() -> None:
    expected = flatten_facade_exports(list_identification_protein_api_modules())

    assert tuple(protein.__all__) == expected
    assert hasattr(protein, "ParsimonyReviewReport")
    assert hasattr(protein, "build_protein_grouping_report")
    assert hasattr(protein, "build_protein_parsimony_report")
    assert _non_empty_line_count(
        "packages/bijux-proteomics-core/src/bijux_proteomics/identification/protein/__init__.py"
    ) <= PROTEIN_FACADE_BUDGET.max_init_lines


def test_fdr_facade_exports_match_governed_public_api() -> None:
    expected = flatten_facade_exports(list_identification_fdr_api_modules())

    assert tuple(fdr.__all__) == expected
    assert hasattr(fdr, "build_psm_target_decoy_fdr_report")
    assert hasattr(fdr, "build_confidence_threshold_sensitivity_bundle")
    assert _non_empty_line_count(
        "packages/bijux-proteomics-core/src/bijux_proteomics/identification/fdr/__init__.py"
    ) <= FDR_FACADE_BUDGET.max_init_lines


def test_contract_facade_exports_match_governed_public_api() -> None:
    expected = flatten_facade_exports(list_identification_contract_api_modules())

    assert tuple(contracts.__all__) == expected
    assert hasattr(contracts, "PsmRecord")
    assert hasattr(contracts, "build_fdr_audit_trail")
    assert _non_empty_line_count(
        "packages/bijux-proteomics-core/src/bijux_proteomics/identification/contracts/__init__.py"
    ) <= CONTRACTS_FACADE_BUDGET.max_init_lines


def test_adapter_facade_exports_match_governed_public_api() -> None:
    expected = flatten_facade_exports(list_identification_adapter_api_modules())

    assert tuple(adapters.__all__) == expected
    assert hasattr(adapters, "build_diann_import_report")
    assert hasattr(adapters, "build_search_adapter_information_loss_report")
    assert _non_empty_line_count(
        "packages/bijux-proteomics-core/src/bijux_proteomics/identification/adapters/__init__.py"
    ) <= ADAPTERS_FACADE_BUDGET.max_init_lines


def test_identification_root_facade_keeps_governed_exports_and_submodules() -> None:
    assert "SearchAdapterKind" in identification.__all__
    assert "ParsimonyReviewReport" in identification.__all__
    assert "confidence" in identification.__all__
    assert "search_adapters" in identification.__all__
    assert hasattr(identification, "SearchAdapterKind")
    assert hasattr(identification, "ParsimonyReviewReport")
    assert hasattr(identification, "confidence")
    assert hasattr(identification, "search_adapters")


def test_search_adapter_subfacade_keeps_canonical_adapter_exports() -> None:
    assert hasattr(search_adapters, "search_adapter_registry")
    assert hasattr(search_adapters, "normalize_search_results_with_adapter")
    assert hasattr(search_adapters, "build_search_adapter_corpus_conformance_matrix")
    assert hasattr(search_adapters, "build_search_adapter_conformance_report")
    assert hasattr(search_adapters, "compare_search_result_reports")
    assert hasattr(search_adapters, "parse_search_parameter_file")
    assert not hasattr(identification, "build_search_adapter_corpus_conformance_matrix")
    assert not hasattr(identification, "build_search_adapter_conformance_report")
    assert not hasattr(identification, "compare_search_result_reports")
    assert not hasattr(identification, "parse_search_parameter_file")
