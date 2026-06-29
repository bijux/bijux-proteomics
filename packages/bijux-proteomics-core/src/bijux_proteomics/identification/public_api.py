"""Machine-readable public facade contract for identification owner packages."""

from __future__ import annotations

from bijux_proteomics.identification.facade_ledger import (
    ADAPTERS_FACADE_BUDGET,
    CONTRACTS_FACADE_BUDGET,
    FDR_FACADE_BUDGET,
    IdentificationFacadeBudget,
    IdentificationFacadeModule,
    PEPTIDE_FACADE_BUDGET,
    PROTEIN_FACADE_BUDGET,
    PSM_FACADE_BUDGET,
    build_facade_export_map,
    flatten_facade_exports,
    list_identification_adapter_api_modules,
    list_identification_contract_api_modules,
    list_identification_fdr_api_modules,
    list_identification_peptide_api_modules,
    list_identification_protein_api_modules,
    list_identification_psm_api_modules,
    merge_facade_export_maps,
)

IDENTIFICATION_OWNER_SUBMODULE_NAMES = (
    "adapters",
    "contracts",
    "fdr",
    "peptide",
    "protein",
    "psm",
)
IDENTIFICATION_COMPATIBILITY_SUBMODULE_NAMES = ("confidence",)
IDENTIFICATION_ROOT_FACADE_ORDER = (
    "adapters",
    "contracts",
    "fdr",
    "peptide",
    "protein",
    "psm",
)
IDENTIFICATION_ROOT_SUBMODULES = {
    "adapters": "bijux_proteomics.identification.adapters",
    "confidence": "bijux_proteomics.identification.confidence",
    "contracts": "bijux_proteomics.identification.contracts",
    "fdr": "bijux_proteomics.identification.fdr",
    "peptide": "bijux_proteomics.identification.peptide",
    "protein": "bijux_proteomics.identification.protein",
    "psm": "bijux_proteomics.identification.psm",
}


def build_identification_root_export_owner_map() -> dict[str, str]:
    """Return the governed root export-owner map for identification."""

    return merge_facade_export_maps(
        build_facade_export_map(list_identification_adapter_api_modules()),
        build_facade_export_map(list_identification_contract_api_modules()),
        build_facade_export_map(list_identification_fdr_api_modules()),
        build_facade_export_map(list_identification_peptide_api_modules()),
        build_facade_export_map(list_identification_protein_api_modules()),
        build_facade_export_map(list_identification_psm_api_modules()),
    )


def list_identification_root_export_names() -> tuple[str, ...]:
    """Return the ordered governed root export names for identification."""

    return tuple(build_identification_root_export_owner_map())


__all__ = [
    "ADAPTERS_FACADE_BUDGET",
    "IDENTIFICATION_COMPATIBILITY_SUBMODULE_NAMES",
    "IDENTIFICATION_ROOT_FACADE_ORDER",
    "IDENTIFICATION_ROOT_SUBMODULES",
    "CONTRACTS_FACADE_BUDGET",
    "FDR_FACADE_BUDGET",
    "IDENTIFICATION_OWNER_SUBMODULE_NAMES",
    "PEPTIDE_FACADE_BUDGET",
    "PROTEIN_FACADE_BUDGET",
    "PSM_FACADE_BUDGET",
    "IdentificationFacadeBudget",
    "IdentificationFacadeModule",
    "build_facade_export_map",
    "merge_facade_export_maps",
    "flatten_facade_exports",
    "build_identification_root_export_owner_map",
    "list_identification_adapter_api_modules",
    "list_identification_contract_api_modules",
    "list_identification_fdr_api_modules",
    "list_identification_peptide_api_modules",
    "list_identification_protein_api_modules",
    "list_identification_psm_api_modules",
    "list_identification_root_export_names",
]
