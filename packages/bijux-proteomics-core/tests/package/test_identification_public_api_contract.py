# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification.public_api import (
    ADAPTERS_FACADE_BUDGET,
    CONTRACTS_FACADE_BUDGET,
    FDR_FACADE_BUDGET,
    IDENTIFICATION_ROOT_SEARCH_ADAPTER_EXCLUDED_EXPORTS,
    IDENTIFICATION_ROOT_SUBMODULES,
    PEPTIDE_FACADE_BUDGET,
    PROTEIN_FACADE_BUDGET,
    PSM_FACADE_BUDGET,
    build_facade_export_map,
    build_identification_root_export_owner_map,
    build_identification_root_search_adapter_export_owner_map,
    flatten_facade_exports,
    list_identification_adapter_api_modules,
    list_identification_contract_api_modules,
    list_identification_fdr_api_modules,
    list_identification_peptide_api_modules,
    list_identification_protein_api_modules,
    list_identification_psm_api_modules,
    list_identification_root_export_names,
)


def test_identification_facade_ledgers_stay_within_governed_symbol_budgets() -> None:
    cases = (
        (
            "psm",
            PSM_FACADE_BUDGET.max_public_symbols,
            list_identification_psm_api_modules(),
        ),
        (
            "peptide",
            PEPTIDE_FACADE_BUDGET.max_public_symbols,
            list_identification_peptide_api_modules(),
        ),
        (
            "protein",
            PROTEIN_FACADE_BUDGET.max_public_symbols,
            list_identification_protein_api_modules(),
        ),
        (
            "fdr",
            FDR_FACADE_BUDGET.max_public_symbols,
            list_identification_fdr_api_modules(),
        ),
        (
            "contracts",
            CONTRACTS_FACADE_BUDGET.max_public_symbols,
            list_identification_contract_api_modules(),
        ),
        (
            "adapters",
            ADAPTERS_FACADE_BUDGET.max_public_symbols,
            list_identification_adapter_api_modules(),
        ),
    )

    for facade_name, max_public_symbols, modules in cases:
        export_names = flatten_facade_exports(modules)
        assert len(export_names) <= max_public_symbols, (
            f"{facade_name} facade exports {len(export_names)} symbols, "
            f"exceeding the governed budget of {max_public_symbols}"
        )


def test_identification_facade_ledgers_keep_export_names_unambiguous() -> None:
    facade_modules = (
        list_identification_psm_api_modules(),
        list_identification_peptide_api_modules(),
        list_identification_protein_api_modules(),
        list_identification_fdr_api_modules(),
        list_identification_contract_api_modules(),
        list_identification_adapter_api_modules(),
    )

    for modules in facade_modules:
        export_names = flatten_facade_exports(modules)
        assert len(export_names) == len(set(export_names))


def test_identification_facade_ledgers_resolve_every_export_to_one_owner() -> None:
    facade_modules = (
        list_identification_psm_api_modules(),
        list_identification_peptide_api_modules(),
        list_identification_protein_api_modules(),
        list_identification_fdr_api_modules(),
        list_identification_contract_api_modules(),
        list_identification_adapter_api_modules(),
    )

    for modules in facade_modules:
        export_names = flatten_facade_exports(modules)
        owner_map = build_facade_export_map(modules)
        assert tuple(owner_map) == export_names
        for module in modules:
            assert module.owner_module.startswith("bijux_proteomics.identification.")
            assert module.classification
            assert module.rationale


def test_identification_root_public_api_ledger_stays_governed() -> None:
    export_names = list_identification_root_export_names()
    owner_map = build_identification_root_export_owner_map()

    assert tuple(owner_map) == export_names
    assert tuple(IDENTIFICATION_ROOT_SUBMODULES) == (
        "adapters",
        "confidence",
        "contracts",
        "fdr",
        "peptide",
        "protein",
        "psm",
        "search_adapters",
    )


def test_identification_root_excludes_search_adapter_corpus_exports() -> None:
    root_search_adapter_owner_map = (
        build_identification_root_search_adapter_export_owner_map()
    )

    assert (
        tuple(
            name
            for name in IDENTIFICATION_ROOT_SEARCH_ADAPTER_EXCLUDED_EXPORTS
            if name in root_search_adapter_owner_map
        )
        == ()
    )
