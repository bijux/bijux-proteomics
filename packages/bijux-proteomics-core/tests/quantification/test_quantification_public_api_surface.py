# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.quantification.public_api import (
    CONTRACTS_FACADE_BUDGET,
    CONTRACTS_FACADE_OWNERS,
    MATRIX_FACADE_BUDGET,
    MATRIX_FACADE_OWNERS,
    MISSINGNESS_FACADE_BUDGET,
    MISSINGNESS_FACADE_OWNERS,
    NORMALIZATION_FACADE_BUDGET,
    NORMALIZATION_FACADE_OWNERS,
    PROVENANCE_FACADE_BUDGET,
    PROVENANCE_FACADE_OWNERS,
    QUANTIFICATION_ROOT_FACADE_OWNERS,
    QUANTIFICATION_ROOT_SUBMODULES,
    ROLLUP_FACADE_BUDGET,
    ROLLUP_FACADE_OWNERS,
    STATISTICS_FACADE_BUDGET,
    STATISTICS_FACADE_OWNERS,
    build_lazy_export_index,
    facade_owner_modules,
)


def test_quantification_facade_ledgers_fit_surface_budgets() -> None:
    budgeted_facades = (
        (MATRIX_FACADE_BUDGET, MATRIX_FACADE_OWNERS),
        (MISSINGNESS_FACADE_BUDGET, MISSINGNESS_FACADE_OWNERS),
        (NORMALIZATION_FACADE_BUDGET, NORMALIZATION_FACADE_OWNERS),
        (PROVENANCE_FACADE_BUDGET, PROVENANCE_FACADE_OWNERS),
        (ROLLUP_FACADE_BUDGET, ROLLUP_FACADE_OWNERS),
        (STATISTICS_FACADE_BUDGET, STATISTICS_FACADE_OWNERS),
        (CONTRACTS_FACADE_BUDGET, CONTRACTS_FACADE_OWNERS),
    )

    for budget, owners in budgeted_facades:
        public_names, export_index = build_lazy_export_index(
            facade_owner_modules(owners)
        )
        assert public_names
        assert len(public_names) == len(export_index)
        assert len(public_names) <= budget.max_public_symbols


def test_quantification_root_compatibility_ledger_prefers_contract_exports() -> None:
    _, export_index = build_lazy_export_index(
        facade_owner_modules(QUANTIFICATION_ROOT_FACADE_OWNERS),
        collision_policy="prefer_first_owner",
    )

    assert export_index["build_quant_design_matrix_report"][0] == (
        "bijux_proteomics.quantification.contracts"
    )
    assert export_index["build_differential_abundance_report"][0] == (
        "bijux_proteomics.quantification.contracts"
    )
    assert export_index["build_missingness_classifier_report"][0] == (
        "bijux_proteomics.quantification.contracts"
    )


def test_quantification_root_submodule_registry_stays_canonical() -> None:
    assert tuple(QUANTIFICATION_ROOT_SUBMODULES) == (
        "contracts",
        "matrix",
        "missingness",
        "normalization",
        "provenance",
        "rollup",
        "statistics",
    )
